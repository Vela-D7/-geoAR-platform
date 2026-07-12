"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getJSON, Site } from "@/lib/api";

const statusColor: Record<string, string> = {
  ready: "text-emerald-400",
  building: "text-amber-300",
  degraded: "text-red-400",
  none: "text-slate-500",
};

export default function SitesPage() {
  const [sites, setSites] = useState<Site[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getJSON<Site[]>("sites").then(setSites).catch((e) => setError(String(e)));
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-semibold">Site registry</h1>
      {error && <p className="mt-4 rounded bg-red-900/40 p-3 text-sm text-red-300">{error}</p>}
      {!sites && !error && <p className="mt-4 text-sm text-slate-400">Loading…</p>}
      {sites && (
        <table className="mt-6 w-full text-left text-sm">
          <thead className="border-b border-slate-700 text-slate-400">
            <tr>
              <th className="py-2 pr-4">Site</th>
              <th className="py-2 pr-4">GPS anchor</th>
              <th className="py-2 pr-4">Recognition target</th>
              <th className="py-2 pr-4">Sessions</th>
              <th className="py-2 pr-4">Last result</th>
              <th className="py-2" />
            </tr>
          </thead>
          <tbody>
            {sites.map((s) => (
              <tr key={s.id} className="border-b border-slate-800/60">
                <td className="py-2 pr-4">
                  <div className="font-medium">{s.name}</div>
                  <div className="text-xs text-slate-500">{s.id}</div>
                </td>
                <td className="py-2 pr-4 font-mono text-xs text-slate-300">
                  {s.lat.toFixed(4)}, {s.lon.toFixed(4)}
                </td>
                <td className={`py-2 pr-4 ${statusColor[s.recognition_target_status] ?? ""}`}>
                  {s.recognition_target_status}
                </td>
                <td className="py-2 pr-4">{s.session_count}</td>
                <td className="py-2 pr-4">{s.last_outcome ?? "—"}</td>
                <td className="py-2">
                  <Link href={`/sites/${s.id}`} className="text-emerald-400 hover:underline">
                    detail / 3D →
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <p className="mt-4 text-xs text-slate-500">
        Session counts currently include synthetic seed data, labelled as such on the
        site detail page — field data replaces it as device sessions are ingested.
      </p>
    </div>
  );
}
