"""Run one self-learning v0 cycle against the backend database and write the
before/after report (the visible adjustment cycle for the 24 July demo).

Reads sessions + current thresholds straight from the DB (same rows the API
serves), applies self_learning.v0.evaluate, and — if a rule fired — appends a
new threshold version with changed_by="self_learning_v0". Also computes what
the fusion outcomes WOULD have been under the new cutoff by re-running the
decision rule over the same sessions (replay, not simulation of new data).

Run:  cd shared-infrastructure/backend && python -m self_learning_runner  (see wrapper)
  or: cd shared-infrastructure && python -m self_learning.run_cycle
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))

from sqlalchemy import select

from app import models
from app.database import SessionLocal

from .v0 import WINDOW_N, Adjustment, evaluate, replay_outcomes

REPORTS_DIR = Path(__file__).parent / "reports"


def run(site_id: str = "oystermouth-chapel", write: bool = True) -> Adjustment:
    db = SessionLocal()
    try:
        current = db.scalars(
            select(models.ThresholdVersion)
            .where(models.ThresholdVersion.site_id == site_id)
            .order_by(models.ThresholdVersion.version.desc()).limit(1)
        ).first()
        if not current:
            raise SystemExit(f"no thresholds for site '{site_id}' — seed the backend first")

        rows = db.scalars(
            select(models.FieldTestSession)
            .where(models.FieldTestSession.site_id == site_id)
            .order_by(models.FieldTestSession.ended_at.desc())
            .limit(WINDOW_N)
        ).all()
        sessions = [
            {"visual_confidence": r.visual_confidence, "outcome": r.outcome,
             "drift_m": r.drift_m, "final_state": r.final_state, "source": r.source,
             "lighting": r.lighting, "ended_at": r.ended_at}
            for r in rows
        ]

        adjustment = evaluate(sessions, current.visual_confidence_min)

        new_version = None
        if adjustment.action != "hold" and write:
            new_version = models.ThresholdVersion(
                site_id=site_id,
                version=current.version + 1,
                gps_accuracy_good_m=current.gps_accuracy_good_m,
                visual_confidence_min=adjustment.new_cutoff,
                changed_by="self_learning_v0",
                reason=adjustment.reason,
            )
            db.add(new_version)
            db.commit()

        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "site_id": site_id,
            "loop_version": "v0 (rule-based — NOT a trained model)",
            "data_provenance": sorted({s["source"] for s in sessions}),
            "action": adjustment.action,
            "reason": adjustment.reason,
            "evidence": adjustment.evidence,
            "before": {
                "threshold_version": current.version,
                "visual_confidence_min": adjustment.old_cutoff,
                "replayed_window_outcomes": replay_outcomes(sessions, adjustment.old_cutoff),
            },
            "after": {
                "threshold_version": new_version.version if new_version else current.version,
                "visual_confidence_min": adjustment.new_cutoff,
                "replayed_window_outcomes": replay_outcomes(sessions, adjustment.new_cutoff),
            },
        }

        REPORTS_DIR.mkdir(exist_ok=True)
        (REPORTS_DIR / "before_after.json").write_text(json.dumps(report, indent=2))
        (REPORTS_DIR / "before_after.md").write_text(render_markdown(report))
        print(json.dumps(report, indent=2))
        print(f"\nreports: {REPORTS_DIR}/before_after.{{json,md}}")
        return adjustment
    finally:
        db.close()


def render_markdown(r: dict) -> str:
    b, a = r["before"], r["after"]
    rows = "\n".join(
        f"| {k.replace('_', ' ')} | {b['replayed_window_outcomes'][k]} | {a['replayed_window_outcomes'][k]} |"
        for k in b["replayed_window_outcomes"]
    )
    return f"""# Self-learning v0 — before/after adjustment cycle

*Generated {r['generated_at']} · site `{r['site_id']}` · {r['loop_version']}*
*Data provenance: {', '.join(r['data_provenance'])} — synthetic/replay sessions are labelled as such everywhere they appear.*

**Action:** `{r['action'].upper()}` — {r['reason']}

| | Before | After |
|---|---|---|
| Threshold version | v{b['threshold_version']} | v{a['threshold_version']} |
| `visual_confidence_min` | {b['visual_confidence_min']} | {a['visual_confidence_min']} |
{rows}

*"Replayed window outcomes" re-applies the visual-lock rule to the same {r['evidence'].get('window', '?')}
logged sessions under each cutoff — a replay of recorded data, not a prediction of future performance.*

Rollback: re-issue v{b['threshold_version']} values via `PUT /api/sites/{r['site_id']}/thresholds`
(every change is an append-only version; nothing is overwritten).
"""


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "oystermouth-chapel")
