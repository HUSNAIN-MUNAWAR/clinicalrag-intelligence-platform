from dataclasses import dataclass
from pathlib import Path
@dataclass
class SourceDownloadResult: source_name:str; target_dir:Path; files:list[Path]; license:str; notes:str
class SourceAdapter:
    id='base'; name='Base'
    def download(self,target_dir:Path,limit:int=5)->SourceDownloadResult: raise NotImplementedError
