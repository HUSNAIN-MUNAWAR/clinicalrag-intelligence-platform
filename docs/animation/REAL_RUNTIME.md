# Real ClinicalRAG runtime evidence

This is the accepted ClinicalRAG animation evidence. It executes the repository's real ingestion, index, hybrid retrieval, citation, safety, and evaluation services with a real local sentence-transformer embedding model. The answer layer remains explicitly retrieval-only because no external LLM endpoint was configured.

## Reproduce

Install the backend requirements, including `sentence-transformers`, then run from the repository root:

```powershell
$env:HF_HUB_DISABLE_IMPLICIT_TOKEN = "1"
py -3.12 scripts/generate_real_runtime_video.py
```

The first run downloads `sentence-transformers/all-MiniLM-L6-v2` into the local Hugging Face cache if it is not present. The generator uses an isolated temporary SQLite/data directory, so it does not mix this evidence with a prior database or index.

## Measured run

- Embedding provider: `sentence_transformers`.
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`.
- Device: CPU; embedding dimension: `384`; normalized probe vector norm: `1.0`.
- Ingestion: 3 demo documents, 20 child chunks, 0 failed files.
- Grounded query: 5 hybrid-retrieved chunks, 5 citations, retrieval-only extractive answer, per-chunk vector/BM25/hybrid scores preserved.
- Grounded answer citation coverage: `0.6` under the repository's exact answer text; the answer cites three of five retrieved citation objects. This is recorded as-is rather than upgraded to a perfect score.
- Unsafe query: dosage request refused by `MedicalSafetyClassifier` before retrieval; no citations returned.
- Evaluation: 3 questions, recall `1.0`, precision `0.4667`, MRR `1.0`, nDCG `1.0`, citation coverage `1.0` under the evaluator's “any citation exists” metric.

The corpus is the repository's synthetic public demo content. These are retrieval-system observations, not clinical validation, medical advice, patient-data processing, or an LLM quality benchmark.

## Preserved outputs

| Artifact | Evidence |
| --- | --- |
| [`clinicalrag-runtime.mp4`](runtime-evidence/clinicalrag-runtime.mp4) | Eight-stage 256-frame animation derived from the real model load, ingestion, retrieval, citations, answer, refusal, evaluation, and export stages. |
| [`clinicalrag-runtime-poster.png`](runtime-evidence/clinicalrag-runtime-poster.png) | Poster showing the real model name, 384-dimensional embedding runtime, retrieval-only answerer, and citation coverage. |
| [`clinicalrag-retrieval.csv`](runtime-evidence/clinicalrag-retrieval.csv) | Five grounded-query chunks with citation IDs, titles, sections, scores, and text excerpts. |
| [`clinicalrag-comparison.csv`](runtime-evidence/clinicalrag-comparison.csv) | Actual vector, BM25, and hybrid comparison outputs. |
| [`clinicalrag-source-files.csv`](runtime-evidence/clinicalrag-source-files.csv) | Hashes of the committed demo source files. |
| [`clinicalrag-runtime-summary.json`](runtime-evidence/clinicalrag-runtime-summary.json) | Full model, ingestion, query, refusal, evaluation, probe-vector, and artifact-hash record. |

The transformer weights are intentionally not committed. The model identifier and a probe-vector digest are recorded in the JSON report; the reproduction command resolves the same public model locally.

The earlier HTML asset at [`frontend/public/animation/clinicalrag-grounding-reel.html`](../../frontend/public/animation/clinicalrag-grounding-reel.html) remains the dependency-free reference UI. Use the runtime-evidence files above for model evidence.
