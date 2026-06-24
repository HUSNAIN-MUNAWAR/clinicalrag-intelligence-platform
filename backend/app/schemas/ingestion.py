from pydantic import BaseModel, ConfigDict
class IngestionStartRequest(BaseModel): source_id:str|None=None; path:str|None=None; rebuild_indexes:bool=True
class IngestionJobResponse(BaseModel):
    id:str; source_id:str|None=None; status:str; current_file:str|None=None; total_files:int; processed_files:int; failed_files:int
    model_config = ConfigDict(from_attributes=True)
IngestionJobOut = IngestionJobResponse
