from app.rag.pipelines.vector_rag import VectorRAG
from app.rag.pipelines.bm25_rag import BM25RAG
from app.rag.pipelines.hybrid_rag import HybridRAG
from app.rag.pipelines.reranked_rag import RerankedHybridRAG
from app.rag.pipelines.parent_child_rag import ParentChildRAG
from app.rag.pipelines.section_aware_rag import SectionAwareMedicalRAG
from app.rag.pipelines.metadata_filtered_rag import MetadataFilteredRAG
from app.rag.pipelines.multi_query_rag import MultiQueryRAG
from app.rag.pipelines.rag_fusion import RAGFusion
from app.rag.pipelines.router_rag import RouterRAG
from app.rag.pipelines.evaluation_aware_rag import EvaluationAwareRAG
_PIPELINES={p.id:p for p in [VectorRAG(),BM25RAG(),HybridRAG(),RerankedHybridRAG(),ParentChildRAG(),SectionAwareMedicalRAG(),MetadataFilteredRAG(),MultiQueryRAG(),RAGFusion(),RouterRAG(),EvaluationAwareRAG()]}
def get_pipeline(pid):
    if pid not in _PIPELINES: raise KeyError(f'Pipeline not implemented: {pid}')
    return _PIPELINES[pid]
def list_pipelines():
    return [{'id':p.id,'name':p.name,'description':p.description,'implemented':True,'supports_reranking':getattr(p,'supports_reranking',False),'experimental':getattr(p,'experimental',False)} for p in _PIPELINES.values()]
