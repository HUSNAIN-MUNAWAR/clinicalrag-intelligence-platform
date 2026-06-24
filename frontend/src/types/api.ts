export type Pipeline = { id:string; name:string; description:string; implemented:boolean; supports_reranking:boolean; experimental:boolean };
export type Citation = { citation_id:string; document_id:string; chunk_id:string; title:string; source_name?:string; section?:string; quote:string };
export type RagAnswer = { answer:string; evidence_summary:string; citations:Citation[]; confidence_level:string; safety_status:string; refusal_reason?:string; latency_breakdown:Record<string,number>; pipeline_used:string; model_used:string; retrieved_chunks:any[]; retrieval_scores:Record<string,unknown> };
