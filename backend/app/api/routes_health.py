from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.dashboard_service import DashboardService
router = APIRouter(tags=['system'])
@router.get('/health')
def health(): return {'status':'ok','service':'ClinicalRAG Intelligence Platform'}
@router.get('/system/status')
def system_status(db: Session = Depends(get_db)):
    return {'status':'ready','dashboard':DashboardService().stats(db)}
@router.get('/dashboard/stats')
def dashboard_stats(db: Session = Depends(get_db)):
    return DashboardService().stats(db)
