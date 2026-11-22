import hashlib
import json

import numpy as np

from app.core.config import settings


class EmbeddingService:
    """Provide deterministic hash embeddings or an explicit local transformer model."""

    def __init__(self, dim: int | None = None):
        self.provider = settings.embedding_provider
        self.model_name = settings.embedding_model
        self.model = None
        self.dim = dim or settings.embedding_dim
        if self.provider == 'sentence_transformers':
            try:
                from sentence_transformers import SentenceTransformer
            except Exception as exc:
                raise RuntimeError(
                    'sentence_transformers provider selected but sentence-transformers could not be imported.'
                ) from exc
            self.model = SentenceTransformer(self.model_name, device='cpu')
            self.dim = int(self.model.get_sentence_embedding_dimension() or self.dim)
        elif self.provider != 'local_hash':
            raise ValueError(f'Unsupported embedding provider: {self.provider}')
        cache_name = 'embedding_cache.json'
        if self.provider != 'local_hash':
            suffix = hashlib.sha256(f'{self.provider}:{self.model_name}'.encode()).hexdigest()[:12]
            cache_name = f'embedding_cache_{self.provider}_{suffix}.json'
        self.cache_path = settings.indexes_dir / cache_name
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache = json.loads(self.cache_path.read_text()) if self.cache_path.exists() else {}

    def embed(self, text: str):
        key = hashlib.sha256(text.encode()).hexdigest()
        if key in self.cache:
            return self.cache[key]
        if self.model is not None:
            out = self.model.encode(text, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
            value = np.asarray(out, dtype=np.float32).tolist()
            self.cache[key] = value
            return value
        v = np.zeros(self.dim, dtype=np.float32)
        for tok in [t.lower().strip('.,;:()[]') for t in text.split() if t.strip()]:
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            v[h % self.dim] += 1.0
            if len(tok) > 4:
                v[(h // 7) % self.dim] += 0.35
        n = float(np.linalg.norm(v)) or 1.0
        out = (v / n).tolist()
        self.cache[key] = out
        if len(self.cache) % 25 == 0:
            self.flush()
        return out

    def embed_batch(self, texts):
        if self.model is None:
            return [self.embed(text) for text in texts]
        missing = [text for text in texts if hashlib.sha256(text.encode()).hexdigest() not in self.cache]
        if missing:
            values = self.model.encode(missing, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
            for text, value in zip(missing, values):
                self.cache[hashlib.sha256(text.encode()).hexdigest()] = np.asarray(value, dtype=np.float32).tolist()
        return [self.cache[hashlib.sha256(text.encode()).hexdigest()] for text in texts]

    def flush(self):
        self.cache_path.write_text(json.dumps(self.cache), encoding='utf-8')
