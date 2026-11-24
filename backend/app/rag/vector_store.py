import hashlib
import json
from dataclasses import dataclass, asdict
import numpy as np
from app.core.config import settings
from app.db.models import Chunk, Document, Source
from app.rag.embeddings import EmbeddingService
@dataclass
class VectorRecord:
    chunk_id:str; document_id:str; parent_id:str|None; title:str; source_name:str|None; section:str|None; text:str; embedding:list[float]; metadata:dict
class LocalVectorStore:
    def __init__(self):
        self.embedder = EmbeddingService()
        index_name = 'vector_index.json'
        if settings.embedding_provider != 'local_hash':
            suffix = hashlib.sha256(f'{settings.embedding_provider}:{settings.embedding_model}'.encode()).hexdigest()[:12]
            index_name = f'vector_index_{settings.embedding_provider}_{suffix}.json'
        self.path = settings.indexes_dir / index_name
        self.records = []
        self.load()
    def load(self):
        if not self.path.exists():
            self.records = []
            return
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f'Vector index cannot be read safely: {self.path}') from exc
        if not isinstance(data, list):
            raise RuntimeError(f'Vector index must contain a JSON list: {self.path}')
        try:
            self.records = [VectorRecord(**r) for r in data]
        except (TypeError, KeyError) as exc:
            raise RuntimeError(f'Vector index contains an invalid record: {self.path}') from exc
    def save(self):
        from app.rag.embeddings import _atomic_json_write
        _atomic_json_write(self.path, [asdict(r) for r in self.records])
        self.embedder.flush()
    def rebuild_from_db(self,db):
        rows=db.query(Chunk,Document,Source).join(Document,Chunk.document_id==Document.id).join(Source,Document.source_id==Source.id).filter(Chunk.chunk_type=='child').all(); self.records=[]
        for c,d,s in rows:
            meta={'source_id':d.source_id,'source_name':s.name,'doc_type':d.doc_type,'year':d.year,'topic':d.topic,'publication_type':d.publication_type,'medical_category':d.medical_category,'license':d.license}
            self.records.append(VectorRecord(c.id,d.id,c.parent_id,d.title,s.name,c.section,c.text,self.embedder.embed(c.text),meta))
        self.save(); return len(self.records)
    def search(self,query,top_k=6,filters=None):
        self.load(); filters=filters or {}; q=np.array(self.embedder.embed(query),dtype=np.float32); out=[]
        for r in self.records:
            if not self._ok(r.metadata,filters): continue
            v=np.array(r.embedding,dtype=np.float32); score=float(np.dot(q,v)/((np.linalg.norm(q) or 1)*(np.linalg.norm(v) or 1)))
            out.append({**asdict(r),'score':score,'vector_score':score,'score_type':'vector'})
        return sorted(out,key=lambda x:x['score'],reverse=True)[:top_k]
    def _ok(self,meta,filters):
        for k,v in filters.items():
            if v in (None,''): continue
            if isinstance(v,list):
                if meta.get(k) not in v: return False
            elif str(meta.get(k,'')).lower()!=str(v).lower(): return False
        return True
