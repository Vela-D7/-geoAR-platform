"""Deploy: stage a versioned bundle (processed LODs + manifest) for the device
build. Spec security check: deploying to a site that has a LIVE anchor requires
explicit confirmation — content changing under a live anchor is an operator
decision, not a default. Every deploy is logged."""

from __future__ import annotations

import json
import logging
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from ..auth import require_operator
from ..database import get_db

log = logging.getLogger("geoar.deploys")
router = APIRouter(prefix="/api/sites/{site_id}", tags=["deploys"], dependencies=[Depends(require_operator)])


class DeployRequest(BaseModel):
    confirm_live_site: bool = False


def _deploy_out(d: models.Deploy) -> dict:
    return {
        "id": d.id,
        "site_id": d.site_id,
        "bundle_path": d.bundle_path,
        "manifest": d.manifest,
        "status": d.status,
        "triggered_by": d.triggered_by,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }


@router.post("/deploy", status_code=201)
def trigger_deploy(site_id: str, body: DeployRequest, db: Session = Depends(get_db)):
    site = db.get(models.Site, site_id)
    if not site:
        raise HTTPException(404, "site not found")

    latest_job = db.scalars(
        select(models.ProcessingJob)
        .where(models.ProcessingJob.site_id == site_id, models.ProcessingJob.status == "succeeded")
        .order_by(models.ProcessingJob.id.desc())
        .limit(1)
    ).first()
    if not latest_job or not latest_job.output_manifest:
        raise HTTPException(409, "no successfully processed model for this site — run processing first")

    has_live_anchor = db.scalars(
        select(models.Anchor).where(models.Anchor.site_id == site_id, models.Anchor.is_live)
    ).first() is not None
    if has_live_anchor and not body.confirm_live_site:
        raise HTTPException(
            409,
            "site has a LIVE anchor; deploying replaces content under it — "
            "pass confirm_live_site=true to proceed (spec: explicit approval required)",
        )

    deploys_dir = Path(latest_job.scan_path).parent / "deploys"
    deploys_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_path = deploys_dir / f"deploy_{stamp}.zip"

    manifest = {
        "site_id": site_id,
        "source_job_id": latest_job.id,
        "profile": latest_job.output_manifest.get("profile"),
        "lods": latest_job.output_manifest.get("lods", []),
        "recognition_target": "stub — pending fine-lock vendor decision",
        "created_at": stamp,
    }
    with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        for lod in manifest["lods"]:
            p = Path(lod["path"])
            if p.exists():
                zf.write(p, arcname=p.name)

    deploy = models.Deploy(site_id=site_id, bundle_path=str(bundle_path), manifest=manifest)
    db.add(deploy)
    db.commit()
    db.refresh(deploy)
    log.info("deploy staged: site=%s bundle=%s live_anchor=%s", site_id, bundle_path, has_live_anchor)
    return _deploy_out(deploy)


@router.get("/deploys")
def list_deploys(site_id: str, db: Session = Depends(get_db)):
    if not db.get(models.Site, site_id):
        raise HTTPException(404, "site not found")
    rows = db.scalars(
        select(models.Deploy)
        .where(models.Deploy.site_id == site_id)
        .order_by(models.Deploy.id.desc())
        .limit(50)
    ).all()
    return [_deploy_out(d) for d in rows]
