# RAG Pipelines

Every pipeline listed by `/rag/pipelines` has a backend implementation under `backend/app/rag/pipelines`.

- Vector: dense local hash embeddings and cosine similarity.
- BM25: pure Python keyword scoring for exact biomedical terminology.
- Hybrid: normalized score fusion between vector and BM25.
- Reranked Hybrid: hybrid candidates re-scored by deterministic lexical reranker.
- Parent-Child: retrieves small chunks and returns parent section context.
- Section-Aware: applies medical section weights.
- Metadata-Filtered: filters by source, type, year, topic, publication type, or category.
- Multi-Query: expands medical synonyms and merged retrieval.
- RAG-Fusion: reciprocal-rank fusion across query variants.
- Router: rule-based pipeline selection by query type.
- Evaluation-Aware: logs retrieval signals for evaluation.
