"""Processing jobs: enqueue an optimisation run for a site's uploaded scan and
poll per-step status (the web Processing page's data source)."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from ..auth import require_operator
from ..database import get_db

router = APIRouter(prefix="/api", tags=["jobs"], dependencies=[Depends(require_operator)])


def _job_out(j: models.ProcessingJob) -> dict:
    return {
        "id": j.id,
        "site_id": j.site_id,
        "status": j.status,
        "attempt": j.attempt,
        "settings_profile": j.settings_profile,
        "steps": j.steps,
        "error": j.error,
        "recommendation": j.recommendation,
        "output_manifest": j.output_manifest,
        "created_at": j.created_at.isoformat() if j.created_at else None,
        "updated_at": j.updated_at.isoformat() if j.updated_at else None,
    }


@router.post("/sites/{site_id}/process", status_code=202)
def enqueue_processing(site_id: str, db: Session = Depends(get_db)):
    site = db.get(models.Site, site_id)
    if not site:
        raise HTTPException(404, "site not found")
    if not site.model_asset_path or not Path(site.model_asset_path).exists():
        raise HTTPException(409, "no uploaded scan for this site — upload first")

    job = models.ProcessingJob(site_id=site_id, scan_path=site.model_asset_path)
    db.add(job)
    db.commit()
    db.refresh(job)

    from ..jobs.tasks import process_scan  # deferred: importing pulls in trimesh

    process_scan.delay(job.id)
    return {"job_id": job.id, "status": "queued"}


@router.get("/sites/{site_id}/jobs")
def list_jobs(site_id: str, db: Session = Depends(get_db)):
    if not db.get(models.Site, site_id):
        raise HTTPException(404, "site not found")
    rows = db.scalars(
        select(models.ProcessingJob)
        .where(models.ProcessingJob.site_id == site_id)
        .order_by(models.ProcessingJob.id.desc())
        .limit(50)
    ).all()
    return [_job_out(j) for j in rows]


@router.get("/jobs/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(models.ProcessingJob, job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return _job_out(job)
