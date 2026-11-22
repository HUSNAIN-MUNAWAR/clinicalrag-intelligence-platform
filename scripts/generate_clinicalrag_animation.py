"""Generate a reproducible ClinicalRAG grounding and safety reference reel."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "demo" / "animation_fixture.synthetic.json"
MANIFEST = ROOT / "docs" / "animation" / "clinicalrag_grounding_sequence.json"
REEL = ROOT / "frontend" / "public" / "animation" / "clinicalrag-grounding-reel.html"


def _trace(response) -> dict[str, object]:
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
    }


def _stable_comparison(comparison: dict[str, object]) -> list[dict[str, object]]:
    return [
        {
            "pipeline_id": row["pipeline_id"],
            "retrieved_count": row["retrieved_count"],
            "top_documents": row["top_documents"],
            "scores": row["scores"],
        }
        for row in comparison["comparisons"]
    ]


def build_manifest() -> dict[str, object]:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    runtime = tempfile.TemporaryDirectory(prefix="clinicalrag-animation-")
    runtime_path = Path(runtime.name)
    os.environ["CLINICALRAG_DATA_DIR"] = str(runtime_path)
    os.environ["CLINICALRAG_DATABASE_URL"] = f"sqlite:///{(runtime_path / 'clinicalrag.db').as_posix()}"
    os.environ["CLINICALRAG_LLM_PROVIDER"] = "retrieval_only"
    sys.path.insert(0, str(ROOT / "backend"))

    from app.core.config import settings  # noqa: PLC0415
    from app.db.models import Chunk, Document  # noqa: PLC0415
    from app.db.session import SessionLocal, engine, init_db  # noqa: PLC0415
    from app.evaluation.datasets import seed_demo_questions  # noqa: PLC0415
    from app.evaluation.evaluator import RAGEvaluator  # noqa: PLC0415
    from app.ingestion.pipeline import IngestionPipeline  # noqa: PLC0415
    from app.services.rag_service import RAGService  # noqa: PLC0415
    from app.safety.classifier import MedicalSafetyClassifier  # noqa: PLC0415

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
        source_bytes = FIXTURE.read_bytes()

        stages = [
            {
                "id": "ingest",
                "short": "Ingest",
                "title": "Synthetic open-corpus files enter the pipeline",
                "detail": "The repository demo adapter writes three public educational documents, then the real ingestion pipeline parses, cleans, chunks, and indexes them.",
                "metric": f"{job.status} · {job.processed_files} files · {db.query(Chunk).count()} chunks",
                "status": job.status,
            },
            {
                "id": "retrieve",
                "short": "Retrieve",
                "title": "Hybrid retrieval finds evidence",
                "detail": "Vector and BM25 stores are fused by the repository's hybrid pipeline before answer generation.",
                "metric": f"{len(grounded.retrieved_chunks)} chunks · {len(grounded.source_documents)} documents",
                "status": "retrieved",
            },
            {
                "id": "cite",
                "short": "Cite",
                "title": "Evidence becomes citation objects",
                "detail": "The citation builder assigns stable C-numbers to retrieved evidence and preserves source titles and sections.",
                "metric": f"{len(grounded.citations)} citations · {grounded.confidence_level} confidence",
                "status": "grounded",
            },
            {
                "id": "answer",
                "short": "Answer",
                "title": "Retrieval-only generation stays bounded",
                "detail": "The default local answerer uses retrieved excerpts and citation IDs; no external model or clinical recommendation is claimed.",
                "metric": grounded.model_used,
                "status": grounded.safety_status,
            },
            {
                "id": "safety",
                "short": "Safety",
                "title": "Unsafe dosage requests are refused",
                "detail": "The deterministic medical safety classifier blocks a patient-specific dosage request before retrieval and records the refusal category.",
                "metric": f"{safety_decision.category} · {safety_decision.severity}",
                "status": unsafe.safety_status,
            },
            {
                "id": "evaluate",
                "short": "Evaluate",
                "title": "Retrieval quality is measured",
                "detail": "The seeded evaluation questions run through the same hybrid pipeline and report recall, precision, MRR, nDCG, and citation coverage.",
                "metric": f"{evaluation['question_count']} questions · recall {evaluation['recall_at_k']:.2f} · MRR {evaluation['mrr']:.2f}",
                "status": "measured",
            },
        ]
        return {
            "schema_version": "1.0",
            "fixture": fixture["fixture_id"],
            "source": {
                "path": FIXTURE.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(source_bytes).hexdigest(),
                "synthetic": True,
                "adapter": "backend/app/ingestion/source_adapters/demo_adapter.py::DemoSourceAdapter",
                "document_count": db.query(Document).count(),
                "chunk_count": db.query(Chunk).count(),
            },
            "runtime": {
                "embedding_provider": settings.embedding_provider,
                "embedding_dim": settings.embedding_dim,
                "llm_provider": settings.llm_provider,
                "answer_model": grounded.model_used,
                "pipeline": fixture["pipeline"],
                "top_k": fixture["top_k"],
            },
            "grounded_query": _trace(grounded),
            "unsafe_query": {
                "trace": _trace(unsafe),
                "classifier": {
                    "allowed": safety_decision.allowed,
                    "category": safety_decision.category,
                    "severity": safety_decision.severity,
                    "matched_patterns": safety_decision.matched_patterns,
                },
            },
            "comparison": _stable_comparison(comparison),
            "evaluation": {
                key: evaluation[key]
                for key in ["pipeline_id", "question_count", "recall_at_k", "precision_at_k", "mrr", "ndcg_at_k", "citation_coverage", "avg_source_diversity"]
            },
            "events": stages,
            "claim_boundary": "Synthetic public demo documents and deterministic local retrieval only; not clinical advice, validation, diagnosis, or patient-data processing.",
        }
    finally:
        if db is not None:
            db.close()
        engine.dispose()
        runtime.cleanup()


def render_reel(manifest: dict[str, object]) -> str:
    payload = json.dumps(manifest, indent=2, sort_keys=True).replace("</", "<\\/")
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ClinicalRAG — Grounding and safety reference reel</title>
  <style>
    :root { color-scheme: dark; --ink:#eef5f4; --muted:#a5bbb8; --line:#284b4d; --accent:#76e3bd; --danger:#ff9b82; }
    * { box-sizing:border-box; } body { margin:0; min-width:320px; background:radial-gradient(circle at 80% 0%,#17424b 0,#081719 55%,#050a0b 100%); color:var(--ink); font:15px/1.5 Inter,ui-sans-serif,system-ui,sans-serif; }
    main { max-width:1160px; margin:auto; padding:42px 26px 34px; } .eyebrow { color:var(--accent); font-size:12px; font-weight:800; letter-spacing:.14em; text-transform:uppercase; }
    h1 { max-width:820px; margin:8px 0 10px; font-size:clamp(28px,5vw,54px); line-height:1.02; letter-spacing:-.045em; } .lede { max-width:790px; margin:0; color:var(--muted); font-size:17px; }
    .stage { margin-top:34px; overflow:hidden; border:1px solid var(--line); border-radius:22px; background:linear-gradient(145deg,rgba(17,57,61,.94),rgba(5,15,17,.98)); box-shadow:0 22px 60px rgba(0,0,0,.3); }
    svg { display:block; width:100%; height:auto; min-height:300px; } .route { fill:none; stroke:#315e63; stroke-width:4; stroke-linecap:round; stroke-dasharray:7 12; }
    .station circle { fill:#081719; stroke:#4c7879; stroke-width:3; transition:fill .25s,stroke .25s,transform .25s; transform-origin:center; } .station text { fill:#a7c1bd; font-size:14px; text-anchor:middle; }
    .station .index { fill:#d7ebe7; font-size:13px; font-weight:800; } .station.active circle { fill:#15584d; stroke:var(--accent); transform:scale(1.1); } .station.active text { fill:var(--ink); } .station.done circle { fill:#19473f; stroke:#6cb4a5; }
    .token { fill:var(--accent); stroke:#dcfff2; stroke-width:3; filter:drop-shadow(0 0 12px rgba(118,227,189,.65)); } .token-label { fill:#06251e; font-size:10px; font-weight:900; text-anchor:middle; }
    .panel { display:grid; grid-template-columns:minmax(0,1fr) auto; gap:18px; align-items:end; padding:22px 24px 24px; border-top:1px solid var(--line); } .panel h2 { margin:0 0 3px; font-size:24px; letter-spacing:-.02em; } .panel p { margin:0; color:var(--muted); } .metric { color:var(--accent); font-size:13px; font-weight:800; text-align:right; }
    .controls { display:flex; gap:8px; margin-top:16px; } button { border:1px solid #467b7c; border-radius:999px; padding:9px 15px; background:#123d42; color:var(--ink); font:inherit; cursor:pointer; } button:hover,button:focus-visible { border-color:var(--accent); outline:2px solid rgba(118,227,189,.35); outline-offset:2px; }
    .timeline { display:grid; grid-template-columns:repeat(3,minmax(120px,1fr)); gap:7px; margin-top:18px; } .timeline button { min-height:60px; border-radius:12px; padding:8px; color:var(--muted); text-align:left; font-size:12px; } .timeline button[aria-current="step"] { border-color:var(--accent); background:#17564e; color:var(--ink); } .timeline strong { display:block; color:inherit; font-size:11px; text-transform:uppercase; letter-spacing:.08em; } .disclaimer { margin-top:20px; color:var(--muted); font-size:12px; }
    @media (max-width:760px) { main { padding:28px 16px; } .panel { grid-template-columns:1fr; } .metric { text-align:left; } .timeline { grid-template-columns:repeat(2,minmax(0,1fr)); } svg { min-height:420px; } } @media (prefers-reduced-motion:reduce) { *,*::before,*::after { transition-duration:.01ms!important; animation-duration:.01ms!important; animation-iteration-count:1!important; } }
  </style>
</head>
<body><main><div class="eyebrow">ClinicalRAG · production reference reel</div><h1>Retrieve evidence. Cite it. Refuse unsafe requests.</h1><p class="lede">A real local medical-RAG path turns synthetic public demo documents into bounded answers, citation objects, safety decisions, and measurable retrieval traces.</p>
  <section class="stage" aria-label="Animated ClinicalRAG sequence"><svg viewBox="0 0 1210 390" role="img" aria-labelledby="diagram-title diagram-description"><title id="diagram-title">ClinicalRAG grounding and safety stages</title><desc id="diagram-description">A token travels through ingestion, retrieval, citations, answer generation, safety, and evaluation.</desc><path class="route" d="M80 190 C220 82 360 82 510 190 S800 298 1130 100"></path><g id="stations"></g><g aria-hidden="true"><circle id="token" class="token" cx="80" cy="190" r="22"></circle><text id="token-label" class="token-label" x="80" y="194">RUN</text></g></svg><div class="panel" aria-live="polite"><div><h2 id="event-title"></h2><p id="event-detail"></p></div><div id="event-metric" class="metric"></div></div></section>
  <div class="controls"><button id="toggle" type="button">Pause</button><button id="replay" type="button">Replay</button></div><div id="timeline" class="timeline" role="list" aria-label="Animation stages"></div><p class="disclaimer">Synthetic public demo corpus · real ingestion/retrieval/safety/evaluation services · no patient data or clinical recommendation.</p>
  <script>
    const sequence = __SEQUENCE__; const events = sequence.events; const points = [[80,190],[270,96],[460,96],[650,190],[840,284],[1040,284]]; const stations = document.getElementById('stations'); const timeline = document.getElementById('timeline'); const token = document.getElementById('token'); const tokenLabel = document.getElementById('token-label'); const title = document.getElementById('event-title'); const detail = document.getElementById('event-detail'); const metric = document.getElementById('event-metric'); const toggle = document.getElementById('toggle'); let current = 0; let started = performance.now(); let playing = !window.matchMedia('(prefers-reduced-motion: reduce)').matches; const duration = 1900;
    points.forEach((point,index) => { const group=document.createElementNS('http://www.w3.org/2000/svg','g'); group.classList.add('station'); group.innerHTML=`<circle cx="${point[0]}" cy="${point[1]}" r="30"></circle><text class="index" x="${point[0]}" y="${point[1]+5}">${index+1}</text><text x="${point[0]}" y="${point[1]+57}">${events[index].short}</text>`; stations.appendChild(group); });
    events.forEach((event,index) => { const item=document.createElement('button'); item.type='button'; item.setAttribute('role','listitem'); item.innerHTML=`<strong>${String(index+1).padStart(2,'0')} · ${event.status}</strong>${event.title}`; item.addEventListener('click',()=>{ current=index; started=performance.now(); playing=false; toggle.textContent='Play'; render(0); }); timeline.appendChild(item); });
    function render(progress) { const next=(current+1)%points.length; const from=points[current]; const to=points[next]; const x=from[0]+(to[0]-from[0])*progress; const y=from[1]+(to[1]-from[1])*progress; token.setAttribute('cx',x); token.setAttribute('cy',y); tokenLabel.setAttribute('x',x); tokenLabel.setAttribute('y',y+4); title.textContent=events[current].title; detail.textContent=events[current].detail; metric.textContent=events[current].metric; document.querySelectorAll('.station').forEach((node,index)=>{ node.classList.toggle('active',index===current); node.classList.toggle('done',index<current); }); timeline.querySelectorAll('button').forEach((node,index)=>node.setAttribute('aria-current',index===current?'step':'false')); }
    function animate(now) { if(playing){ const progress=Math.min(1,(now-started)/duration); render(progress); if(progress>=1){ current=(current+1)%events.length; started=now; } } else { render(0); } requestAnimationFrame(animate); }
    toggle.addEventListener('click',()=>{ playing=!playing; started=performance.now(); toggle.textContent=playing?'Pause':'Play'; }); document.getElementById('replay').addEventListener('click',()=>{ current=0; started=performance.now(); playing=true; toggle.textContent='Pause'; }); render(0); requestAnimationFrame(animate);
  </script>
</main></body></html>
""".replace("__SEQUENCE__", payload)


def main() -> None:
    manifest = build_manifest()
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    REEL.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REEL.write_text(render_reel(manifest), encoding="utf-8")
    print(f"wrote {MANIFEST.relative_to(ROOT)}")
    print(f"wrote {REEL.relative_to(ROOT)}")
    print(f"ingestion: {manifest['events'][0]['metric']}")
    print(f"safety: {manifest['unsafe_query']['classifier']['category']} -> {manifest['unsafe_query']['trace']['safety_status']}")
    print(f"evaluation recall: {manifest['evaluation']['recall_at_k']:.2f}")


if __name__ == "__main__":
    main()
