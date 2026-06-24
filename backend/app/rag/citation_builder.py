from app.schemas.common import Citation, RetrievedChunk
class CitationBuilder:
    def build(self, retrieved, max_citations=6):
        cites=[]; chunks=[]; docs=[]; seen_chunks=set(); seen_docs=set()
        for item in retrieved:
            if item.get('chunk_id') in seen_chunks: continue
            seen_chunks.add(item.get('chunk_id'))
            quote=' '.join((item.get('text') or '').split())[:420]
            cid=f'C{len(cites)+1}'
            cites.append(Citation(citation_id=cid,document_id=item.get('document_id',''),chunk_id=item.get('chunk_id',''),title=item.get('title','Untitled'),source_name=item.get('source_name'),section=item.get('section'),quote=quote,metadata=item.get('metadata',{})))
            chunks.append(RetrievedChunk(chunk_id=item.get('chunk_id',''),document_id=item.get('document_id',''),parent_id=item.get('parent_id'),title=item.get('title'),text=item.get('text',''),section=item.get('section'),score=float(item.get('score',0) or 0),score_type=item.get('score_type','combined'),bm25_score=item.get('bm25_score'),vector_score=item.get('vector_score'),reranker_score=item.get('reranker_score'),reason=item.get('reason'),metadata=item.get('metadata',{})))
            did=item.get('document_id','')
            if did and did not in seen_docs:
                seen_docs.add(did); docs.append({'document_id':did,'title':item.get('title','Untitled'),'source_name':item.get('source_name'),'metadata':item.get('metadata',{})})
            if len(cites)>=max_citations: break
        return cites, chunks, docs
    def evidence_text(self, retrieved, max_citations=6):
        citations, _, _ = self.build(retrieved, max_citations)
        return '\n'.join(f'[{c.citation_id}] {c.title} / {c.section}: {c.quote}' for c in citations)
    def citation_coverage(self, answer, citations):
        return sum(1 for c in citations if f'[{c.citation_id}]' in answer)/max(len(citations),1) if answer.strip() else 0
