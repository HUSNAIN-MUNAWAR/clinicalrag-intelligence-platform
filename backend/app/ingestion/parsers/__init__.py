from pathlib import Path
from app.core.exceptions import UnsupportedParserError
from app.ingestion.parsers.txt_parser import TxtParser
from app.ingestion.parsers.pdf_parser import PdfParser
from app.ingestion.parsers.xml_parser import XmlParser
from app.ingestion.parsers.json_parser import JsonParser
from app.ingestion.parsers.html_parser import HtmlParser
PARSERS=[TxtParser(),PdfParser(),XmlParser(),JsonParser(),HtmlParser()]
def get_parser(path):
    ext=Path(path).suffix.lower()
    for p in PARSERS:
        if ext in p.supported_extensions: return p
    raise UnsupportedParserError(f'Unsupported file extension: {ext}')
