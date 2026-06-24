import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.db.session import SessionLocal, init_db
from app.ingestion.pipeline import IngestionPipeline
if __name__ == '__main__':
    init_db()
    db = SessionLocal()
    job = IngestionPipeline().run(db, None)
    print({'job_id': job.id, 'status': job.status, 'processed_files': job.processed_files, 'failed_files': job.failed_files})
