from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.rag import RagAskRequest, RagRetrieveRequest, RagCompareRequest, RagAnswerResponse
from app.services.rag_service import RAGService
from app.rag.pipelines import get_pipeline
router = APIRouter(prefix='/rag', tags=['rag'])
@router.get('/pipelines')
def pipelines(): return RAGService().pipelines()
@router.get('/pipelines/{pipeline_id}')
def pipeline_detail(pipeline_id: str):
    for p in RAGService().pipelines():
        if p['id']==pipeline_id: return p
    raise HTTPException(404,'pipeline not implemented')
@router.post('/retrieve')
def retrieve(payload: RagRetrieveRequest, db: Session=Depends(get_db)):
    res = RAGService().retrieve(db, payload.question, payload.pipeline_id, payload.top_k, payload.filters)
    return {'pipeline_id': res.pipeline_id, 'retrieved_chunks': res.retrieved, 'retrieval_scores': res.retrieval_scores}
@router.post('/ask', response_model=RagAnswerResponse)
def ask(payload: RagAskRequest, db: Session=Depends(get_db)):
    return RAGService().ask(db, payload.question, payload.pipeline_id, payload.top_k, payload.filters, payload.safety_mode, payload.model_provider)
@router.post('/compare')
def compare(payload: RagCompareRequest, db: Session=Depends(get_db)):
    return RAGService().compare(db, payload.question, payload.pipeline_ids, payload.top_k)
@router.post('/explain-retrieval')
def explain(payload: RagRetrieveRequest, db: Session=Depends(get_db)):
    res = RAGService().retrieve(db, payload.question, payload.pipeline_id, payload.top_k, payload.filters)
    return {'question': payload.question, 'pipeline_id': payload.pipeline_id, 'explanations': [{'chunk_id': r.get('chunk_id'), 'title': r.get('title'), 'section': r.get('section'), 'score': r.get('score'), 'reason': r.get('reason'), 'parent_id': r.get('parent_id')} for r in res.retrieved]}
