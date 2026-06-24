import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from uuid import uuid4
from app.db.session import get_db
from app.db.models import EvaluationQuestion, EvaluationRun
from app.schemas.evaluation import EvaluationQuestionCreate, EvaluationRunRequest
from app.evaluation.datasets import seed_demo_questions
from app.evaluation.evaluator import RAGEvaluator
router = APIRouter(prefix='/evaluation', tags=['evaluation'])
@router.post('/questions')
def add_question(payload: EvaluationQuestionCreate, db: Session=Depends(get_db)):
    row=EvaluationQuestion(id=str(uuid4()), question=payload.question, expected_doc_ids=json.dumps(payload.expected_doc_ids), answer_key=payload.answer_key, tags=json.dumps(payload.tags))
    db.add(row); db.commit(); db.refresh(row); return row
@router.get('/questions')
def list_questions(db: Session=Depends(get_db)):
    seed_demo_questions(db); return db.query(EvaluationQuestion).all()
@router.post('/run')
def run_eval(payload: EvaluationRunRequest, db: Session=Depends(get_db)):
    seed_demo_questions(db); run=RAGEvaluator().run(db, payload.pipeline_id, payload.top_k); return {'run_id':run.id,'pipeline_id':run.pipeline_id,'metrics':json.loads(run.metrics_json),'report_path':run.report_path}
@router.get('/runs')
def runs(db: Session=Depends(get_db)): return db.query(EvaluationRun).order_by(EvaluationRun.created_at.desc()).all()
@router.get('/runs/{run_id}')
def get_run(run_id: str, db: Session=Depends(get_db)):
    run=db.query(EvaluationRun).filter(EvaluationRun.id==run_id).first()
    if not run: raise HTTPException(404,'run not found')
    return {'id':run.id,'pipeline_id':run.pipeline_id,'metrics':json.loads(run.metrics_json),'report_path':run.report_path}
@router.get('/runs/{run_id}/export')
def export_run(run_id: str, db: Session=Depends(get_db)):
    run=db.query(EvaluationRun).filter(EvaluationRun.id==run_id).first()
    if not run: raise HTTPException(404,'run not found')
    return FileResponse(run.report_path, media_type='application/json', filename=f'evaluation_{run_id}.json')
