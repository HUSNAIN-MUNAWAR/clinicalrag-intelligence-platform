from pydantic import BaseModel, ConfigDict
class DocumentResponse(BaseModel):
    id:str; source_id:str; title:str; path:str|None=None; doc_type:str; license:str|None=None; year:int|None=None; topic:str|None=None; publication_type:str|None=None; medical_category:str|None=None; status:str
    model_config = ConfigDict(from_attributes=True)
DocumentOut = DocumentResponse
