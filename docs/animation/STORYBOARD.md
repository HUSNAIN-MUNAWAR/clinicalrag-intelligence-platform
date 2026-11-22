# Storyboard: ClinicalRAG grounding loop

1. **Ingest** — synthetic public demo files pass parsing, chunking, and indexing.
2. **Retrieve** — vector and BM25 evidence are fused by the hybrid pipeline.
3. **Cite** — retrieved evidence becomes source-aware C-number citation objects.
4. **Answer** — the local extractive model quotes bounded evidence and states limitations.
5. **Safety** — a dosage request is refused before retrieval by deterministic rules.
6. **Evaluate** — seeded questions report recall, precision, MRR, nDCG, citation coverage, and source diversity.

The reel is a model/reference artifact for product communication, not a clinical outcome claim.
