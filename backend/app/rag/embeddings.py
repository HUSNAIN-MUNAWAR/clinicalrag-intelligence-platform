import hashlib, json
import numpy as np
from app.core.config import settings
class EmbeddingService:
    def __init__(self, dim:int|None=None):
        self.dim=dim or settings.embedding_dim; self.cache_path=settings.indexes_dir/'embedding_cache.json'; self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache=json.loads(self.cache_path.read_text()) if self.cache_path.exists() else {}
    def embed(self,text:str):
        key=hashlib.sha256(text.encode()).hexdigest()
        if key in self.cache: return self.cache[key]
        v=np.zeros(self.dim,dtype=np.float32)
        for tok in [t.lower().strip('.,;:()[]') for t in text.split() if t.strip()]:
            h=int(hashlib.md5(tok.encode()).hexdigest(),16); v[h%self.dim]+=1.0
            if len(tok)>4: v[(h//7)%self.dim]+=0.35
        n=float(np.linalg.norm(v)) or 1.0; out=(v/n).tolist(); self.cache[key]=out
        if len(self.cache)%25==0: self.flush()
        return out
    def embed_batch(self,texts): return [self.embed(t) for t in texts]
    def flush(self): self.cache_path.write_text(json.dumps(self.cache), encoding='utf-8')
