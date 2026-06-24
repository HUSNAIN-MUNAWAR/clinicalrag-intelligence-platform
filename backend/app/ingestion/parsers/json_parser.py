from pathlib import Path
import json
from app.ingestion.metadata import guess_title
from app.ingestion.parsers.base import BaseParser, ParsedDocument
class JsonParser(BaseParser):
    supported_extensions=('.json',)
    def parse(self,path):
        data=json.loads(Path(path).read_text(encoding='utf-8', errors='ignore')); title=data.get('title') if isinstance(data,dict) else None
        text='\n'.join(str(v) for v in data.values()) if isinstance(data,dict) else json.dumps(data)
        return ParsedDocument(text=text,title=title or guess_title(text,path),metadata={'parser':'json'})
