from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import SafetyRefusal
from app.schemas.safety import SafetyCheckRequest
from app.safety.classifier import MedicalSafetyClassifier
from app.safety.rules import public_rules
router = APIRouter(prefix='/safety', tags=['safety'])
@router.post('/check')
def check(payload: SafetyCheckRequest):
    d=MedicalSafetyClassifier().check(payload.text or payload.question or "")
    return {'allowed':d.allowed,'category':d.category,'severity':d.severity,'reason':d.reason,'matched_patterns':d.matched_patterns or []}
@router.get('/refusals')
def refusals(db: Session=Depends(get_db)):
    return db.query(SafetyRefusal).order_by(SafetyRefusal.created_at.desc()).limit(100).all()
@router.get('/rules')
def rules(): return public_rules()
