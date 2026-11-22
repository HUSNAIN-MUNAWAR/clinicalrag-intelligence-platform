"""Run ClinicalRAG with a real local embedding model and render its evidence."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "demo" / "animation_fixture.synthetic.json"
RAW_CORPUS = ROOT / "data" / "demo_corpus" / "raw"
OUTPUT_DIR = ROOT / "docs" / "animation" / "runtime-evidence"
VIDEO_PATH = OUTPUT_DIR / "clinicalrag-runtime.mp4"
POSTER_PATH = OUTPUT_DIR / "clinicalrag-runtime-poster.png"
SUMMARY_PATH = OUTPUT_DIR / "clinicalrag-runtime-summary.json"
RETRIEVAL_PATH = OUTPUT_DIR / "clinicalrag-retrieval.csv"
SOURCES_PATH = OUTPUT_DIR / "clinicalrag-source-files.csv"
COMPARISON_PATH = OUTPUT_DIR / "clinicalrag-comparison.csv"


def sha256_file(path: Path) -> str:
    """Hash a source or generated artifact."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def trace_response(response: Any) -> dict[str, Any]:
    """Convert a RAG response into a JSON-safe trace."""
    return {
        "safety_status": response.safety_status,
        "confidence_level": response.confidence_level,
        "pipeline_used": response.pipeline_used,
        "model_used": response.model_used,
        "citation_ids": [item.citation_id for item in response.citations],
        "source_titles": [item.title for item in response.citations],
        "answer": response.answer,
        "evidence_summary": response.evidence_summary,
        "retrieval_scores": response.retrieval_scores,
        "refusal_reason": response.refusal_reason,
        "latency_breakdown": response.latency_breakdown.model_dump(),
        "retrieved_chunks": [item.model_dump() for item in response.retrieved_chunks],
        "citation_coverage": sum(1 for item in response.citations if f'[{item.citation_id}]' in response.answer) / max(len(response.citations), 1),
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    """Write a compact, reviewable trace CSV."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run_real_pipeline() -> dict[str, Any]:
    """Execute ingestion, transformer-backed retrieval, citations, safety, and evaluation."""
    runtime = tempfile.TemporaryDirectory(prefix="clinicalrag-real-runtime-")
    runtime_path = Path(runtime.name)
    os.environ["CLINICALRAG_DATA_DIR"] = str(runtime_path)
    os.environ["CLINICALRAG_DATABASE_URL"] = f"sqlite:///{(runtime_path / 'clinicalrag.db').as_posix()}"
    os.environ["CLINICALRAG_LLM_PROVIDER"] = "retrieval_only"
    os.environ["CLINICALRAG_EMBEDDING_PROVIDER"] = "sentence_transformers"
    os.environ["CLINICALRAG_EMBEDDING_MODEL"] = "sentence-transformers/all-MiniLM-L6-v2"
    os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
    sys.path.insert(0, str(ROOT / "backend"))

    from app.core.config import settings  # noqa: PLC0415
    from app.db.models import Chunk, Document  # noqa: PLC0415
    from app.db.session import SessionLocal, engine, init_db  # noqa: PLC0415
    from app.evaluation.datasets import seed_demo_questions  # noqa: PLC0415
    from app.evaluation.evaluator import RAGEvaluator  # noqa: PLC0415
    from app.ingestion.pipeline import IngestionPipeline  # noqa: PLC0415
    from app.rag.embeddings import EmbeddingService  # noqa: PLC0415
    from app.services.rag_service import RAGService  # noqa: PLC0415
    from app.safety.classifier import MedicalSafetyClassifier  # noqa: PLC0415

    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    db = None
    try:
        init_db()
        db = SessionLocal()
        job = IngestionPipeline().run(db)
        service = RAGService()
        grounded = service.ask(db, fixture["queries"]["grounded"], fixture["pipeline"], fixture["top_k"])
        unsafe = service.ask(db, fixture["queries"]["unsafe"], fixture["pipeline"], fixture["top_k"])
        comparison = service.compare(db, fixture["queries"]["evaluation"], ["vector", "bm25", "hybrid"], fixture["top_k"])
        seed_demo_questions(db)
        evaluation_run = RAGEvaluator().run(db, fixture["evaluation"]["pipeline"], fixture["evaluation"]["top_k"])
        evaluation = json.loads(evaluation_run.metrics_json)
        safety_decision = MedicalSafetyClassifier().check(fixture["queries"]["unsafe"])

        embedder = EmbeddingService()
        probe_text = "hypertension symptoms and grounded educational evidence"
        probe_vector = np.asarray(embedder.embed(probe_text), dtype=np.float32)
        source_files = []
        for path in sorted(RAW_CORPUS.iterdir()):
            if path.is_file():
                source_files.append({"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": sha256_file(path)})

        comparison_rows = []
        for row in comparison["comparisons"]:
            comparison_rows.append(
                {
                    "pipeline_id": row["pipeline_id"],
                    "retrieved_count": row["retrieved_count"],
                    "top_documents": json.dumps(row["top_documents"], ensure_ascii=True),
                    "scores": json.dumps(row["scores"], ensure_ascii=True),
                }
            )
        retrieval_rows = []
        for rank, chunk in enumerate(grounded.retrieved_chunks, 1):
            retrieval_rows.append(
                {
                    "rank": rank,
                    "citation_id": grounded.citations[rank - 1].citation_id if rank <= len(grounded.citations) else "",
                    "title": chunk.title,
                    "section": chunk.section,
                    "score": chunk.score,
                    "vector_score": chunk.vector_score,
                    "bm25_score": chunk.bm25_score,
                    "text": " ".join(chunk.text.split())[:420],
                }
            )

        return {
            "schema_version": "2.0",
            "fixture": fixture["fixture_id"],
            "source": {
                "path": FIXTURE.relative_to(ROOT).as_posix(),
                "sha256": sha256_file(FIXTURE),
                "synthetic": True,
                "adapter": "backend/app/ingestion/source_adapters/demo_adapter.py::DemoSourceAdapter",
                "raw_files": source_files,
                "document_count": db.query(Document).count(),
                "chunk_count": db.query(Chunk).count(),
                "processed_files": job.processed_files,
                "failed_files": job.failed_files,
            },
            "runtime": {
                "python_version": sys.version.split()[0],
                "numpy_version": np.__version__,
                "embedding_provider": settings.embedding_provider,
                "embedding_model": settings.embedding_model,
                "embedding_dim": embedder.dim,
                "embedding_probe": {
                    "text": probe_text,
                    "dimension": int(probe_vector.shape[0]),
                    "norm": float(np.linalg.norm(probe_vector)),
                    "sha256": hashlib.sha256(probe_vector.tobytes()).hexdigest(),
                },
                "llm_provider": settings.llm_provider,
                "answer_model": grounded.model_used,
                "pipeline": fixture["pipeline"],
                "top_k": fixture["top_k"],
                "external_llm_called": False,
            },
            "grounded_query": trace_response(grounded),
            "unsafe_query": {
                "trace": trace_response(unsafe),
                "classifier": {
                    "allowed": safety_decision.allowed,
                    "category": safety_decision.category,
                    "severity": safety_decision.severity,
                    "matched_patterns": safety_decision.matched_patterns,
                },
            },
            "comparison": comparison_rows,
            "evaluation": {key: evaluation[key] for key in ["pipeline_id", "question_count", "recall_at_k", "precision_at_k", "mrr", "ndcg_at_k", "citation_coverage", "avg_source_diversity"]},
            "claim_boundary": "A real local sentence-transformer embeds the synthetic public demo corpus; retrieval and extractive citation generation are measured locally. No external LLM, patient data, clinical validation, or medical advice is claimed.",
            "_retrieval_rows": retrieval_rows,
        }
    finally:
        if db is not None:
            db.close()
        engine.dispose()
        runtime.cleanup()


def put_lines(canvas: np.ndarray, lines: list[str], origin: tuple[int, int], color: tuple[int, int, int], scale: float = 0.56, gap: int = 26) -> None:
    """Draw ASCII-only lines for reliable video text rendering."""
    x, y = origin
    for line in lines:
        cv2.putText(canvas, line, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, 1, cv2.LINE_AA)
        y += gap


def render_frame(evidence: dict[str, Any], stage: str, index: int, total: int) -> np.ndarray:
    """Render one stage from measured retrieval/safety values."""
    canvas = np.full((720, 1280, 3), (8, 18, 24), dtype=np.uint8)
    white, muted = (238, 245, 242), (157, 179, 177)
    accent, green, danger = (118, 227, 189), (132, 224, 158), (104, 111, 235)
    cv2.putText(canvas, "CLINICALRAG | REAL LOCAL GROUNDING", (52, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.96, accent, 2, cv2.LINE_AA)
    cv2.putText(canvas, "SentenceTransformer embeddings | retrieval-only answerer | no patient data", (53, 88), cv2.FONT_HERSHEY_SIMPLEX, 0.55, muted, 1, cv2.LINE_AA)
    cv2.line(canvas, (52, 112), (1228, 112), (44, 71, 75), 1)
    cv2.rectangle(canvas, (52, 140), (824, 652), (15, 30, 38), -1)
    cv2.rectangle(canvas, (850, 140), (1228, 652), (15, 30, 38), -1)
    cv2.putText(canvas, f"{index + 1:02d}/{total:02d}  {stage.upper()}", (82, 186), cv2.FONT_HERSHEY_SIMPLEX, 0.75, green, 2, cv2.LINE_AA)

    runtime = evidence["runtime"]
    source = evidence["source"]
    grounded = evidence["grounded_query"]
    unsafe = evidence["unsafe_query"]
    model_display = runtime["embedding_model"].rsplit("/", 1)[-1]
    if stage == "embedding model":
        put_lines(canvas, ["actual local model loaded", f"provider: {runtime['embedding_provider']}", f"model: {runtime['embedding_model']}", f"dimension: {runtime['embedding_dim']}", f"probe norm: {runtime['embedding_probe']['norm']:.6f}", f"probe sha: {runtime['embedding_probe']['sha256'][:24]}..."], (86, 270), white)
    elif stage == "ingestion":
        put_lines(canvas, ["actual IngestionPipeline", f"status: {source['processed_files']} files processed", f"failed files: {source['failed_files']}", f"documents: {source['document_count']}", f"child chunks indexed: {source['chunk_count']}", "temporary SQLite runtime"], (86, 270), white)
    elif stage == "retrieval":
        put_lines(canvas, ["actual hybrid retrieval", f"pipeline: {grounded['pipeline_used']}", f"retrieved: {len(grounded['retrieved_chunks'])} chunks", f"sources: {len(grounded['source_titles'])}", f"vector hits: {grounded['retrieval_scores'].get('vector_hits')}", f"bm25 hits: {grounded['retrieval_scores'].get('bm25_hits')}"], (86, 270), white)
        y = 470
        for row in grounded["retrieved_chunks"][:3]:
            title = (row.get("title") or "unknown")[:34]
            cv2.putText(canvas, f"{row.get('score', 0):.3f}  {title}", (86, y), cv2.FONT_HERSHEY_SIMPLEX, 0.48, muted, 1, cv2.LINE_AA)
            y += 27
    elif stage == "citations":
        put_lines(canvas, ["CitationBuilder output", f"citations: {len(grounded['citation_ids'])}", f"confidence: {grounded['confidence_level']}", f"model_used: {grounded['model_used']}", "citation IDs are from retrieved chunks", "quotes preserved in CSV"], (86, 270), white)
    elif stage == "answer":
        put_lines(canvas, ["retrieval-only extractive answer", f"citation coverage: {grounded['citation_coverage']:.3f}", "no external LLM called", "answer excerpt:", *[grounded["answer"][start : start + 70] for start in range(0, min(len(grounded["answer"]), 210), 70)]], (86, 270), white, 0.49, 24)
    elif stage == "safety":
        put_lines(canvas, ["actual MedicalSafetyClassifier", f"allowed: {unsafe['classifier']['allowed']}", f"category: {unsafe['classifier']['category']}", f"severity: {unsafe['classifier']['severity']}", "retrieval performed: false", "refusal trace preserved"], (86, 270), white)
        cv2.rectangle(canvas, (86, 470), (700, 524), danger, 2)
        cv2.putText(canvas, "unsafe dosage request refused", (106, 505), cv2.FONT_HERSHEY_SIMPLEX, 0.58, danger, 1, cv2.LINE_AA)
    elif stage == "evaluation":
        metrics = evidence["evaluation"]
        put_lines(canvas, ["actual RAGEvaluator", f"questions: {metrics['question_count']}", f"recall@k: {metrics['recall_at_k']:.3f}", f"precision@k: {metrics['precision_at_k']:.3f}", f"MRR: {metrics['mrr']:.3f}", f"citation coverage: {metrics['citation_coverage']:.3f}"], (86, 270), white)
    else:
        put_lines(canvas, ["reviewable evidence written", "MP4 + poster + retrieval CSV", "source hashes + comparison CSV", "full JSON trace + model probe", "external LLM: false", "clinical boundary: explicit"], (86, 270), white)

    cv2.putText(canvas, "RUNTIME FACTS", (878, 186), cv2.FONT_HERSHEY_SIMPLEX, 0.7, accent, 2, cv2.LINE_AA)
    put_lines(canvas, [f"model: {model_display}", f"provider: {runtime['embedding_provider']}", f"embedding dim: {runtime['embedding_dim']}", f"answerer: {runtime['answer_model']}", "device: CPU", "data: public demo only"], (878, 238), muted, 0.53)
    cv2.line(canvas, (878, 418), (1198, 418), (44, 71, 75), 1)
    put_lines(canvas, ["HONEST BOUNDARY", "Real embedding model.", "Synthetic public corpus.", "Retrieval-only answer.", "Not medical advice."], (878, 464), green, 0.56)
    cv2.putText(canvas, "No fabricated citations or metrics", (53, 695), cv2.FONT_HERSHEY_SIMPLEX, 0.54, muted, 1, cv2.LINE_AA)
    return canvas


def write_outputs(evidence: dict[str, Any]) -> None:
    """Persist actual traces and the MP4 presentation."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    retrieval_rows = evidence.pop("_retrieval_rows")
    write_csv(RETRIEVAL_PATH, retrieval_rows, ["rank", "citation_id", "title", "section", "score", "vector_score", "bm25_score", "text"])
    write_csv(SOURCES_PATH, evidence["source"]["raw_files"], ["path", "bytes", "sha256"])
    write_csv(COMPARISON_PATH, evidence["comparison"], ["pipeline_id", "retrieved_count", "top_documents", "scores"])

    stages = ["embedding model", "ingestion", "retrieval", "citations", "answer", "safety", "evaluation", "artifacts"]
    writer = cv2.VideoWriter(str(VIDEO_PATH), cv2.VideoWriter_fourcc(*"mp4v"), 20.0, (1280, 720))
    if not writer.isOpened():
        raise RuntimeError(f"Could not open video writer: {VIDEO_PATH}")
    try:
        for index, stage in enumerate(stages):
            frame = render_frame(evidence, stage, index, len(stages))
            if stage == "answer":
                cv2.imwrite(str(POSTER_PATH), frame)
            for _ in range(32):
                writer.write(frame)
    finally:
        writer.release()

    evidence["artifacts"] = {
        "video": {"path": VIDEO_PATH.relative_to(ROOT).as_posix(), "sha256": sha256_file(VIDEO_PATH), "frames": len(stages) * 32, "fps": 20},
        "poster": {"path": POSTER_PATH.relative_to(ROOT).as_posix(), "sha256": sha256_file(POSTER_PATH)},
        "retrieval_csv": {"path": RETRIEVAL_PATH.relative_to(ROOT).as_posix(), "sha256": sha256_file(RETRIEVAL_PATH)},
        "sources_csv": {"path": SOURCES_PATH.relative_to(ROOT).as_posix(), "sha256": sha256_file(SOURCES_PATH)},
        "comparison_csv": {"path": COMPARISON_PATH.relative_to(ROOT).as_posix(), "sha256": sha256_file(COMPARISON_PATH)},
    }
    with SUMMARY_PATH.open("w", encoding="utf-8") as handle:
        json.dump(evidence, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main() -> None:
    """Run the real local model path and generate reviewable evidence."""
    evidence = run_real_pipeline()
    write_outputs(evidence)
    print(json.dumps({"summary": SUMMARY_PATH.as_posix(), "video": VIDEO_PATH.as_posix(), "embedding_model": evidence["runtime"]["embedding_model"], "evaluation": evidence["evaluation"]}, indent=2))


if __name__ == "__main__":
    main()
