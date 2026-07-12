import ComingNext from "@/components/ComingNext";

export default function MonitorPage() {
  return (
    <ComingNext
      title="Field-test monitor"
      description="Logged device sessions per site: GPS accuracy, visual confidence, time-to-lock, drift, outcome — timestamped, filterable by provenance (field / synthetic / replay)."
      endpoint="GET /api/field-tests?site_id=…&source=…"
      items={[
        "Session table with outcome badges and provenance labels",
        "Charts: time-to-lock and drift trends over sessions",
        "Flag list (rescan_recommended, tracking_lost) per session",
      ]}
    />
  );
}
