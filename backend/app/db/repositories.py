import json
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.db.models import Source, Document, Chunk, IngestionJob, QuestionLog, SafetyRefusal

def counts(db:Session):
    return {'sources':db.query(func.count(Source.id)).scalar() or 0,'documents':db.query(func.count(Document.id)).scalar() or 0,'chunks':db.query(func.count(Chunk.id)).scalar() or 0,'questions':db.query(func.count(QuestionLog.id)).scalar() or 0,'refusals':db.query(func.count(SafetyRefusal.id)).scalar() or 0}
def job_logs(job:IngestionJob):
    try: return json.loads(job.logs_json or '[]')
    except Exception: return []
def append_job_log(db, job, level, message):
    logs=job_logs(job); logs.append({'level':level,'message':message}); job.logs_json=json.dumps(logs[-500:]); db.add(job); db.commit()
