import time
from uuid import uuid4
from sqlalchemy.orm import Session
from app.db.models import QuestionLog, SafetyRefusal
from app.rag.pipelines import get_pipeline, list_pipelines
from app.rag.pipelines.comparative_rag import ComparativeRAG
from app.rag.citation_builder import CitationBuilder
from app.rag.llm import LLMProvider
from app.safety.classifier import MedicalSafetyClassifier
from app.safety.refusals import safe_refusal
from app.schemas.common import LatencyBreakdown
from app.schemas.rag import RagAnswerResponse

class RAGService:
    def __init__(self):
        self.safety = MedicalSafetyClassifier()
        self.citations = CitationBuilder()
        self.llm = LLMProvider()

    def pipelines(self):
        return list_pipelines()

    def retrieve(self, db: Session, question: str, pipeline_id: str, top_k: int, filters: dict | None = None):
        return get_pipeline(pipeline_id).retrieve(db, question, top_k, filters or {})

    def ask(self, db: Session, question: str, pipeline_id='hybrid', top_k=6, filters=None, safety_mode=True, model_provider=None) -> RagAnswerResponse:
        t0 = time.perf_counter()
        decision = self.safety.check(question) if safety_mode else None
        if safety_mode and decision and not decision.allowed:
            answer = safe_refusal(question, decision)
            db.add(SafetyRefusal(id=str(uuid4()), question=question, category=decision.category or 'unknown', reason=decision.reason or 'refused'))
            db.add(QuestionLog(id=str(uuid4()), question=question, pipeline_used=pipeline_id, answer=answer, latency_ms=(time.perf_counter()-t0)*1000, citation_coverage=0, hallucination_risk='blocked', safety_status='refused'))
            db.commit()
            return RagAnswerResponse(answer=answer, evidence_summary='No retrieval performed because the request was unsafe.', citations=[], source_documents=[], retrieved_chunks=[], confidence_level='refused', limitations=['Educational system only; not for personal medical decisions.'], safety_status='refused', refusal_reason=decision.reason, latency_breakdown=LatencyBreakdown(total_ms=round((time.perf_counter()-t0)*1000,2)), pipeline_used=pipeline_id, model_used='none', retrieval_scores={})
        rt0 = time.perf_counter()
        result = self.retrieve(db, question, pipeline_id, top_k, filters or {})
        retrieval_ms = (time.perf_counter()-rt0)*1000
        citations, retrieved_chunks, source_docs = self.citations.build(result.retrieved)
        gt0 = time.perf_counter()
        answer = self.llm.generate_grounded_answer(question, result.retrieved, citations)
        generation_ms = (time.perf_counter()-gt0)*1000
        citation_coverage = 1.0 if citations and '[C' in answer else 0.0
        risk = 'low' if citation_coverage >= 0.8 and len(citations) >= 2 else 'medium' if citations else 'high'
        confidence = 'high' if risk == 'low' and len(retrieved_chunks) >= 3 else 'medium' if citations else 'low'
        total_ms = (time.perf_counter()-t0)*1000
        db.add(QuestionLog(id=str(uuid4()), question=question, pipeline_used=pipeline_id, answer=answer, latency_ms=total_ms, citation_coverage=citation_coverage, hallucination_risk=risk, safety_status='allowed'))
        db.commit()
        return RagAnswerResponse(
            answer=answer,
            evidence_summary=f'Retrieved {len(retrieved_chunks)} chunks from {len(source_docs)} source document(s). Hallucination risk estimate: {risk}.',
            citations=citations,
            source_documents=source_docs,
            retrieved_chunks=retrieved_chunks,
            confidence_level=confidence,
            limitations=['Educational/research use only.', 'Answers are limited to the indexed open corpus.', 'Not medical advice and not clinically validated.'],
            safety_status='allowed',
            refusal_reason=None,
            latency_breakdown=LatencyBreakdown(retrieval_ms=round(retrieval_ms,2), generation_ms=round(generation_ms,2), total_ms=round(total_ms,2)),
            pipeline_used=pipeline_id,
            model_used=self.llm.model_name,
            retrieval_scores=result.retrieval_scores,
        )

    def compare(self, db: Session, question: str, pipeline_ids: list[str], top_k=6):
        raw = ComparativeRAG().compare(db, question, pipeline_ids, top_k)
        comparisons = []
        for row in raw['comparisons']:
            citations, chunks, docs = self.citations.build(row['retrieved_chunks'])
            comparisons.append({**row, 'citation_count': len(citations), 'source_document_count': len(docs), 'hallucination_risk': 'low' if len(citations) >= 2 else 'medium' if citations else 'high'})
        return {'question': question, 'comparisons': comparisons}
