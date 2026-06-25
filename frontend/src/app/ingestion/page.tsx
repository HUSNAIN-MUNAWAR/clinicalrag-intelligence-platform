'use client';
import { useEffect, useState } from 'react';
import { apiGet, apiPost, endpoints } from '@/lib/api';

export default function Ingestion() {
  const [jobs, setJobs] = useState<any[]>([]);

  async function load() {
    setJobs(await apiGet<any[]>(endpoints.ingestionJobs).catch(() => []));
  }

  useEffect(() => {
    load();
  }, []);

  async function start() {
    await apiPost(endpoints.ingestionStart, {});
    await load();
  }

  return (
    <div>
      <h1 className="text-3xl font-bold">Ingestion Monitor</h1>
      <button className="btn mt-6" onClick={start}>Ingest demo corpus</button>
      <div className="mt-6 space-y-3">
        {jobs.map((j) => (
          <div key={j.id} className="card p-4">
            <b>{j.status}</b>
            <div className="text-sm text-slate-500">
              {j.processed_files}/{j.total_files} processed - failed {j.failed_files}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
