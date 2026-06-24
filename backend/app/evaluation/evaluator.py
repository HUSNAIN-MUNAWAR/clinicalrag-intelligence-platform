import json
from uuid import uuid4
from sqlalchemy.orm import Session
from app.db.models import EvaluationQuestion, EvaluationRun
from app.rag.pipelines import get_pipeline
from app.rag.citation_builder import CitationBuilder
from app.evaluation.metrics import recall_at_k, precision_at_k, mrr, ndcg_at_k
from app.evaluation.report_generator import EvaluationReportGenerator

class RAGEvaluator:
    def run(self, db: Session, pipeline_id: str = 'hybrid', top_k: int = 5) -> EvaluationRun:
        qs = db.query(EvaluationQuestion).all()
        pipeline = get_pipeline(pipeline_id)
        rows = []
        for q in qs:
            expected = json.loads(q.expected_doc_ids or '[]')
            result = pipeline.retrieve(db, q.question, top_k, {})
            citations, chunks, docs = CitationBuilder().build(result.retrieved)
            rows.append({
                'question_id': q.id,
                'question': q.question,
                'recall_at_k': recall_at_k(result.retrieved, expected, top_k),
                'precision_at_k': precision_at_k(result.retrieved, expected, top_k),
                'mrr': mrr(result.retrieved, expected),
                'ndcg_at_k': ndcg_at_k(result.retrieved, expected, top_k),
                'citation_coverage': 1.0 if citations else 0.0,
                'source_diversity': len({d['document_id'] for d in docs}),
                'retrieved_count': len(chunks),
            })
        avg = lambda key: sum(r[key] for r in rows)/max(len(rows),1)
        metrics = {
            'pipeline_id': pipeline_id,
            'question_count': len(rows),
            'recall_at_k': avg('recall_at_k'),
            'precision_at_k': avg('precision_at_k'),
            'mrr': avg('mrr'),
            'ndcg_at_k': avg('ndcg_at_k'),
            'citation_coverage': avg('citation_coverage'),
            'avg_source_diversity': avg('source_diversity'),
            'rows': rows,
        }
        run_id = str(uuid4())
        path = EvaluationReportGenerator().write(run_id, metrics)
        run = EvaluationRun(id=run_id, pipeline_id=pipeline_id, metrics_json=json.dumps(metrics), report_path=path)
        db.add(run); db.commit(); db.refresh(run)
        return run
