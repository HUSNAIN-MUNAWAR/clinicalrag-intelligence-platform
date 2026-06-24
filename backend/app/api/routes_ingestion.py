import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import IngestionJob
from app.schemas.ingestion import IngestionStartRequest, IngestionJobResponse
from app.ingestion.pipeline import IngestionPipeline
router = APIRouter(prefix='/ingestion', tags=['ingestion'])
@router.post('/start', response_model=IngestionJobResponse)
def start_ingestion(payload: IngestionStartRequest, db: Session=Depends(get_db)):
    return IngestionPipeline().run(db, payload.source_id)
@router.post('/stop')
def stop_ingestion(): return {'status':'not_running','note':'Local demo jobs run synchronously; background cancellation can be wired to Celery/RQ.'}
@router.get('/jobs', response_model=list[IngestionJobResponse])
def jobs(db: Session=Depends(get_db)): return db.query(IngestionJob).order_by(IngestionJob.created_at.desc()).all()
@router.get('/jobs/{job_id}', response_model=IngestionJobResponse)
def get_job(job_id: str, db: Session=Depends(get_db)):
    job=db.query(IngestionJob).filter(IngestionJob.id==job_id).first()
    if not job: raise HTTPException(404,'job not found')
    return job
@router.get('/jobs/{job_id}/logs')
def job_logs(job_id: str, db: Session=Depends(get_db)):
    job=db.query(IngestionJob).filter(IngestionJob.id==job_id).first()
    if not job: raise HTTPException(404,'job not found')
    return json.loads(job.logs_json or '[]')
@router.post('/jobs/{job_id}/retry', response_model=IngestionJobResponse)
def retry(job_id: str, db: Session=Depends(get_db)):
    job=db.query(IngestionJob).filter(IngestionJob.id==job_id).first()
    if not job: raise HTTPException(404,'job not found')
    return IngestionPipeline().run(db, job.source_id)
@router.get('/jobs/{job_id}/events')
def job_events(job_id: str, db: Session=Depends(get_db)):
    job=db.query(IngestionJob).filter(IngestionJob.id==job_id).first()
    if not job: raise HTTPException(404,'job not found')
    logs=json.loads(job.logs_json or '[]')
    def gen():
        for row in logs:
            yield f"data: {json.dumps(row)}\n\n"
    return StreamingResponse(gen(), media_type='text/event-stream')
