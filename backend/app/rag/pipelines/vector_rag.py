from app.rag.pipelines.base import BaseRAGPipeline, PipelineResult
from app.rag.vector_store import LocalVectorStore
class VectorRAG(BaseRAGPipeline):
    id='vector'; name='Naive Vector RAG'; description='Dense vector search over embedded chunks.'
    def retrieve(self,db,question,top_k=6,filters=None):
        res=LocalVectorStore().search(question,top_k,filters); [r.update(reason='Selected by vector cosine similarity.') for r in res]
        return PipelineResult(self.id,res,{'vector_hits':len(res)})
