from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
Base=declarative_base()
class Source(Base):
    __tablename__='sources'; id=Column(String, primary_key=True); name=Column(String, nullable=False); source_type=Column(String, default='demo'); url=Column(String); license=Column(String); license_status=Column(String, default='unknown'); raw_path=Column(String); status=Column(String, default='registered'); created_at=Column(DateTime, default=datetime.utcnow); documents=relationship('Document', back_populates='source', cascade='all, delete-orphan')
class Document(Base):
    __tablename__='documents'; id=Column(String, primary_key=True); source_id=Column(String, ForeignKey('sources.id'), nullable=False); title=Column(String, nullable=False); path=Column(String); doc_type=Column(String, default='txt'); license=Column(String); year=Column(Integer); topic=Column(String); publication_type=Column(String); medical_category=Column(String); sha256=Column(String, index=True); status=Column(String, default='processed'); created_at=Column(DateTime, default=datetime.utcnow); source=relationship('Source', back_populates='documents'); chunks=relationship('Chunk', back_populates='document', cascade='all, delete-orphan')
class Chunk(Base):
    __tablename__='chunks'; id=Column(String, primary_key=True); document_id=Column(String, ForeignKey('documents.id'), nullable=False); parent_id=Column(String, index=True); chunk_type=Column(String, default='child'); section=Column(String); text=Column(Text, nullable=False); token_count=Column(Integer, default=0); start_char=Column(Integer); end_char=Column(Integer); vector_indexed=Column(Boolean, default=False); bm25_indexed=Column(Boolean, default=False); document=relationship('Document', back_populates='chunks')
class IngestionJob(Base):
    __tablename__='ingestion_jobs'; id=Column(String, primary_key=True); source_id=Column(String); status=Column(String, default='queued'); current_file=Column(String); total_files=Column(Integer, default=0); processed_files=Column(Integer, default=0); failed_files=Column(Integer, default=0); logs_json=Column(Text, default='[]'); created_at=Column(DateTime, default=datetime.utcnow); updated_at=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
class QuestionLog(Base):
    __tablename__='question_logs'; id=Column(String, primary_key=True); question=Column(Text); pipeline_used=Column(String); answer=Column(Text); latency_ms=Column(Float, default=0); citation_coverage=Column(Float, default=0); hallucination_risk=Column(String, default='unknown'); safety_status=Column(String, default='allowed'); created_at=Column(DateTime, default=datetime.utcnow)
class SafetyRefusal(Base):
    __tablename__='safety_refusals'; id=Column(String, primary_key=True); question=Column(Text); category=Column(String); reason=Column(Text); created_at=Column(DateTime, default=datetime.utcnow)
class EvaluationQuestion(Base):
    __tablename__='evaluation_questions'; id=Column(String, primary_key=True); question=Column(Text); expected_doc_ids=Column(Text, default='[]'); answer_key=Column(Text); tags=Column(Text, default='[]'); created_at=Column(DateTime, default=datetime.utcnow)
class EvaluationRun(Base):
    __tablename__='evaluation_runs'; id=Column(String, primary_key=True); pipeline_id=Column(String); metrics_json=Column(Text); report_path=Column(String); created_at=Column(DateTime, default=datetime.utcnow)
