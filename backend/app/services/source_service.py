from uuid import uuid4
from sqlalchemy.orm import Session
from app.db.models import Source
from app.ingestion.license_checker import LicenseChecker

class SourceService:
    def list_sources(self, db: Session):
        return db.query(Source).order_by(Source.created_at.desc()).all()

    def create_source(self, db: Session, payload) -> Source:
        checker = LicenseChecker()
        status = checker.validate(payload.license or '', payload.url or '').status
        src = Source(
            id=str(uuid4()),
            name=payload.name,
            source_type=payload.source_type,
            url=payload.url,
            license=payload.license,
            raw_path=payload.raw_path,
            license_status=status,
            status='registered',
        )
        db.add(src); db.commit(); db.refresh(src)
        return src

    def delete_source(self, db: Session, source_id: str) -> bool:
        src = db.query(Source).filter(Source.id == source_id).first()
        if not src:
            return False
        db.delete(src); db.commit(); return True
