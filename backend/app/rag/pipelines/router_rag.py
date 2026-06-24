from app.rag.pipelines.base import BaseRAGPipeline, PipelineResult
from app.rag.pipelines.bm25_rag import BM25RAG
from app.rag.pipelines.hybrid_rag import HybridRAG
from app.rag.pipelines.section_aware_rag import SectionAwareMedicalRAG
from app.rag.pipelines.rag_fusion import RAGFusion
class RouterRAG(BaseRAGPipeline):
    id='router'; name='Router RAG'; description='Rule-based selection of best retrieval pipeline.'; experimental=True
    def retrieve(self,db,question,top_k=6,filters=None):
        q=question.lower(); chosen=SectionAwareMedicalRAG() if any(x in q for x in ['diagnosis','treatment','warning','contraindication','symptom']) else (RAGFusion() if any(x in q for x in ['compare','difference','relationship']) else (BM25RAG() if any(ch.isdigit() for ch in q) else HybridRAG()))
        res=chosen.retrieve(db,question,top_k,filters)
        for r in res.retrieved: r['reason']=f'Router selected {chosen.id}. '+(r.get('reason') or '')
        return PipelineResult(self.id,res.retrieved,{'chosen_pipeline':chosen.id,**res.retrieval_scores})
