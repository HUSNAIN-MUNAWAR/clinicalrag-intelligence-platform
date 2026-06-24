import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'backend'))
from app.db.session import SessionLocal, init_db
from app.services.index_service import IndexService
if __name__ == '__main__':
    init_db(); db=SessionLocal(); print(IndexService().rebuild(db))
