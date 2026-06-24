from pathlib import Path
from app.ingestion.parsers.txt_parser import TxtParser
from app.ingestion.parsers.xml_parser import XmlParser
from app.ingestion.chunkers.medical_chunker import MedicalChunker, MedicalSectionDetector

def test_txt_parser(tmp_path: Path):
    p=tmp_path/'doc.txt'; p.write_text('Hypertension Overview\nSymptoms\nMany people have no symptoms.', encoding='utf-8')
    doc=TxtParser().parse(p)
    assert 'Hypertension' in doc.title

def test_xml_parser(tmp_path: Path):
    p=tmp_path/'doc.xml'; p.write_text('<root><title>Asthma</title><summary>Airway disease</summary></root>', encoding='utf-8')
    doc=XmlParser().parse(p)
    assert doc.title == 'Asthma'

def test_medical_section_detector_and_chunker():
    text='Asthma Overview\nSymptoms\nWheezing and cough.\nTreatment\nClinician guided treatment.'
    sections=MedicalSectionDetector().split_sections(text)
    assert sections
    result=MedicalChunker(chunk_size=60, overlap=10).chunk(text,'d1')
    assert result.parents and result.children
