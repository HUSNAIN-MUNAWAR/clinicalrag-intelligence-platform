from app.db.models import Chunk
from app.rag.pipelines.base import BaseRAGPipeline, PipelineResult
from app.rag.pipelines.vector_rag import VectorRAG
class ParentChildRAG(BaseRAGPipeline):
    id='parent_child'; name='Parent-Child RAG'; description='Retrieves child chunks but returns parent section context.'
    def retrieve(self,db,question,top_k=6,filters=None):
        child=VectorRAG().retrieve(db,question,top_k*2,filters); out=[]; seen=set()
        for c in child.retrieved:
            key=(c.get('document_id'),c.get('parent_id'))
            if key in seen: continue
            seen.add(key); x=dict(c)
            parent=db.query(Chunk).filter(Chunk.id==c.get('parent_id')).first() if c.get('parent_id') else None
            if parent: x['text']=parent.text; x['reason']='Child matched query; parent section returned for context.'
            out.append(x)
            if len(out)>=top_k: break
        return PipelineResult(self.id,out,{'child_hits':len(child.retrieved),'parent_contexts':len(out)})
