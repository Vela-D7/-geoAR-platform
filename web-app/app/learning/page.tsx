"use client";

import { useCallback, useEffect, useState } from "react";
import { api, getJSON, Site, Thresholds } from "@/lib/api";

type Report = {
  id: number;
  action: string;
  created_at: string;
  report: {
    reason: string;
    data_provenance: string[];
    evidence: { window: number; near_miss_but_fine: number; passed_but_bad: number };
    before: { threshold_version: number; visual_confidence_min: number; replayed_window_outcomes: Record<string, number> };
    after: { threshold_version: number; visual_confidence_min: number; replayed_window_outcomes: Record<string, number> };
  };
};

const actionStyle: Record<string, string> = {
  loosen: "bg-sky-900/50 text-sky-300",
  tighten: "bg-amber-900/50 text-amber-300",
  hold: "bg-slate-800 text-slate-400",
};

export default function LearningPage() {
  const [site, setSite] = useState<Site | null>(null);
  const [history, setHistory] = useState<Thresholds[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const sites = await getJSON<Site[]>("sites");
    if (!sites.length) return;
    setSite(sites[0]); // MVP: single site
    setHistory(await getJSON<Thresholds[]>(`sites/${sites[0].id}/thresholds/history`));
    setReports(await getJSON<Report[]>(`sites/${sites[0].id}/learning/reports`));
  }, []);

  useEffect(() => {
    refresh().catch((e) => setError(String(e)));
  }, [refresh]);

  async function runCycle() {
    if (!site) return;
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(api(`sites/${site.id}/learning/run`), { method: "POST" });
      if (!res.ok) throw new Error(`${res.status}: ${(await res.json()).detail}`);
      await refresh();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  const latest = reports[0];

  return (
    <div>
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-semibold">Self-learning panel</h1>
        <span className="rounded bg-slate-800 px-2 py-0.5 text-xs text-slate-400">
          v0 — rule-based, not a trained model
        </span>
      </div>
      <p className="mt-2 text-sm text-slate-400">
        Per-site confidence thresholds, the append-only history of automatic adjustments,
        and the before/after replay from each cycle.
      </p>

      {error && <p className="mt-4 rounded bg-red-900/40 p-3 text-sm text-red-300">{error}</p>}

      {site && (
        <div className="mt-6 flex items-center gap-4">
          <h2 className="font-medium">{site.name}</h2>
          <button
            onClick={runCycle}
            disabled={busy}
            className="ml-auto rounded bg-emerald-600 px-4 py-2 text-sm font-medium disabled:opacity-40"
          >
            {busy ? "Evaluating…" : "Run adjustment cycle now"}
          </button>
        </div>
      )}

      {latest && (
        <div className="mt-4 rounded-lg border border-slate-800 bg-slate-900 p-4">
          <div className="flex items-center gap-3">
            <span className={`rounded px-2 py-0.5 text-xs uppercase ${actionStyle[latest.action]}`}>
              {latest.action}
            </span>
            <span className="text-xs text-slate-500">{latest.created_at.slice(0, 19)}</span>
            <span className="ml-auto text-xs text-amber-300/80">
              data: {latest.report.data_provenance.join(", ")}
            </span>
          </div>
          <p className="mt-2 text-sm text-slate-300">{latest.report.reason}</p>
          <table className="mt-3 w-full max-w-lg text-left text-sm">
            <thead className="border-b border-slate-700 text-slate-400">
              <tr>
                <th className="py-1.5 pr-3" />
                <th className="py-1.5 pr-3">Before (v{latest.report.before.threshold_version})</th>
                <th className="py-1.5">After (v{latest.report.after.threshold_version})</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-slate-800/60">
                <td className="py-1.5 pr-3 text-slate-400">visual_confidence_min</td>
                <td className="py-1.5 pr-3 font-mono">{latest.report.before.visual_confidence_min}</td>
                <td className="py-1.5 font-mono">{latest.report.after.visual_confidence_min}</td>
              </tr>
              {Object.keys(latest.report.before.replayed_window_outcomes).map((k) => (
                <tr key={k} className="border-b border-slate-800/60">
                  <td className="py-1.5 pr-3 text-slate-400">{k.replaceAll("_", " ")} (replayed)</td>
                  <td className="py-1.5 pr-3 font-mono">{latest.report.before.replayed_window_outcomes[k]}</td>
                  <td className="py-1.5 font-mono">{latest.report.after.replayed_window_outcomes[k]}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-2 text-xs text-slate-500">
            "Replayed" re-applies the visual-lock rule to the same {latest.report.evidence.window} logged
            sessions under each cutoff — a replay of recorded data, not a prediction.
          </p>
        </div>
      )}

      <h2 className="mt-8 font-medium">Threshold version history</h2>
      <table className="mt-3 w-full text-left text-sm">
        <thead className="border-b border-slate-700 text-slate-400">
          <tr>
            <th className="py-1.5 pr-3">Version</th>
            <th className="py-1.5 pr-3">visual_confidence_min</th>
            <th className="py-1.5 pr-3">gps_accuracy_good_m</th>
            <th className="py-1.5 pr-3">Changed by</th>
            <th className="py-1.5">Reason</th>
          </tr>
        </thead>
        <tbody>
          {[...history].reverse().map((h) => (
            <tr key={h.version} className="border-b border-slate-800/60">
              <td className="py-1.5 pr-3">v{h.version}</td>
              <td className="py-1.5 pr-3 font-mono">{h.visual_confidence_min}</td>
              <td className="py-1.5 pr-3 font-mono">{h.gps_accuracy_good_m}</td>
              <td className="py-1.5 pr-3">{h.changed_by}</td>
              <td className="py-1.5 text-xs text-slate-400">{h.reason}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2 className="mt-8 font-medium">Cycle history</h2>
      <table className="mt-3 w-full max-w-2xl text-left text-sm">
        <thead className="border-b border-slate-700 text-slate-400">
          <tr>
            <th className="py-1.5 pr-3">When</th>
            <th className="py-1.5 pr-3">Action</th>
            <th className="py-1.5 pr-3">Cutoff</th>
            <th className="py-1.5">Evidence (window / near-miss / passed-bad)</th>
          </tr>
        </thead>
        <tbody>
          {reports.map((r) => (
            <tr key={r.id} className="border-b border-slate-800/60">
              <td className="py-1.5 pr-3 font-mono text-xs">{r.created_at.slice(0, 19)}</td>
              <td className="py-1.5 pr-3">
                <span className={`rounded px-2 py-0.5 text-xs uppercase ${actionStyle[r.action]}`}>{r.action}</span>
              </td>
              <td className="py-1.5 pr-3 font-mono text-xs">
                {r.report.before.visual_confidence_min} → {r.report.after.visual_confidence_min}
              </td>
              <td className="py-1.5 font-mono text-xs">
                {r.report.evidence.window} / {r.report.evidence.near_miss_but_fine} / {r.report.evidence.passed_but_bad}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
