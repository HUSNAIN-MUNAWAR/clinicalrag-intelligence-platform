# ClinicalRAG grounding and safety animation enhancement

## Purpose

Make the platform's clinical-safety boundary visible: synthetic public demo documents are ingested, retrieved through hybrid search, converted into citations, answered in retrieval-only mode, screened for unsafe requests, and evaluated with retrieval metrics.

## Real service boundary

The generator executes the repository's `DemoSourceAdapter`, `IngestionPipeline`, `IndexService`, vector/BM25/hybrid pipelines, `CitationBuilder`, `RAGService`, `MedicalSafetyClassifier`, and `RAGEvaluator`. It runs in a temporary SQLite/index directory and leaves no local runtime database in the repository.

It never claims diagnosis, treatment, patient-data handling, clinical validation, or an external LLM response. The fixture is explicitly synthetic and public-demo-only.

## Reproduce

```bash
python scripts/generate_clinicalrag_animation.py
```

Outputs:

- `docs/animation/clinicalrag_grounding_sequence.json` — source checksum, pipeline traces, safety decision, comparison, evaluation metrics, and scene events.
- `frontend/public/animation/clinicalrag-grounding-reel.html` — dependency-free animated reference reel with pause, replay, and stage selection.
