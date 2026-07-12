"""Self-learning v0 over the API: run one cycle for a site (writes a versioned
threshold change when a rule fires, plus a stored report), and read report
history — the data source for the web Self-learning panel.

The rule engine lives in the sibling self_learning package (monorepo, not
packaged); the path insert below is the controlled seam."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parents[3]))  # shared-infrastructure/

from self_learning.v0 import WINDOW_N, evaluate, replay_outcomes  # noqa: E402

from .. import models  # noqa: E402
from ..auth import require_operator  # noqa: E402
from ..database import get_db  # noqa: E402

router = APIRouter(prefix="/api/sites/{site_id}/learning", tags=["learning"], dependencies=[Depends(require_operator)])


def _window_sessions(db: Session, site_id: str) -> list[dict]:
    rows = db.scalars(
        select(models.FieldTestSession)
        .where(models.FieldTestSession.site_id == site_id)
        .order_by(models.FieldTestSession.ended_at.desc())
        .limit(WINDOW_N)
    ).all()
    return [
        {"visual_confidence": r.visual_confidence, "outcome": r.outcome,
         "drift_m": r.drift_m, "final_state": r.final_state, "source": r.source}
        for r in rows
    ]


@router.post("/run", status_code=201)
def run_cycle(site_id: str, db: Session = Depends(get_db)):
    current = db.scalars(
        select(models.ThresholdVersion)
        .where(models.ThresholdVersion.site_id == site_id)
        .order_by(models.ThresholdVersion.version.desc()).limit(1)
    ).first()
    if not current:
        raise HTTPException(404, "site not found or has no threshold config")

    sessions = _window_sessions(db, site_id)
    adjustment = evaluate(sessions, current.visual_confidence_min)

    new_version = current.version
    if adjustment.action != "hold":
        row = models.ThresholdVersion(
            site_id=site_id,
            version=current.version + 1,
            gps_accuracy_good_m=current.gps_accuracy_good_m,
            visual_confidence_min=adjustment.new_cutoff,
            changed_by="self_learning_v0",
            reason=adjustment.reason,
        )
        db.add(row)
        new_version = row.version

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
            "threshold_version": new_version,
            "visual_confidence_min": adjustment.new_cutoff,
            "replayed_window_outcomes": replay_outcomes(sessions, adjustment.new_cutoff),
        },
    }
    db.add(models.LearningReport(site_id=site_id, action=adjustment.action, report=report))
    db.commit()
    return report


@router.get("/reports")
def report_history(site_id: str, db: Session = Depends(get_db)):
    if not db.get(models.Site, site_id):
        raise HTTPException(404, "site not found")
    rows = db.scalars(
        select(models.LearningReport)
        .where(models.LearningReport.site_id == site_id)
        .order_by(models.LearningReport.id.desc())
        .limit(50)
    ).all()
    return [{"id": r.id, "action": r.action, "created_at": r.created_at.isoformat(), "report": r.report} for r in rows]
