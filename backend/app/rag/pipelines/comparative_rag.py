from app.rag.pipelines.registry import get_pipeline
class ComparativeRAG:
    def compare(self,db,question,pipeline_ids,top_k=6):
        rows=[]
        for pid in pipeline_ids:
            res=get_pipeline(pid).retrieve(db,question,top_k,{})
            rows.append({'pipeline_id':pid,'retrieved_count':len(res.retrieved),'top_documents':[r.get('title') for r in res.retrieved[:3]],'scores':[round(float(r.get('score',0)),4) for r in res.retrieved[:top_k]],'retrieved_chunks':res.retrieved,'retrieval_scores':res.retrieval_scores})
        return {'question':question,'comparisons':rows}
