from typing import Any
from pydantic import BaseModel, Field
from app.schemas.common import Citation, RetrievedChunk, LatencyBreakdown
class RagAskRequest(BaseModel): question:str; pipeline_id:str='hybrid'; top_k:int=6; rerank:bool=False; safety_mode:bool=True; filters:dict[str,Any]=Field(default_factory=dict); model_provider:str|None=None
class RagRetrieveRequest(BaseModel): question:str; pipeline_id:str='hybrid'; top_k:int=6; filters:dict[str,Any]=Field(default_factory=dict)
class RagCompareRequest(BaseModel): question:str; pipeline_ids:list[str]=Field(default_factory=lambda:['vector','bm25','hybrid','reranked_hybrid']); top_k:int=6; safety_mode:bool=True
class RagAnswerResponse(BaseModel):
    answer:str; evidence_summary:str; citations:list[Citation]; source_documents:list[dict[str,Any]]; retrieved_chunks:list[RetrievedChunk]; confidence_level:str; limitations:list[str]; safety_status:str; refusal_reason:str|None=None; latency_breakdown:LatencyBreakdown; pipeline_used:str; model_used:str; retrieval_scores:dict[str,Any]
