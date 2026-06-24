# Architecture

ClinicalRAG Intelligence Platform is a local-first advanced RAG system for open medical and biomedical knowledge. It is intentionally not a clinical decision support product.

## Layers

1. Frontend dashboard: Next.js pages for source management, ingestion, playground, comparison, retrieval inspection, evaluation, safety, and settings.
2. FastAPI backend: typed route layer, service layer, ingestion layer, retrieval layer, safety layer, evaluation layer.
3. Storage: SQLite/PostgreSQL metadata, raw document filesystem, JSON local vector/BM25 indexes by default.
4. RAG: vector, BM25, hybrid, reranked hybrid, parent-child, section-aware, metadata-filtered, multi-query, RAG-Fusion, router, evaluation-aware.
5. Safety: deterministic guardrails for emergency, diagnosis, dosage, prescription, PHI, and citation-bypass requests.
