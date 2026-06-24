from app.rag.pipelines.base import BaseRAGPipeline, PipelineResult
from app.rag.vector_store import LocalVectorStore
from app.rag.bm25_store import BM25Store
def norm(items):
    if not items: return {}
    vals=[float(x.get('score',0)) for x in items]; mn=min(vals); mx=max(vals)
    return {x['chunk_id']:((float(x.get('score',0))-mn)/(mx-mn+1e-9) if mx!=mn else 1.0) for x in items}
class HybridRAG(BaseRAGPipeline):
    id='hybrid'; name='Hybrid RAG'; description='Weighted fusion of vector and BM25 retrieval.'
    def retrieve(self,db,question,top_k=6,filters=None):
        v=LocalVectorStore().search(question,top_k*2,filters); b=BM25Store().search(question,top_k*2,filters); vn=norm(v); bn=norm(b); merged={}
        for r in v+b:
            cid=r['chunk_id']; merged.setdefault(cid,dict(r)); merged[cid]['vector_score']=vn.get(cid,merged[cid].get('vector_score')); merged[cid]['bm25_score']=bn.get(cid,merged[cid].get('bm25_score')); merged[cid]['score']=0.55*vn.get(cid,0)+0.45*bn.get(cid,0); merged[cid]['score_type']='hybrid'; merged[cid]['reason']='Selected by weighted fusion of vector and BM25 retrieval.'
        res=sorted(merged.values(),key=lambda x:x['score'],reverse=True)[:top_k]
        return PipelineResult(self.id,res,{'vector_hits':len(v),'bm25_hits':len(b),'hybrid_hits':len(res)})
