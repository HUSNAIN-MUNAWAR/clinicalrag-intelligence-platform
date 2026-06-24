from app.safety.classifier import MedicalSafetyClassifier
from app.evaluation.metrics import precision_at_k, recall_at_k, mrr, ndcg_at_k
from app.rag.citation_builder import CitationBuilder

def test_safety_refuses_dosage():
    d=MedicalSafetyClassifier().check('What dosage of amoxicillin should I take?')
    assert not d.allowed
    assert d.category in {'prescription','drug_interaction'}

def test_metrics():
    items=[{'document_id':'a'},{'document_id':'b'}]
    assert recall_at_k(items,['a'],2) == 1
    assert precision_at_k(items,['a'],2) == 0.5
    assert mrr(items,['b']) == 0.5
    assert ndcg_at_k(items,['a'],2) > 0

def test_citation_builder():
    citations, chunks, docs = CitationBuilder().build([{'chunk_id':'c1','document_id':'d1','title':'T','source_name':'S','section':'abstract','text':'This is evidence text used for a citation.','score':0.9}])
    assert citations[0].citation_id == 'C1'
    assert chunks[0].chunk_id == 'c1'
    assert docs[0]['document_id'] == 'd1'
