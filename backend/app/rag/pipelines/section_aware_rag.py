from app.rag.pipelines.base import BaseRAGPipeline, PipelineResult
from app.rag.pipelines.hybrid_rag import HybridRAG
WEIGHTS={'abstract':1.1,'diagnosis':1.18,'treatment':1.12,'warnings':1.2,'contraindications':1.2,'conclusion':1.08,'references':0.75,'body':1.0}
class SectionAwareMedicalRAG(BaseRAGPipeline):
    id='section_aware'; name='Section-Aware Medical RAG'; description='Reweights by medical section labels.'
    def retrieve(self,db,question,top_k=6,filters=None):
        base=HybridRAG().retrieve(db,question,top_k*2,filters)
        for r in base.retrieved:
            w=WEIGHTS.get(r.get('section') or 'body',1.0); r['score']=float(r.get('score',0))*w; r['reason']=f'Hybrid match reweighted by medical section {r.get("section")}.'
        return PipelineResult(self.id,sorted(base.retrieved,key=lambda x:x['score'],reverse=True)[:top_k],{**base.retrieval_scores,'section_weights':WEIGHTS})
