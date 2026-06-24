'use client';
import {useState} from 'react';
import {apiPost,endpoints} from '@/lib/api';
export default function Inspector(){const [q,setQ]=useState('hypertension risk factors'); const [out,setOut]=useState<any>(null); async function run(){setOut(await apiPost('/rag/explain-retrieval',{question:q,pipeline_id:'hybrid',top_k:8}))} return <div><h1 className="text-3xl font-bold">Retrieval Inspector</h1><div className="card mt-6 p-6"><input className="input w-full" value={q} onChange={e=>setQ(e.target.value)}/><button className="btn mt-4" onClick={run}>Explain retrieval</button></div>{out&&<pre className="card mt-6 overflow-auto p-5 text-xs">{JSON.stringify(out,null,2)}</pre>}</div>}
