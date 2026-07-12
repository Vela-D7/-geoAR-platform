import ComingNext from "@/components/ComingNext";

export default function LearningPage() {
  return (
    <ComingNext
      title="Self-learning panel"
      description="Current confidence thresholds per site, append-only history of automatic adjustments, and the before/after comparison from each adjustment cycle. The loop itself is v0 — rule-based, not a trained model."
      endpoint="GET /api/sites/{id}/thresholds/history · reports in self_learning/reports/"
      items={[
        "Threshold version timeline (operator vs self_learning_v0 changes)",
        "Before/after replay comparison per adjustment cycle",
        "One-click rollback (re-issue a previous version)",
      ]}
    />
  );
}
