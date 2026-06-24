import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'backend'))
from app.db.session import SessionLocal, init_db
from app.evaluation.datasets import seed_demo_questions
from app.evaluation.evaluator import RAGEvaluator
if __name__ == '__main__':
    init_db(); db=SessionLocal(); seed_demo_questions(db)
    pipeline = sys.argv[1] if len(sys.argv)>1 else 'hybrid'
    run=RAGEvaluator().run(db,pipeline,5)
    print(json.dumps({'run_id':run.id,'pipeline_id':run.pipeline_id,'report_path':run.report_path,'metrics':json.loads(run.metrics_json)}, indent=2))
