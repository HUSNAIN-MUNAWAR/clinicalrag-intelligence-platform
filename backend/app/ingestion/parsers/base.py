from dataclasses import dataclass, field
from typing import Any
@dataclass
class ParsedDocument:
    text:str; title:str|None=None; metadata:dict[str,Any]=field(default_factory=dict); tables:list[dict[str,Any]]=field(default_factory=list); references:list[str]=field(default_factory=list)
class BaseParser:
    supported_extensions:tuple[str,...]=()
    def parse(self,path:str)->ParsedDocument: raise NotImplementedError
