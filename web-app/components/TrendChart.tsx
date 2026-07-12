"use client";

import { useMemo, useState } from "react";

/** Single-series trend line (small-multiple form): thin 2px line, ≥8px hover
 *  targets, per-point tooltip, recessive grid, one axis. Series color is the
 *  validated dark-mode categorical slot-1 (#3987e5) — passes lightness band,
 *  chroma floor and 3:1 contrast on this surface (see dataviz validator). A
 *  single series needs no legend: the title names it. */
export default function TrendChart({
  title,
  unit,
  points,
}: {
  title: string;
  unit: string;
  points: { label: string; value: number }[];
}) {
  const [hover, setHover] = useState<number | null>(null);

  const W = 420, H = 140, PAD = { l: 40, r: 10, t: 10, b: 20 };
  const iw = W - PAD.l - PAD.r, ih = H - PAD.t - PAD.b;

  const { xs, ys, max, ticks } = useMemo(() => {
    const max = Math.max(...points.map((p) => p.value), 0.001);
    const nice = max <= 1 ? Math.ceil(max * 10) / 10 : Math.ceil(max);
    const xs = points.map((_, i) => PAD.l + (points.length === 1 ? iw / 2 : (i * iw) / (points.length - 1)));
    const ys = points.map((p) => PAD.t + ih - (p.value / nice) * ih);
    const ticks = [0, nice / 2, nice];
    return { xs, ys, max: nice, ticks };
  }, [points, iw, ih, PAD.l, PAD.t]);

  if (points.length === 0)
    return (
      <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
        <h3 className="text-sm font-medium text-slate-300">{title}</h3>
        <p className="mt-4 text-xs text-slate-500">No sessions match the current filter.</p>
      </div>
    );

  const path = xs.map((x, i) => `${i === 0 ? "M" : "L"}${x},${ys[i]}`).join(" ");

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
      <h3 className="text-sm font-medium text-slate-300">
        {title} <span className="text-xs font-normal text-slate-500">({unit})</span>
      </h3>
      <svg viewBox={`0 0 ${W} ${H}`} className="mt-2 w-full" role="img" aria-label={title}>
        {ticks.map((t) => {
          const y = PAD.t + ih - (t / max) * ih;
          return (
            <g key={t}>
              <line x1={PAD.l} x2={W - PAD.r} y1={y} y2={y} stroke="#1e293b" strokeWidth="1" />
              <text x={PAD.l - 6} y={y + 3} textAnchor="end" fontSize="9" fill="#64748b">
                {t}
              </text>
            </g>
          );
        })}
        <path d={path} fill="none" stroke="#3987e5" strokeWidth="2" strokeLinejoin="round" />
        {xs.map((x, i) => (
          <g key={i}>
            {/* hit target bigger than the mark */}
            <circle
              cx={x} cy={ys[i]} r="10" fill="transparent"
              onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}
            />
            <circle cx={x} cy={ys[i]} r={hover === i ? 4 : 2.5} fill="#3987e5" stroke="#0f172a" strokeWidth="2" pointerEvents="none" />
          </g>
        ))}
        {hover !== null && (
          <g pointerEvents="none">
            <line x1={xs[hover]} x2={xs[hover]} y1={PAD.t} y2={PAD.t + ih} stroke="#334155" strokeWidth="1" />
            <rect
              x={Math.min(xs[hover] + 8, W - 130)} y={Math.max(ys[hover] - 30, 2)}
              width="122" height="26" rx="4" fill="#1e293b" stroke="#334155"
            />
            <text x={Math.min(xs[hover] + 14, W - 124)} y={Math.max(ys[hover] - 30, 2) + 11} fontSize="9" fill="#94a3b8">
              {points[hover].label}
            </text>
            <text x={Math.min(xs[hover] + 14, W - 124)} y={Math.max(ys[hover] - 30, 2) + 21} fontSize="10" fill="#f1f5f9">
              {points[hover].value} {unit}
            </text>
          </g>
        )}
      </svg>
    </div>
  );
}
