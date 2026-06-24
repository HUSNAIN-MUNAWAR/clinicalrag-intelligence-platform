from pathlib import Path
import xml.etree.ElementTree as ET
from app.ingestion.metadata import guess_title
from app.ingestion.parsers.base import BaseParser, ParsedDocument
class XmlParser(BaseParser):
    supported_extensions=('.xml',)
    def parse(self,path):
        raw=Path(path).read_text(encoding='utf-8', errors='ignore'); root=ET.fromstring(raw); parts=[]; refs=[]; title=None
        for e in root.iter():
            tag=e.tag.split('}')[-1].lower(); text=(e.text or '').strip()
            if not text: continue
            if tag in {'title','full-summary','group-name'} and not title: title=text[:180]
            if tag in {'reference','citation','url'}: refs.append(text)
            parts.append(f'{tag}: {text}')
        full='\n'.join(parts) or raw
        return ParsedDocument(text=full,title=title or guess_title(full,path),metadata={'parser':'xml'},references=refs)
