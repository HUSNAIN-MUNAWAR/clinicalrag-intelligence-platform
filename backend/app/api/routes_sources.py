from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Source
from app.schemas.sources import SourceCreate, SourceResponse, LicenseValidationRequest, LicenseValidationResponse
from app.services.source_service import SourceService
from app.ingestion.license_checker import LicenseChecker
router = APIRouter(prefix='/sources', tags=['sources'])
@router.get('', response_model=list[SourceResponse])
def list_sources(db: Session=Depends(get_db)): return SourceService().list_sources(db)
@router.post('', response_model=SourceResponse)
def create_source(payload: SourceCreate, db: Session=Depends(get_db)): return SourceService().create_source(db, payload)
@router.post('/download')
def download_source(payload: SourceCreate, db: Session=Depends(get_db)):
    src = SourceService().create_source(db, payload)
    return {'source_id': src.id, 'status': 'registered', 'next_step': 'POST /ingestion/start with this source_id'}
@router.post('/validate-license', response_model=LicenseValidationResponse)
def validate_license(payload: LicenseValidationRequest): return LicenseChecker().validate(payload.license, payload.url)
@router.delete('/{source_id}')
def delete_source(source_id: str, db: Session=Depends(get_db)):
    ok = SourceService().delete_source(db, source_id)
    if not ok: raise HTTPException(404,'source not found')
    return {'deleted': True, 'source_id': source_id}
