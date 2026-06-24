from app.rag.pipelines.base import BaseRAGPipeline, PipelineResult
from app.rag.pipelines.hybrid_rag import HybridRAG
class MetadataFilteredRAG(BaseRAGPipeline):
    id='metadata_filtered'; name='Metadata-Filtered RAG'; description='Applies metadata filters before hybrid retrieval.'
    def retrieve(self,db,question,top_k=6,filters=None):
        res=HybridRAG().retrieve(db,question,top_k,filters or {}); [r.update(reason='Selected after metadata filtering and hybrid scoring.') for r in res.retrieved]
        return PipelineResult(self.id,res.retrieved,{**res.retrieval_scores,'filters':filters or {}})
