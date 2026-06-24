from fastapi.testclient import TestClient
from app.main import app

def test_health_and_pipelines():
    c=TestClient(app)
    assert c.get('/health').status_code == 200
    r=c.get('/rag/pipelines')
    assert r.status_code == 200
    ids={p['id'] for p in r.json()}
    assert {'vector','bm25','hybrid','reranked_hybrid','parent_child','section_aware','metadata_filtered','multi_query','rag_fusion','router','evaluation_aware'} <= ids

def test_safety_route():
    c=TestClient(app)
    r=c.post('/safety/check', json={'text':'Should I go to hospital for chest pain?'})
    assert r.status_code == 200
    assert r.json()['allowed'] is False
