import json
from pathlib import Path
from uuid import uuid4
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.models import Source, Document, Chunk, IngestionJob
from app.ingestion.parsers import get_parser
from app.ingestion.cleaners.text_cleaner import TextCleaner
from app.ingestion.chunkers.medical_chunker import MedicalChunker
from app.ingestion.metadata import enrich_metadata
from app.ingestion.source_adapters import DemoSourceAdapter, MedlinePlusAdapter, PMCOAAdapter
from app.ingestion.license_checker import LicenseChecker
from app.services.index_service import IndexService

ADAPTERS = {'demo': DemoSourceAdapter, 'medlineplus': MedlinePlusAdapter, 'pmc_oa': PMCOAAdapter, 'local': None}

class IngestionPipeline:
    def __init__(self):
        self.cleaner = TextCleaner()
        self.chunker = MedicalChunker(settings.chunk_size, settings.chunk_overlap)
        self.license_checker = LicenseChecker()

    def _log(self, db: Session, job: IngestionJob, msg: str):
        logs = json.loads(job.logs_json or '[]')
        logs.append({'ts': datetime.utcnow().isoformat(), 'message': msg})
        job.logs_json = json.dumps(logs[-1000:])
        job.updated_at = datetime.utcnow()
        db.commit()

    def _files_for_source(self, db: Session, source: Source) -> list[Path]:
        if source.source_type == 'demo':
            adapter = DemoSourceAdapter()
            return adapter.download(settings.raw_dir).files
        if source.source_type == 'medlineplus':
            adapter = MedlinePlusAdapter()
            if source.url: adapter.url = source.url
            return adapter.download(settings.raw_dir).files
        if source.source_type == 'pmc_oa':
            adapter = PMCOAAdapter()
            if source.url: adapter.oa_file_list = source.url
            return adapter.download(settings.raw_dir).files
        if source.raw_path:
            p = Path(source.raw_path)
            if p.is_dir():
                return [x for x in p.rglob('*') if x.suffix.lower() in {'.txt','.xml','.json','.html','.htm','.pdf'}]
            if p.exists():
                return [p]
        return []

    def run(self, db: Session, source_id: str | None = None) -> IngestionJob:
        source = db.query(Source).filter(Source.id == source_id).first() if source_id else None
        if not source:
            source = Source(id=str(uuid4()), name='Demo Medical Corpus', source_type='demo', license='CC-BY-4.0-demo', license_status='allowed', status='registered')
            db.add(source); db.commit(); db.refresh(source)
        job = IngestionJob(id=str(uuid4()), source_id=source.id, status='running')
        db.add(job); db.commit(); db.refresh(job)
        try:
            license_result = self.license_checker.validate(source.license or '', source.url or '')
            source.license_status = license_result.status
            if license_result.status == 'blocked':
                job.status = 'failed'; job.failed_files = 1; db.commit(); self._log(db, job, f'Blocked by license checker: {license_result.reason}'); return job
            files = self._files_for_source(db, source)
            job.total_files = len(files); db.commit()
            self._log(db, job, f'Found {len(files)} files for source {source.name}')
            seen_hashes = {x.sha256 for x in db.query(Document.sha256).all() if x.sha256}
            for path in files:
                job.current_file = str(path); db.commit(); self._log(db, job, f'Parsing {path.name}')
                try:
                    parser = get_parser(path)
                    parsed = parser.parse(path)
                    meta = enrich_metadata(parsed.metadata | {'license': source.license, 'source_id': source.id, 'path': str(path), 'title': parsed.title, 'text': parsed.text})
                    if meta['sha256'] in seen_hashes:
                        self._log(db, job, f'Skipped duplicate {path.name}')
                        job.processed_files += 1; db.commit(); continue
                    cleaned = self.cleaner.clean(parsed.text)
                    doc = Document(
                        id=str(uuid4()), source_id=source.id, title=meta.get('title') or path.stem, path=str(path),
                        doc_type=path.suffix.lower().lstrip('.'), license=source.license, year=meta.get('year'),
                        topic=meta.get('topic'), publication_type=meta.get('publication_type'), medical_category=meta.get('medical_category'),
                        sha256=meta['sha256'], status='processed'
                    )
                    db.add(doc); db.flush()
                    parent_child = self.chunker.chunk(cleaned, doc.id)
                    parent_id_map = {}
                    for parent in parent_child.parents:
                        pid = str(uuid4()); parent_id_map[parent.local_id] = pid
                        db.add(Chunk(id=pid, document_id=doc.id, parent_id=None, chunk_type='parent', section=parent.section, text=parent.text, token_count=len(parent.text.split()), start_char=parent.start_char, end_char=parent.end_char))
                    for child in parent_child.children:
                        db.add(Chunk(id=str(uuid4()), document_id=doc.id, parent_id=parent_id_map.get(child.parent_local_id), chunk_type='child', section=child.section, text=child.text, token_count=len(child.text.split()), start_char=child.start_char, end_char=child.end_char))
                    job.processed_files += 1; seen_hashes.add(meta['sha256']); db.commit(); self._log(db, job, f'Processed {path.name}: {len(parent_child.children)} child chunks')
                except Exception as exc:
                    job.failed_files += 1; db.commit(); self._log(db, job, f'ERROR {path.name}: {exc}')
            source.status = 'ingested'
            idx = IndexService().rebuild(db)
            self._log(db, job, f'Index rebuild complete: {idx}')
            job.status = 'completed' if job.failed_files == 0 else 'completed_with_errors'
            db.commit(); return job
        except Exception as exc:
            job.status = 'failed'; job.failed_files += 1; db.commit(); self._log(db, job, f'Fatal ingestion error: {exc}'); return job
