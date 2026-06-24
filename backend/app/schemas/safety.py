from pydantic import BaseModel
class SafetyCheckRequest(BaseModel): text:str|None=None; question:str|None=None
class SafetyCheckResponse(BaseModel): allowed:bool; category:str|None=None; severity:str='low'; reason:str|None=None; matched_patterns:list[str]=[]
