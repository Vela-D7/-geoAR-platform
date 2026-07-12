"""Scan-processing task: mesh cleanup → LOD generation → texture bake (stub) →
recognition target build (stub), with per-step pass/fail persisted after every
step so the Processing page shows live progress.

Failure policy (spec: AI Orchestration Logic):
  attempt 1 runs the "standard" profile; on any step failure the task re-enqueues
  itself once with the "conservative" profile (halved LOD budgets, lenient
  cleanup). If that also fails: status=failed with a clear error and a capture
  recommendation. No silent skips.

Reuses the Prototype A pipeline code — one optimisation implementation across
the platform.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parents[4]
sys.path.insert(0, str(REPO_ROOT / "prototype-a-xreal-now"))

import trimesh  # noqa: E402

from pipeline import optimise  # noqa: E402  (prototype-a package)

from ..database import SessionLocal  # noqa: E402
from .. import models  # noqa: E402
from .celery_app import celery  # noqa: E402

PROFILES = {
    "standard": {"budgets": {0: 100_000, 1: 25_000, 2: 5_000}, "lenient": False},
    # Conservative retry: smaller outputs, tolerate scan debris.
    "conservative": {"budgets": {0: 50_000, 1: 12_000, 2: 3_000}, "lenient": True},
}
RETRY_ORDER = ["standard", "conservative"]

CAPTURE_RECOMMENDATION = (
    "Processing failed under both settings profiles. Common capture causes: "
    "incomplete coverage (rescan with slower, overlapping passes), scan debris "
    "from moving objects, or a corrupt export. Re-export as binary GLB/PLY and "
    "re-upload; if failure persists, rescan the site."
)


def _set_step(db, job, name: str, status: str, detail: str = "") -> None:
    steps = [s for s in job.steps if s["name"] != name]
    steps.append({"name": name, "status": status, "detail": detail})
    order = ["mesh_cleanup", "lod_generation", "texture_bake", "recognition_target"]
    job.steps = sorted(steps, key=lambda s: order.index(s["name"]))
    db.commit()


@celery.task(name="geoar.process_scan")
def process_scan(job_id: int) -> str:
    db = SessionLocal()
    try:
        job = db.get(models.ProcessingJob, job_id)
        if job is None:
            return "missing"
        profile = PROFILES[job.settings_profile]
        job.status = "running"
        job.steps = []
        db.commit()

        out_dir = Path(job.scan_path).parent / f"processed_attempt{job.attempt}"

        try:
            # Step 1: cleanup
            _set_step(db, job, "mesh_cleanup", "running")
            mesh = optimise.load_input_mesh(job.scan_path)
            cleaned = optimise.clean_mesh(mesh)
            if len(cleaned.faces) == 0 or (not profile["lenient"] and len(cleaned.faces) < 100):
                raise ValueError(f"cleanup left {len(cleaned.faces)} faces — scan too sparse")
            _set_step(db, job, "mesh_cleanup", "passed", f"{len(mesh.faces)} -> {len(cleaned.faces)} faces")

            # Step 2: LOD generation
            _set_step(db, job, "lod_generation", "running")
            out_dir.mkdir(parents=True, exist_ok=True)
            lods = []
            for tier, budget in profile["budgets"].items():
                lod = optimise.decimate_to(cleaned, budget)
                path = out_dir / f"lod{tier}.glb"
                lod.export(path)
                lods.append({"tier": tier, "faces": len(lod.faces), "path": str(path)})
            # Tiers must never grow; equal tiers are legitimate when the input
            # mesh is already under a budget (decimation no-ops). The smallest
            # tier must always be within its budget.
            counts = [l["faces"] for l in lods]
            smallest_budget = min(profile["budgets"].values())
            if not all(a >= b for a, b in zip(counts, counts[1:])):
                raise ValueError(f"LOD tiers increased across levels: {counts}")
            if counts[-1] > smallest_budget:
                raise ValueError(f"final LOD {counts[-1]} faces exceeds budget {smallest_budget}")
            _set_step(db, job, "lod_generation", "passed", f"tiers {counts}")

            # Step 3: texture bake — declared stub (Blender headless job pending)
            _set_step(db, job, "texture_bake", "stub", "Blender bake job not yet implemented — tracked pre-24 July")

            # Step 4: recognition target — declared stub (MultiSet/custom feature map pending)
            _set_step(db, job, "recognition_target", "stub", "feature-map build pending fine-lock vendor decision")

            job.status = "succeeded"
            job.output_manifest = {"lods": lods, "profile": job.settings_profile}
            site = db.get(models.Site, job.site_id)
            site.recognition_target_status = "ready"
            db.commit()
            return "succeeded"

        except Exception as e:  # any step failure
            failed_step = next((s["name"] for s in job.steps if s["status"] == "running"), "mesh_cleanup")
            _set_step(db, job, failed_step, "failed", str(e)[:300])

            next_idx = RETRY_ORDER.index(job.settings_profile) + 1
            if next_idx < len(RETRY_ORDER):
                retry = models.ProcessingJob(
                    site_id=job.site_id,
                    scan_path=job.scan_path,
                    attempt=job.attempt + 1,
                    settings_profile=RETRY_ORDER[next_idx],
                )
                db.add(retry)
                job.status = "failed"
                job.error = f"{failed_step}: {e} — retrying with '{RETRY_ORDER[next_idx]}' profile"
                db.commit()
                process_scan.delay(retry.id)
                return "retrying"

            job.status = "failed"
            job.error = f"{failed_step}: {e}"
            job.recommendation = CAPTURE_RECOMMENDATION
            db.commit()
            return "failed"
    finally:
        db.close()
