from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Document, Chunk
from app.schemas.documents import DocumentResponse
from app.services.index_service import IndexService
router = APIRouter(prefix='/documents', tags=['documents'])
@router.get('', response_model=list[DocumentResponse])
def list_documents(db: Session=Depends(get_db)):
    return db.query(Document).order_by(Document.created_at.desc()).all()
@router.get('/{document_id}')
def get_document(document_id: str, db: Session=Depends(get_db)):
    doc = db.query(Document).filter(Document.id==document_id).first()
    if not doc: raise HTTPException(404,'document not found')
    chunks = db.query(Chunk).filter(Chunk.document_id==document_id, Chunk.chunk_type=='child').limit(50).all()
    return {'document': doc, 'chunks': chunks}
@router.delete('/{document_id}')
def delete_document(document_id: str, db: Session=Depends(get_db)):
    ok = IndexService().delete_document_from_db(db, document_id)
    if not ok: raise HTTPException(404,'document not found')
    return {'deleted': True, 'document_id': document_id}
@router.post('/{document_id}/reindex')
def reindex_document(document_id: str, db: Session=Depends(get_db)):
    if not db.query(Document).filter(Document.id==document_id).first(): raise HTTPException(404,'document not found')
    return IndexService().rebuild(db)
