"""Site registry + anchors. Live-anchor overwrites require explicit confirmation
per the spec's security checks, and every anchor write is logged."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from ..auth import require_operator
from ..database import get_db
from ..schemas import AnchorCreate, AnchorOut, SiteCreate, SiteOut

log = logging.getLogger("geoar.anchors")
router = APIRouter(prefix="/api/sites", tags=["sites"], dependencies=[Depends(require_operator)])


def _site_out(site: models.Site) -> SiteOut:
    last = max(site.sessions, key=lambda s: s.ended_at, default=None)
    return SiteOut(
        id=site.id, name=site.name, lat=site.lat, lon=site.lon,
        recognition_target_status=site.recognition_target_status,
        model_asset_path=site.model_asset_path,
        last_outcome=last.outcome if last else None,
        session_count=len(site.sessions),
    )


@router.get("", response_model=list[SiteOut])
def list_sites(db: Session = Depends(get_db)):
    return [_site_out(s) for s in db.scalars(select(models.Site)).all()]


@router.post("", response_model=SiteOut, status_code=201)
def create_site(body: SiteCreate, db: Session = Depends(get_db)):
    if db.get(models.Site, body.id):
        raise HTTPException(409, f"site '{body.id}' already exists")
    site = models.Site(**body.model_dump())
    db.add(site)
    # Every site starts with a v1 default threshold config.
    db.add(models.ThresholdVersion(
        site_id=body.id, version=1,
        gps_accuracy_good_m=10.0, visual_confidence_min=0.70,
        changed_by="operator", reason="initial defaults",
    ))
    db.commit()
    db.refresh(site)
    return _site_out(site)


@router.get("/{site_id}", response_model=SiteOut)
def get_site(site_id: str, db: Session = Depends(get_db)):
    site = db.get(models.Site, site_id)
    if not site:
        raise HTTPException(404, "site not found")
    return _site_out(site)


@router.get("/{site_id}/anchors", response_model=list[AnchorOut])
def list_anchors(site_id: str, db: Session = Depends(get_db)):
    if not db.get(models.Site, site_id):
        raise HTTPException(404, "site not found")
    return db.scalars(select(models.Anchor).where(models.Anchor.site_id == site_id)).all()


@router.post("/{site_id}/anchors", response_model=AnchorOut, status_code=201)
def create_anchor(site_id: str, body: AnchorCreate, db: Session = Depends(get_db)):
    if not db.get(models.Site, site_id):
        raise HTTPException(404, "site not found")

    if body.is_live:
        existing_live = db.scalars(
            select(models.Anchor).where(models.Anchor.site_id == site_id, models.Anchor.is_live)
        ).first()
        if existing_live and not body.confirm_overwrite_live:
            raise HTTPException(
                409,
                "a live anchor already exists for this site; "
                "pass confirm_overwrite_live=true to replace it (spec: explicit approval required)",
            )
        if existing_live:
            existing_live.is_live = False
            log.warning("live anchor %s for site %s demoted by overwrite", existing_live.id, site_id)

    anchor = models.Anchor(site_id=site_id, **body.model_dump(exclude={"confirm_overwrite_live"}))
    db.add(anchor)
    db.commit()
    db.refresh(anchor)
    log.info("anchor write: site=%s handle=%s live=%s", site_id, body.anchor_handle, body.is_live)
    return anchor
