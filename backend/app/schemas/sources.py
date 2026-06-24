from pydantic import BaseModel, ConfigDict
class SourceCreate(BaseModel):
    name:str='Demo Medical Corpus'; source_type:str='demo'; url:str|None=None; license:str|None='CC BY / Public educational demo'; raw_path:str|None=None
class SourceResponse(BaseModel):
    id:str; name:str; source_type:str; url:str|None=None; license:str|None=None; license_status:str|None=None; raw_path:str|None=None; status:str
    model_config = ConfigDict(from_attributes=True)
SourceOut = SourceResponse
class LicenseValidationRequest(BaseModel): license:str|None=None; url:str|None=None
class LicenseValidationResponse(BaseModel): status:str; reason:str; allowed:bool; notes:list[str]=[]
