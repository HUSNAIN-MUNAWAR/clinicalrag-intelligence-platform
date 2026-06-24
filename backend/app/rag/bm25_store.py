import json, math, re
from dataclasses import dataclass, asdict
from collections import Counter, defaultdict
from app.core.config import settings
from app.db.models import Chunk, Document, Source
TOKEN_RE=re.compile(r'[A-Za-z0-9][A-Za-z0-9\-]+')
def tokenize(text): return [t.lower() for t in TOKEN_RE.findall(text or '')]
@dataclass
class BM25Record:
    chunk_id:str; document_id:str; parent_id:str|None; title:str; source_name:str|None; section:str|None; text:str; tokens:list[str]; metadata:dict
class BM25Store:
    def __init__(self): self.path=settings.indexes_dir/'bm25_index.json'; self.records=[]; self.load()
    def load(self): self.records=[BM25Record(**r) for r in json.loads(self.path.read_text())] if self.path.exists() else []
    def save(self): self.path.parent.mkdir(parents=True, exist_ok=True); self.path.write_text(json.dumps([asdict(r) for r in self.records], ensure_ascii=False), encoding='utf-8')
    def rebuild_from_db(self,db):
        rows=db.query(Chunk,Document,Source).join(Document,Chunk.document_id==Document.id).join(Source,Document.source_id==Source.id).filter(Chunk.chunk_type=='child').all(); self.records=[]
        for c,d,s in rows:
            meta={'source_id':d.source_id,'source_name':s.name,'doc_type':d.doc_type,'year':d.year,'topic':d.topic,'publication_type':d.publication_type,'medical_category':d.medical_category,'license':d.license}
            self.records.append(BM25Record(c.id,d.id,c.parent_id,d.title,s.name,c.section,c.text,tokenize(c.text),meta))
        self.save(); return len(self.records)
    def search(self,query,top_k=6,filters=None):
        self.load(); filters=filters or {}; terms=tokenize(query); N=len(self.records)
        if not terms or not N: return []
        avgdl=sum(len(r.tokens) for r in self.records)/max(N,1); dfs=defaultdict(int)
        for r in self.records:
            seen=set(r.tokens)
            for t in set(terms):
                if t in seen: dfs[t]+=1
        out=[]
        for r in self.records:
            if not self._ok(r.metadata,filters): continue
            freqs=Counter(r.tokens); dl=len(r.tokens) or 1; score=0.0
            for t in terms:
                df=dfs.get(t,0)
                if not df: continue
                idf=math.log(1+(N-df+0.5)/(df+0.5)); tf=freqs.get(t,0); score+=idf*(tf*2.5)/(tf+1.5*(1-0.75+0.75*dl/max(avgdl,1)))
            if score>0: out.append({**asdict(r),'score':score,'bm25_score':score,'score_type':'bm25'})
        return sorted(out,key=lambda x:x['score'],reverse=True)[:top_k]
    def _ok(self,meta,filters):
        for k,v in filters.items():
            if v in (None,''): continue
            if isinstance(v,list):
                if meta.get(k) not in v: return False
            elif str(meta.get(k,'')).lower()!=str(v).lower(): return False
        return True
