from app.rag.pipelines.base import BaseRAGPipeline, PipelineResult
from app.rag.bm25_store import BM25Store
class BM25RAG(BaseRAGPipeline):
    id='bm25'; name='BM25 RAG'; description='Keyword search for exact biomedical terms.'
    def retrieve(self,db,question,top_k=6,filters=None):
        res=BM25Store().search(question,top_k,filters); [r.update(reason='Selected by BM25 exact term relevance.') for r in res]
        return PipelineResult(self.id,res,{'bm25_hits':len(res)})
