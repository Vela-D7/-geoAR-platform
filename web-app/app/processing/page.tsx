"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getJSON, Site } from "@/lib/api";

type Job = {
  id: number;
  site_id: string;
  status: "queued" | "running" | "succeeded" | "failed";
  attempt: number;
  settings_profile: string;
  steps: { name: string; status: string; detail: string }[];
  error: string | null;
  recommendation: string | null;
  created_at: string | null;
};

const stepStyle: Record<string, string> = {
  passed: "bg-emerald-900/50 text-emerald-300",
  running: "bg-sky-900/50 text-sky-300",
  failed: "bg-red-900/50 text-red-300",
  stub: "bg-amber-900/50 text-amber-300",
};

const jobStyle: Record<string, string> = {
  succeeded: "text-emerald-400",
  failed: "text-red-400",
  running: "text-sky-300",
  queued: "text-slate-400",
};

const PIPELINE_STEPS = ["mesh_cleanup", "lod_generation", "texture_bake", "recognition_target"];

export default function ProcessingPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [error, setError] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  const refresh = useCallback(async () => {
    const sites = await getJSON<Site[]>("sites");
    const all: Job[] = [];
    for (const s of sites) all.push(...(await getJSON<Job[]>(`sites/${s.id}/jobs`)));
    all.sort((a, b) => b.id - a.id);
    setJobs(all);
    return all;
  }, []);

  useEffect(() => {
    refresh().catch((e) => setError(String(e)));
    // Poll while anything is in flight; the interval self-cancels when idle.
    timer.current = setInterval(async () => {
      try {
        const all = await refresh();
        if (!all.some((j) => j.status === "queued" || j.status === "running") && timer.current) {
          clearInterval(timer.current);
          timer.current = null;
        }
      } catch {
        /* transient poll errors are non-fatal */
      }
    }, 2000);
    return () => {
      if (timer.current) clearInterval(timer.current);
    };
  }, [refresh]);

  return (
    <div>
      <h1 className="text-2xl font-semibold">Processing status</h1>
      <p className="mt-2 text-sm text-slate-400">
        Optimisation pipeline runs: mesh cleanup → LOD generation → texture bake →
        recognition target, with pass/fail per step. Failed runs retry once with a
        conservative settings profile before reporting a capture recommendation.
      </p>

      {error && <p className="mt-4 rounded bg-red-900/40 p-3 text-sm text-red-300">{error}</p>}
      {jobs.length === 0 && !error && (
        <p className="mt-6 rounded border border-slate-800 p-4 text-sm text-slate-400">
          No processing jobs yet — upload a scan to start one.
        </p>
      )}

      {jobs.map((job) => (
        <div key={job.id} className="mt-4 rounded-lg border border-slate-800 bg-slate-900 p-4">
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <span className="font-medium">Job #{job.id}</span>
            <span className="text-slate-500">{job.site_id}</span>
            <span className={`font-medium ${jobStyle[job.status]}`}>{job.status}</span>
            <span className="text-xs text-slate-500">
              attempt {job.attempt} · profile: {job.settings_profile}
            </span>
            <span className="ml-auto font-mono text-xs text-slate-500">
              {job.created_at?.slice(0, 19)}
            </span>
          </div>

          <div className="mt-3 flex flex-wrap gap-2">
            {PIPELINE_STEPS.map((name) => {
              const step = job.steps.find((s) => s.name === name);
              const status = step?.status ?? "pending";
              return (
                <div key={name} className="flex items-center gap-2 rounded border border-slate-800 px-3 py-1.5">
                  <span className={`rounded px-1.5 py-0.5 text-xs ${stepStyle[status] ?? "bg-slate-800 text-slate-500"}`}>
                    {status}
                  </span>
                  <span className="text-xs text-slate-300">{name.replaceAll("_", " ")}</span>
                  {step?.detail && <span className="max-w-56 truncate text-xs text-slate-500" title={step.detail}>{step.detail}</span>}
                </div>
              );
            })}
          </div>

          {job.error && <p className="mt-3 rounded bg-red-950/50 p-2 text-xs text-red-300">{job.error}</p>}
          {job.recommendation && (
            <p className="mt-2 rounded bg-amber-950/40 p-2 text-xs text-amber-200">{job.recommendation}</p>
          )}
        </div>
      ))}
    </div>
  );
}
