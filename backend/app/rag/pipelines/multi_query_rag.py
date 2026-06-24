from app.rag.pipelines.base import BaseRAGPipeline, PipelineResult
from app.rag.pipelines.hybrid_rag import HybridRAG
SYN={'high blood pressure':'hypertension','heart attack':'myocardial infarction','side effects':'adverse effects','breathing difficulty':'dyspnea'}
def expand_query(q):
    qs=[q]; low=q.lower()
    for a,b in SYN.items():
        if a in low: qs.append(low.replace(a,b))
        if b in low: qs.append(low.replace(b,a))
    qs.append(q+' symptoms diagnosis treatment warnings')
    return list(dict.fromkeys(qs))[:4]
class MultiQueryRAG(BaseRAGPipeline):
    id='multi_query'; name='Multi-Query RAG'; description='Expands question into multiple query variants and merges results.'; experimental=True
    def retrieve(self,db,question,top_k=6,filters=None):
        merged={}; queries=expand_query(question)
        for q in queries:
            res=HybridRAG().retrieve(db,q,top_k,filters)
            for rank,item in enumerate(res.retrieved,1):
                cid=item['chunk_id']; score=float(item.get('score',0))+1/rank
                if cid not in merged or score>merged[cid]['score']:
                    x=dict(item); x['score']=score; x['reason']=f'Selected by multi-query variant: {q[:100]}'; merged[cid]=x
        return PipelineResult(self.id,sorted(merged.values(),key=lambda x:x['score'],reverse=True)[:top_k],{'queries':queries,'merged_hits':len(merged)})
