from typing import Any
from pydantic import BaseModel, Field
class Citation(BaseModel):
    citation_id:str; document_id:str; chunk_id:str; title:str; source_name:str|None=None; section:str|None=None; quote:str; metadata:dict[str,Any]=Field(default_factory=dict)
class RetrievedChunk(BaseModel):
    chunk_id:str; document_id:str; parent_id:str|None=None; title:str|None=None; text:str; section:str|None=None; score:float; score_type:str='combined'; bm25_score:float|None=None; vector_score:float|None=None; reranker_score:float|None=None; reason:str|None=None; metadata:dict[str,Any]=Field(default_factory=dict)
class LatencyBreakdown(BaseModel):
    safety_ms:float=0; retrieval_ms:float=0; rerank_ms:float=0; generation_ms:float=0; total_ms:float=0
