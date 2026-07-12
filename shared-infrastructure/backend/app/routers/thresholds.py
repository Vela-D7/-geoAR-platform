"""Per-site fusion thresholds with append-only version history (rollback = new
version copying an old one). The self-learning loop writes through this same
path with changed_by=self_learning_v0."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from ..auth import require_operator
from ..database import get_db
from ..schemas import ThresholdsOut, ThresholdsUpdate

router = APIRouter(prefix="/api/sites/{site_id}/thresholds", tags=["thresholds"], dependencies=[Depends(require_operator)])


def _latest(db: Session, site_id: str) -> models.ThresholdVersion | None:
    return db.scalars(
        select(models.ThresholdVersion)
        .where(models.ThresholdVersion.site_id == site_id)
        .order_by(models.ThresholdVersion.version.desc())
        .limit(1)
    ).first()


@router.get("", response_model=ThresholdsOut)
def current_thresholds(site_id: str, db: Session = Depends(get_db)):
    latest = _latest(db, site_id)
    if not latest:
        raise HTTPException(404, "site not found or has no threshold config")
    return latest


@router.get("/history", response_model=list[ThresholdsOut])
def threshold_history(site_id: str, db: Session = Depends(get_db)):
    return db.scalars(
        select(models.ThresholdVersion)
        .where(models.ThresholdVersion.site_id == site_id)
        .order_by(models.ThresholdVersion.version)
    ).all()


@router.put("", response_model=ThresholdsOut, status_code=201)
def update_thresholds(site_id: str, body: ThresholdsUpdate, db: Session = Depends(get_db)):
    if not db.get(models.Site, site_id):
        raise HTTPException(404, "site not found")
    latest = _latest(db, site_id)
    next_version = (latest.version + 1) if latest else 1
    row = models.ThresholdVersion(site_id=site_id, version=next_version, **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
