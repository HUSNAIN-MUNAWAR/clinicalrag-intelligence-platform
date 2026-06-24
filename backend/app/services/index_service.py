from sqlalchemy.orm import Session
from app.db.models import Document
from app.rag.vector_store import LocalVectorStore
from app.rag.bm25_store import BM25Store

class IndexService:
    def __init__(self):
        self.vector = LocalVectorStore()
        self.bm25 = BM25Store()
    def rebuild(self, db: Session) -> dict:
        v = self.vector.rebuild_from_db(db)
        b = self.bm25.rebuild_from_db(db)
        return {'indexed_chunks': v, 'bm25_chunks': b, 'vector_index_path': str(self.vector.path), 'bm25_index_path': str(self.bm25.path)}
    def delete_document_from_db(self, db: Session, document_id: str) -> bool:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc: return False
        db.delete(doc); db.commit(); self.rebuild(db); return True
