'use client';
import { useEffect, useState } from 'react';
import { apiGet, apiPost, endpoints } from '@/lib/api';

export default function Sources() {
  const [rows, setRows] = useState<any[]>([]);

  async function load() {
    setRows(await apiGet<any[]>(endpoints.sources).catch(() => []));
  }

  useEffect(() => {
    load();
  }, []);

  async function addDemo() {
    await apiPost(endpoints.sources, {
      name: 'Demo Medical Corpus',
      source_type: 'demo',
      license: 'CC BY / Public educational demo',
    });
    await load();
  }

  return (
    <div>
      <h1 className="text-3xl font-bold">Data Source Manager</h1>
      <button className="btn mt-6" onClick={addDemo}>Register demo source</button>
      <div className="card mt-6 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="p-3 text-left">Name</th>
              <th>Type</th>
              <th>License</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((s) => (
              <tr className="border-t" key={s.id}>
                <td className="p-3">{s.name}</td>
                <td>{s.source_type}</td>
                <td>{s.license_status}</td>
                <td>{s.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
