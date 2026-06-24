'use client';
import {useState} from 'react';
import {apiPost,endpoints} from '@/lib/api';
export default function Safety(){const [text,setText]=useState('Should I go to hospital for chest pain?'); const [out,setOut]=useState<any>(null); async function run(){setOut(await apiPost(endpoints.safetyCheck,{text}))} return <div><h1 className="text-3xl font-bold">Safety Center</h1><div className="card mt-6 p-6"><input className="input w-full" value={text} onChange={e=>setText(e.target.value)}/><button className="btn mt-4" onClick={run}>Check safety</button></div>{out&&<pre className="card mt-6 p-5 text-xs">{JSON.stringify(out,null,2)}</pre>}</div>}
