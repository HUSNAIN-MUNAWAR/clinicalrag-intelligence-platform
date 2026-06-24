import json
from uuid import uuid4
from sqlalchemy.orm import Session
from app.db.models import EvaluationQuestion, Document

def _doc_ids_like(db: Session, text: str) -> list[str]:
    docs = db.query(Document).all()
    return [d.id for d in docs if text.lower() in (d.title or '').lower()]

def seed_demo_questions(db: Session):
    if db.query(EvaluationQuestion).count():
        return
    rows = [
        ('What are common symptoms of hypertension?', _doc_ids_like(db,'hypertension'), 'General symptoms and silent nature of hypertension.'),
        ('What warning signs are mentioned for asthma?', _doc_ids_like(db,'asthma'), 'Wheezing, shortness of breath, emergency warning signs.'),
        ('How should medical RAG systems communicate limitations?', _doc_ids_like(db,'lifestyle'), 'Ground answers in evidence and communicate limitations.'),
    ]
    for q, ids, answer_key in rows:
        db.add(EvaluationQuestion(id=str(uuid4()), question=q, expected_doc_ids=json.dumps(ids), answer_key=answer_key, tags='["demo"]'))
    db.commit()
