import hashlib, re
from pathlib import Path
SECTIONS={'abstract':['abstract','summary','overview'],'symptoms':['symptoms','signs and symptoms'],'causes':['causes','etiology'],'risk_factors':['risk factors','risks'],'diagnosis':['diagnosis','diagnostic','testing','tests'],'treatment':['treatment','management','therapy'],'prevention':['prevention'],'contraindications':['contraindications'],'warnings':['warnings','adverse effects','side effects','precautions'],'methods':['methods'],'results':['results','findings'],'conclusion':['conclusion'],'references':['references']}
def sha256_text(text): return hashlib.sha256(text.encode('utf-8','ignore')).hexdigest()
def guess_title(text,path=None):
    for line in text.splitlines():
        s=line.strip(' #\t')
        if 5<=len(s)<=180: return s
    return Path(path).stem if path else 'Untitled document'
def detect_section(text):
    s=re.sub(r'[^a-z0-9 ]+',' ',text.lower()[:180])
    for k,vals in SECTIONS.items():
        if any(v in s for v in vals): return k
    return 'body'
def extract_year(text):
    m=re.search(r'\b(19\d{2}|20\d{2})\b', text); return int(m.group(1)) if m else None
def classify_medical_category(text):
    s=text.lower()
    if any(x in s for x in ['contraindication','adverse','dosage','drug']): return 'medication_or_safety'
    if any(x in s for x in ['symptom','diagnosis','treatment','prevention']): return 'health_topic'
    if any(x in s for x in ['methods','results','trial','cohort']): return 'biomedical_article'
    return 'general_medical'

def enrich_metadata(metadata: dict) -> dict:
    metadata = dict(metadata or {})
    text = (metadata.get('text') or metadata.get('title') or metadata.get('path') or '')
    path = metadata.get('path')
    if not metadata.get('title') and text:
        metadata['title'] = guess_title(str(text), path)
    if not metadata.get('year'):
        metadata['year'] = extract_year(str(text))
    if not metadata.get('medical_category'):
        metadata['medical_category'] = classify_medical_category(str(text))
    if not metadata.get('publication_type'):
        metadata['publication_type'] = 'health_topic' if metadata.get('medical_category') == 'health_topic' else 'article_or_document'
    if not metadata.get('topic'):
        metadata['topic'] = metadata.get('title') or 'general medical'
    base = (str(metadata.get('title','')) + str(metadata.get('path','')) + str(metadata.get('license','')))
    metadata['sha256'] = metadata.get('sha256') or sha256_text(base)
    return metadata
