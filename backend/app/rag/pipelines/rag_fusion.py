from app.rag.pipelines.base import BaseRAGPipeline, PipelineResult
from app.rag.pipelines.hybrid_rag import HybridRAG
from app.rag.pipelines.multi_query_rag import expand_query
class RAGFusion(BaseRAGPipeline):
    id='rag_fusion'; name='RAG-Fusion'; description='Reciprocal-rank fusion across multiple query variants.'; experimental=True
    def retrieve(self,db,question,top_k=6,filters=None):
        fused={}; queries=expand_query(question); k=60
        for q in queries:
            res=HybridRAG().retrieve(db,q,top_k*2,filters)
            for rank,item in enumerate(res.retrieved,1):
                cid=item['chunk_id']; fused.setdefault(cid,{**item,'score':0.0,'fusion_queries':[]}); fused[cid]['score']+=1/(k+rank); fused[cid]['fusion_queries'].append(q)
        out=sorted(fused.values(),key=lambda x:x['score'],reverse=True)[:top_k]
        for r in out: r['score_type']='rrf'; r['reason']='Selected by reciprocal-rank fusion across query variants.'
        return PipelineResult(self.id,out,{'queries':queries,'rrf_k':k})
