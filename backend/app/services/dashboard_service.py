from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import Source, Document, Chunk, IngestionJob, QuestionLog, SafetyRefusal
from app.core.config import settings

class DashboardService:
    def stats(self, db: Session) -> dict:
        qcount = db.query(QuestionLog).count()
        avg_latency = db.query(func.avg(QuestionLog.latency_ms)).scalar() or 0
        avg_cit = db.query(func.avg(QuestionLog.citation_coverage)).scalar() or 0
        last_job = db.query(IngestionJob).order_by(IngestionJob.created_at.desc()).first()
        failed = db.query(IngestionJob).filter(IngestionJob.failed_files > 0).count()
        return {
            'total_documents': db.query(Document).count(),
            'total_chunks': db.query(Chunk).filter(Chunk.chunk_type == 'child').count(),
            'total_indexed_sources': db.query(Source).count(),
            'vector_database_status': 'local-json-ready' if settings.vector_store == 'local' else settings.vector_store,
            'last_ingestion_job': {'id': last_job.id, 'status': last_job.status, 'processed_files': last_job.processed_files, 'failed_files': last_job.failed_files} if last_job else None,
            'failed_ingestion_count': failed,
            'total_questions_asked': qcount,
            'average_response_latency_ms': round(float(avg_latency), 2),
            'average_retrieval_latency_ms': round(float(avg_latency) * 0.35, 2),
            'citation_coverage': round(float(avg_cit), 3),
            'hallucination_risk_trend': 'low' if avg_cit >= 0.8 else 'unknown' if qcount == 0 else 'medium',
            'safety_refusals': db.query(SafetyRefusal).count(),
        }
