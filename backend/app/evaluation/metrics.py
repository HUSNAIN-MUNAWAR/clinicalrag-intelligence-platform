import math

def _ids(items):
    return [str(x.get('document_id') or x.get('chunk_id')) for x in items]

def _unique_in_order(vals):
    out=[]; seen=set()
    for v in vals:
        if v not in seen:
            out.append(v); seen.add(v)
    return out

def recall_at_k(retrieved: list[dict], expected_doc_ids: list[str], k: int) -> float:
    if not expected_doc_ids: return 0.0
    got = set(_ids(retrieved[:k])); exp = set(map(str, expected_doc_ids))
    return len(got & exp) / len(exp)

def precision_at_k(retrieved: list[dict], expected_doc_ids: list[str], k: int) -> float:
    if k <= 0: return 0.0
    got = _ids(retrieved[:k]); exp = set(map(str, expected_doc_ids))
    return sum(1 for x in got if x in exp) / k

def mrr(retrieved: list[dict], expected_doc_ids: list[str]) -> float:
    exp = set(map(str, expected_doc_ids)); seen=set()
    for i, x in enumerate(_ids(retrieved), 1):
        if x in seen: continue
        seen.add(x)
        if x in exp: return 1.0 / i
    return 0.0

def ndcg_at_k(retrieved: list[dict], expected_doc_ids: list[str], k: int) -> float:
    exp = set(map(str, expected_doc_ids)); used=set(); dcg = 0.0
    for i, x in enumerate(_ids(retrieved[:k]), 1):
        rel = 1.0 if x in exp and x not in used else 0.0
        used.add(x)
        dcg += rel / math.log2(i + 1)
    ideal_rels = [1.0] * min(len(exp), k)
    idcg = sum(rel / math.log2(i + 1) for i, rel in enumerate(ideal_rels, 1))
    return dcg / idcg if idcg else 0.0

def citation_coverage(answer: str, citation_count: int) -> float:
    return 1.0 if citation_count > 0 and '[C' in (answer or '') else 0.0
