from dataclasses import dataclass
from typing import Any
@dataclass
class PipelineResult: pipeline_id:str; retrieved:list[dict]; retrieval_scores:dict[str,Any]
class BaseRAGPipeline:
    id='base'; name='Base'; description='Base'; supports_reranking=False; experimental=False
    def retrieve(self,db,question,top_k=6,filters=None): raise NotImplementedError
