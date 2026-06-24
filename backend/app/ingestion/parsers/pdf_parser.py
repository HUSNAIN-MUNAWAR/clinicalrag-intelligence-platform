from app.ingestion.metadata import guess_title
from app.ingestion.parsers.base import BaseParser, ParsedDocument
class PdfParser(BaseParser):
    supported_extensions=('.pdf',)
    def parse(self,path):
        from pypdf import PdfReader
        reader=PdfReader(path); parts=[]
        for i,p in enumerate(reader.pages): parts.append(f'\n\n[Page {i+1}]\n'+(p.extract_text() or ''))
        text=''.join(parts); return ParsedDocument(text=text,title=guess_title(text,path),metadata={'parser':'pdf','page_count':len(reader.pages)})
