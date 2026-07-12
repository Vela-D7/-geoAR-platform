/** Static placeholder for pages whose API contract exists but UI ships next.
 *  Deliberately not a broken link and not a fake UI — it states exactly what
 *  will appear and which backend endpoint already serves the data. */
export default function ComingNext({
  title,
  description,
  endpoint,
  items,
}: {
  title: string;
  description: string;
  endpoint: string;
  items: string[];
}) {
  return (
    <div className="max-w-2xl">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-semibold">{title}</h1>
        <span className="rounded bg-amber-900/60 px-2 py-0.5 text-xs text-amber-300">coming next</span>
      </div>
      <p className="mt-2 text-sm text-slate-400">{description}</p>
      <div className="mt-6 rounded-lg border border-dashed border-slate-700 p-6">
        <p className="text-sm text-slate-300">This page will show:</p>
        <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-slate-400">
          {items.map((i) => (
            <li key={i}>{i}</li>
          ))}
        </ul>
        <p className="mt-4 text-xs text-slate-500">
          Backend already serves this data at <code className="text-slate-400">{endpoint}</code> —
          the UI is the missing piece, not the plumbing.
        </p>
      </div>
    </div>
  );
}
