from app.rag.bm25_store import tokenize
class Reranker:
    def rerank(self,query,candidates,top_k=6):
        q=set(tokenize(query)); out=[]
        for c in candidates:
            overlap=len(q & set(tokenize(c.get('text',''))))/max(len(q),1); prior=float(c.get('score',0)); section_bonus=0.08 if c.get('section') in {'diagnosis','treatment','warnings','abstract','conclusion'} else 0
            x=dict(c); x['reranker_score']=0.65*prior+0.35*overlap+section_bonus; x['score']=x['reranker_score']; x['score_type']='reranked'; x['reason']=f'Reranked by lexical overlap {overlap:.2f} plus section prior.'; out.append(x)
        return sorted(out,key=lambda x:x['score'],reverse=True)[:top_k]
