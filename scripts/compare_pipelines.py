import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'backend'))
from app.db.session import SessionLocal, init_db
from app.services.rag_service import RAGService
if __name__ == '__main__':
    init_db(); db=SessionLocal()
    q=' '.join(sys.argv[1:]) or 'What are common symptoms of hypertension?'
    out=RAGService().compare(db,q,['vector','bm25','hybrid','reranked_hybrid','section_aware'],5)
    print(json.dumps(out, indent=2))
