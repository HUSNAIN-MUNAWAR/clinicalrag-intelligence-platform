from app.rag.pipelines.base import BaseRAGPipeline, PipelineResult
from app.rag.pipelines.reranked_rag import RerankedHybridRAG
class EvaluationAwareRAG(BaseRAGPipeline):
    id='evaluation_aware'; name='Evaluation-Aware RAG'; description='Reranked hybrid with extra evaluation logging signals.'; supports_reranking=True; experimental=True
    def retrieve(self,db,question,top_k=6,filters=None):
        res=RerankedHybridRAG().retrieve(db,question,top_k,filters); unique=len({r.get('document_id') for r in res.retrieved}); avg=sum(float(r.get('score',0)) for r in res.retrieved)/max(len(res.retrieved),1)
        for r in res.retrieved: r['reason']='Evaluation-aware retrieval logs citation/groundedness signals. '+(r.get('reason') or '')
        return PipelineResult(self.id,res.retrieved,{**res.retrieval_scores,'unique_docs':unique,'avg_score':avg})
