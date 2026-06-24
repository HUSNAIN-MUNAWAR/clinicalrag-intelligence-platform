from pathlib import Path
from app.ingestion.metadata import guess_title
from app.ingestion.parsers.base import BaseParser, ParsedDocument
class TxtParser(BaseParser):
    supported_extensions=('.txt','.md')
    def parse(self,path):
        text=Path(path).read_text(encoding='utf-8', errors='ignore')
        return ParsedDocument(text=text,title=guess_title(text,path),metadata={'parser':'txt'})
