'use client';
import {useState} from 'react';
import {apiPost,endpoints} from '@/lib/api';
export default function Evaluation(){const [out,setOut]=useState<any>(null); async function run(){setOut(await apiPost(endpoints.evalRun,{pipeline_id:'hybrid',top_k:5}))} return <div><h1 className="text-3xl font-bold">Evaluation Lab</h1><button className="btn mt-6" onClick={run}>Run demo evaluation</button>{out&&<pre className="card mt-6 overflow-auto p-5 text-xs">{JSON.stringify(out,null,2)}</pre>}</div>}
