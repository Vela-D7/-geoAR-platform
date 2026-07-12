"use client";

import { useEffect, useMemo, useState } from "react";
import { getJSON } from "@/lib/api";
import TrendChart from "@/components/TrendChart";

type Session = {
  session_id: string;
  site_id: string;
  ended_at: string;
  gps_accuracy_m: number;
  visual_confidence: number;
  time_to_lock_s: number;
  drift_m: number;
  lighting: string;
  final_state: string | null;
  outcome: "success" | "degraded" | "failure";
  flags: string[];
  source: "field" | "synthetic" | "replay";
};

const outcomeStyle: Record<string, string> = {
  success: "bg-emerald-900/50 text-emerald-300",
  degraded: "bg-amber-900/50 text-amber-300",
  failure: "bg-red-900/50 text-red-300",
};

const SOURCES = ["all", "field", "synthetic", "replay"] as const;

export default function MonitorPage() {
  const [sessions, setSessions] = useState<Session[] | null>(null);
  const [source, setSource] = useState<(typeof SOURCES)[number]>("all");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getJSON<Session[]>("field-tests").then(setSessions).catch((e) => setError(String(e)));
  }, []);

  const filtered = useMemo(
    () => (sessions ?? []).filter((s) => source === "all" || s.source === source),
    [sessions, source]
  );
  const chronological = useMemo(
    () => [...filtered].sort((a, b) => a.ended_at.localeCompare(b.ended_at)),
    [filtered]
  );

  return (
    <div>
      <h1 className="text-2xl font-semibold">Field-test monitor</h1>
      <p className="mt-2 text-sm text-slate-400">
        Logged device sessions. Provenance is tracked per row —{" "}
        <span className="text-amber-300/90">no field sessions exist yet; current data is synthetic seed</span>.
      </p>

      {/* filter row above the charts */}
      <div className="mt-4 flex gap-2 text-sm">
        {SOURCES.map((s) => (
          <button
            key={s}
            onClick={() => setSource(s)}
            className={`rounded px-3 py-1 ${
              source === s ? "bg-slate-700 text-white" : "bg-slate-900 text-slate-400 hover:text-slate-200"
            }`}
          >
            {s}
          </button>
        ))}
        <span className="ml-auto self-center text-xs text-slate-500">{filtered.length} sessions</span>
      </div>

      {error && <p className="mt-4 rounded bg-red-900/40 p-3 text-sm text-red-300">{error}</p>}

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <TrendChart
          title="Time to lock per session"
          unit="s"
          points={chronological.map((s) => ({ label: s.ended_at.slice(0, 16), value: s.time_to_lock_s }))}
        />
        <TrendChart
          title="Anchor drift per session"
          unit="m"
          points={chronological.map((s) => ({ label: s.ended_at.slice(0, 16), value: s.drift_m }))}
        />
      </div>

      <div className="mt-6 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-700 text-slate-400">
            <tr>
              <th className="py-2 pr-3">Ended</th>
              <th className="py-2 pr-3">Outcome</th>
              <th className="py-2 pr-3">Final state</th>
              <th className="py-2 pr-3">GPS acc (m)</th>
              <th className="py-2 pr-3">Confidence</th>
              <th className="py-2 pr-3">Lock (s)</th>
              <th className="py-2 pr-3">Drift (m)</th>
              <th className="py-2 pr-3">Lighting</th>
              <th className="py-2 pr-3">Flags</th>
              <th className="py-2">Source</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((s) => (
              <tr key={s.session_id} className="border-b border-slate-800/60">
                <td className="py-1.5 pr-3 font-mono text-xs">{s.ended_at.slice(0, 16)}</td>
                <td className="py-1.5 pr-3">
                  <span className={`rounded px-2 py-0.5 text-xs ${outcomeStyle[s.outcome]}`}>{s.outcome}</span>
                </td>
                <td className="py-1.5 pr-3 font-mono text-xs">{s.final_state ?? "—"}</td>
                <td className="py-1.5 pr-3">{s.gps_accuracy_m}</td>
                <td className="py-1.5 pr-3">{s.visual_confidence}</td>
                <td className="py-1.5 pr-3">{s.time_to_lock_s}</td>
                <td className="py-1.5 pr-3">{s.drift_m}</td>
                <td className="py-1.5 pr-3">{s.lighting}</td>
                <td className="py-1.5 pr-3 text-xs text-slate-400">{s.flags.join(", ") || "—"}</td>
                <td className="py-1.5">
                  <span className={s.source === "field" ? "text-emerald-300" : "text-amber-300/90"}>{s.source}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
