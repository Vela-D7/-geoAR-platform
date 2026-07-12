"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { api, getJSON, Site, Thresholds } from "@/lib/api";

const ModelViewer = dynamic(() => import("@/components/ModelViewer"), { ssr: false });

export default function SiteDetail({ params }: { params: { id: string } }) {
  const [site, setSite] = useState<Site | null>(null);
  const [thresholds, setThresholds] = useState<Thresholds | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getJSON<Site>(`sites/${params.id}`).then(setSite).catch((e) => setError(String(e)));
    getJSON<Thresholds>(`sites/${params.id}/thresholds`).then(setThresholds).catch(() => {});
  }, [params.id]);

  if (error) return <p className="rounded bg-red-900/40 p-3 text-sm text-red-300">{error}</p>;
  if (!site) return <p className="text-sm text-slate-400">Loading…</p>;

  return (
    <div>
      <h1 className="text-2xl font-semibold">{site.name}</h1>
      <p className="mt-1 font-mono text-xs text-slate-500">
        {site.id} · {site.lat.toFixed(5)}, {site.lon.toFixed(5)} · target: {site.recognition_target_status}
      </p>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <h2 className="mb-2 font-medium">Optimised model preview</h2>
          {site.model_asset_path ? (
            <>
              <ModelViewer url={api(`sites/${site.id}/model`)} />
              <p className="mt-1 text-xs text-amber-300/80">
                Current asset is the pipeline&apos;s placeholder mesh (LOD1) — the real
                Oystermouth LiDAR model replaces it through the same upload path.
              </p>
            </>
          ) : (
            <p className="rounded border border-slate-800 p-4 text-sm text-slate-400">
              No model asset yet — upload a scan first.
            </p>
          )}
        </div>

        <div>
          <h2 className="mb-2 font-medium">Fusion thresholds</h2>
          {thresholds ? (
            <dl className="space-y-2 rounded-lg border border-slate-800 bg-slate-900 p-4 text-sm">
              <div className="flex justify-between">
                <dt className="text-slate-400">version</dt>
                <dd>v{thresholds.version}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-400">visual_confidence_min</dt>
                <dd className="font-mono">{thresholds.visual_confidence_min}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-400">gps_accuracy_good_m</dt>
                <dd className="font-mono">{thresholds.gps_accuracy_good_m}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-400">last changed by</dt>
                <dd>{thresholds.changed_by}</dd>
              </div>
              <p className="border-t border-slate-800 pt-2 text-xs text-slate-500">{thresholds.reason}</p>
            </dl>
          ) : (
            <p className="text-sm text-slate-400">No threshold config.</p>
          )}

          <h2 className="mb-2 mt-6 font-medium">Field-test data</h2>
          <p className="rounded-lg border border-slate-800 bg-slate-900 p-4 text-sm text-slate-400">
            {site.session_count} logged sessions
            <span className="mt-1 block text-xs text-amber-300/80">
              currently synthetic seed data (labelled at ingest) — the field-test monitor
              page ships next and will filter by provenance
            </span>
          </p>
        </div>
      </div>
    </div>
  );
}
