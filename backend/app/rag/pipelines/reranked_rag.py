from app.rag.pipelines.base import BaseRAGPipeline, PipelineResult
from app.rag.pipelines.hybrid_rag import HybridRAG
from app.rag.reranker import Reranker
class RerankedHybridRAG(BaseRAGPipeline):
    id='reranked_hybrid'; name='Reranked Hybrid RAG'; description='Hybrid retrieval plus reranking.'; supports_reranking=True
    def retrieve(self,db,question,top_k=6,filters=None):
        base=HybridRAG().retrieve(db,question,top_k*3,filters); res=Reranker().rerank(question,base.retrieved,top_k)
        return PipelineResult(self.id,res,{**base.retrieval_scores,'reranked_hits':len(res)})
