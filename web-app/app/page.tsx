import Link from "next/link";

const cards = [
  { href: "/upload", title: "Upload", desc: "LiDAR scan upload with validation; auto-enqueues processing", live: true },
  { href: "/processing", title: "Processing status", desc: "Pipeline runs with pass/fail per step and retry-with-fallback", live: true },
  { href: "/sites", title: "Site registry", desc: "Registered sites, GPS anchors, target status, last field-test result", live: true },
  { href: "/sites/oystermouth-chapel", title: "3D preview", desc: "Inspect the optimised site model in the browser (Three.js)", live: true },
  { href: "/deploy", title: "Deploy", desc: "Stage model bundles for the device build (live-anchor approval gate)", live: true },
  { href: "/monitor", title: "Field-test monitor", desc: "Logged sessions: GPS accuracy, confidence, time-to-lock, drift", live: true },
  { href: "/learning", title: "Self-learning panel", desc: "Threshold history and before/after adjustment cycles (v0, rule-based)", live: true },
];

export default function Home() {
  return (
    <div>
      <h1 className="text-2xl font-semibold">Operator console</h1>
      <p className="mt-2 max-w-2xl text-sm text-slate-400">
        Full lifecycle for location-based AR sites: upload → process → deploy → monitor.
        Pages marked <span className="text-amber-300">coming next</span> have a working API
        contract behind them but no UI yet.
      </p>
      <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map((c) => (
          <Link
            key={c.href}
            href={c.href}
            className="rounded-lg border border-slate-800 bg-slate-900 p-4 transition hover:border-emerald-600"
          >
            <div className="flex items-center justify-between">
              <h2 className="font-medium">{c.title}</h2>
              {!c.live && (
                <span className="rounded bg-amber-900/60 px-2 py-0.5 text-xs text-amber-300">coming next</span>
              )}
            </div>
            <p className="mt-2 text-sm text-slate-400">{c.desc}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
