from pydantic import BaseModel, Field
class EvaluationQuestionCreate(BaseModel): question:str; expected_doc_ids:list[str]=Field(default_factory=list); answer_key:str|None=None; tags:list[str]=Field(default_factory=list)
class EvaluationRunRequest(BaseModel): pipeline_id:str='hybrid'; top_k:int=6; question_ids:list[str]|None=None
class EvaluationRunOut(BaseModel): id:str; pipeline_id:str; metrics:dict; report_path:str|None=None
