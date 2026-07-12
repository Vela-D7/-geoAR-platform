"use client";

import { useCallback, useEffect, useState } from "react";
import { api, getJSON, Site } from "@/lib/api";

type Deploy = {
  id: number;
  site_id: string;
  bundle_path: string;
  manifest: { lods: { tier: number; faces: number }[]; profile: string; recognition_target: string };
  status: string;
  created_at: string;
};

export default function DeployPage() {
  const [sites, setSites] = useState<Site[]>([]);
  const [deploys, setDeploys] = useState<Record<string, Deploy[]>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [needsConfirm, setNeedsConfirm] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const s = await getJSON<Site[]>("sites");
    setSites(s);
    const d: Record<string, Deploy[]> = {};
    for (const site of s) d[site.id] = await getJSON<Deploy[]>(`sites/${site.id}/deploys`);
    setDeploys(d);
  }, []);

  useEffect(() => {
    refresh().catch((e) => setError(String(e)));
  }, [refresh]);

  async function trigger(siteId: string, confirmLive: boolean) {
    setBusy(siteId);
    setError(null);
    try {
      const res = await fetch(api(`sites/${siteId}/deploy`), {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ confirm_live_site: confirmLive }),
      });
      if (res.status === 409) {
        const detail = (await res.json()).detail as string;
        if (detail.includes("LIVE anchor")) {
          setNeedsConfirm(siteId); // surface the approval gate, don't bypass it
          return;
        }
        throw new Error(detail);
      }
      if (!res.ok) throw new Error(`${res.status}: ${(await res.json()).detail}`);
      setNeedsConfirm(null);
      await refresh();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold">Deploy</h1>
      <p className="mt-2 text-sm text-slate-400">
        Stages a versioned bundle (processed LODs + manifest) for the Unity/XREAL build.
        The recognition target is still a declared stub pending the fine-lock vendor decision.
      </p>

      {error && <p className="mt-4 rounded bg-red-900/40 p-3 text-sm text-red-300">{error}</p>}

      {sites.map((site) => (
        <div key={site.id} className="mt-6 rounded-lg border border-slate-800 bg-slate-900 p-4">
          <div className="flex items-center gap-4">
            <div>
              <h2 className="font-medium">{site.name}</h2>
              <p className="text-xs text-slate-500">
                target: {site.recognition_target_status} · {deploys[site.id]?.length ?? 0} deploys
              </p>
            </div>
            <button
              onClick={() => trigger(site.id, false)}
              disabled={busy === site.id}
              className="ml-auto rounded bg-emerald-600 px-4 py-2 text-sm font-medium disabled:opacity-40"
            >
              {busy === site.id ? "Staging…" : "Deploy latest processed model"}
            </button>
          </div>

          {needsConfirm === site.id && (
            <div className="mt-3 rounded border border-amber-700 bg-amber-950/40 p-3 text-sm">
              <p className="text-amber-200">
                This site has a <strong>live anchor</strong> — deploying replaces the content
                rendered under it. Explicit approval required (security check).
              </p>
              <div className="mt-2 flex gap-2">
                <button
                  onClick={() => trigger(site.id, true)}
                  className="rounded bg-amber-600 px-3 py-1.5 text-xs font-medium text-black"
                >
                  Confirm deploy to live site
                </button>
                <button
                  onClick={() => setNeedsConfirm(null)}
                  className="rounded bg-slate-700 px-3 py-1.5 text-xs"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {(deploys[site.id] ?? []).length > 0 && (
            <table className="mt-4 w-full text-left text-sm">
              <thead className="border-b border-slate-700 text-slate-400">
                <tr>
                  <th className="py-1.5 pr-3">#</th>
                  <th className="py-1.5 pr-3">Created</th>
                  <th className="py-1.5 pr-3">Bundle</th>
                  <th className="py-1.5 pr-3">Profile</th>
                  <th className="py-1.5 pr-3">LOD faces</th>
                  <th className="py-1.5">Status</th>
                </tr>
              </thead>
              <tbody>
                {deploys[site.id].map((d) => (
                  <tr key={d.id} className="border-b border-slate-800/60">
                    <td className="py-1.5 pr-3">{d.id}</td>
                    <td className="py-1.5 pr-3 font-mono text-xs">{d.created_at.slice(0, 19)}</td>
                    <td className="py-1.5 pr-3 font-mono text-xs">{d.bundle_path.split("/").pop()}</td>
                    <td className="py-1.5 pr-3">{d.manifest.profile}</td>
                    <td className="py-1.5 pr-3 font-mono text-xs">
                      {d.manifest.lods.map((l) => l.faces).join(" / ")}
                    </td>
                    <td className="py-1.5">{d.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      ))}
    </div>
  );
}
