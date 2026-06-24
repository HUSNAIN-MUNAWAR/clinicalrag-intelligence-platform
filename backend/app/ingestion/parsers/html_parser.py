from pathlib import Path
from app.ingestion.metadata import guess_title
from app.ingestion.parsers.base import BaseParser, ParsedDocument
class HtmlParser(BaseParser):
    supported_extensions=('.html','.htm')
    def parse(self,path):
        raw=Path(path).read_text(encoding='utf-8', errors='ignore')
        try:
            from bs4 import BeautifulSoup
            soup=BeautifulSoup(raw,'html.parser')
            for t in soup(['script','style','nav','footer']): t.decompose()
            title=soup.title.string.strip() if soup.title and soup.title.string else None; text=soup.get_text('\n')
        except Exception: title=None; text=raw
        return ParsedDocument(text=text,title=title or guess_title(text,path),metadata={'parser':'html'})
