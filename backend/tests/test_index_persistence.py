import pytest

from app.core.config import settings
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import LocalVectorStore


def test_corrupt_embedding_cache_is_not_silently_replaced(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'data_dir', tmp_path)
    index_dir = tmp_path / 'indexes'
    index_dir.mkdir()
    (index_dir / 'embedding_cache.json').write_text('{broken', encoding='utf-8')
    with pytest.raises(RuntimeError, match='Embedding cache cannot be read safely'):
        EmbeddingService()


def test_corrupt_vector_index_is_not_silently_replaced(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'data_dir', tmp_path)
    index_dir = tmp_path / 'indexes'
    index_dir.mkdir()
    (index_dir / 'vector_index.json').write_text('{broken', encoding='utf-8')
    with pytest.raises(RuntimeError, match='Vector index cannot be read safely'):
        LocalVectorStore()
