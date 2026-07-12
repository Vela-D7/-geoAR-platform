"use client";

import { useState } from "react";
import { api, getJSON, Site, UploadResult } from "@/lib/api";
import { useEffect } from "react";

export default function UploadPage() {
  const [sites, setSites] = useState<Site[]>([]);
  const [siteId, setSiteId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getJSON<Site[]>("sites")
      .then((s) => {
        setSites(s);
        if (s.length) setSiteId(s[0].id);
      })
      .catch((e) => setError(String(e)));
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!file || !siteId) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const body = new FormData();
      body.append("file", file);
      const res = await fetch(api(`sites/${siteId}/scans`), { method: "POST", body });
      if (!res.ok) throw new Error(`${res.status}: ${(await res.json()).detail ?? "upload failed"}`);
      setResult(await res.json());
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-semibold">Upload LiDAR scan</h1>
      <p className="mt-2 text-sm text-slate-400">
        Accepted formats: .glb .gltf .ply .obj .stl (max 200 MB). The backend validates
        geometry before accepting: loadable mesh, building-scale extents. Coverage/density
        checks run in the processing pipeline after acceptance.
      </p>

      <form onSubmit={submit} className="mt-6 space-y-4">
        <label className="block text-sm">
          <span className="text-slate-300">Site</span>
          <select
            value={siteId}
            onChange={(e) => setSiteId(e.target.value)}
            className="mt-1 block w-full rounded border border-slate-700 bg-slate-900 p-2"
          >
            {sites.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.id})
              </option>
            ))}
          </select>
        </label>

        <label className="block text-sm">
          <span className="text-slate-300">Scan file</span>
          <input
            type="file"
            accept=".glb,.gltf,.ply,.obj,.stl"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="mt-1 block w-full text-sm file:mr-3 file:rounded file:border-0 file:bg-emerald-700 file:px-3 file:py-1.5 file:text-white"
          />
        </label>

        <button
          type="submit"
          disabled={!file || !siteId || busy}
          className="rounded bg-emerald-600 px-4 py-2 text-sm font-medium disabled:opacity-40"
        >
          {busy ? "Uploading + validating…" : "Upload"}
        </button>
      </form>

      {error && <p className="mt-4 rounded bg-red-900/40 p-3 text-sm text-red-300">{error}</p>}

      {result && (
        <div className="mt-6 rounded-lg border border-slate-800 bg-slate-900 p-4">
          <h2 className="font-medium">
            {result.filename} — {(result.size_bytes / 1e6).toFixed(1)} MB —{" "}
            {result.accepted ? (
              <span className="text-emerald-400">accepted</span>
            ) : (
              <span className="text-red-400">rejected</span>
            )}
          </h2>
          <ul className="mt-3 space-y-1 text-sm">
            {result.checks.map((c) => (
              <li key={c.name} className="flex gap-2">
                <span className={c.passed ? "text-emerald-400" : "text-red-400"}>
                  {c.passed ? "✓" : "✗"}
                </span>
                <span className="text-slate-300">{c.name}</span>
                <span className="text-slate-500">{c.detail}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
