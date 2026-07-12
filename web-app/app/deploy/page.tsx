import ComingNext from "@/components/ComingNext";

export default function DeployPage() {
  return (
    <ComingNext
      title="Deploy"
      description="Trigger export/push of the optimised model + recognition target to the Unity/XREAL build (Prototype A; extendable to Prototype B)."
      endpoint="GET /api/sites/{id}/model (delivery); deploy trigger endpoint to follow"
      items={[
        "Per-site deploy button with model + target version",
        "Deploy history with who/when/what",
        "Approval gate before overwriting a live site anchor (already enforced by the API)",
      ]}
    />
  );
}
