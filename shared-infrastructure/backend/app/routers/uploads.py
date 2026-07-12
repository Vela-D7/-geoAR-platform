"""Scan upload + model delivery.

Upload: size-capped, extension-checked, then geometry-validated (loadable mesh,
non-empty, plausible extents) before it is accepted into storage — per the
spec's 'validate uploaded scan files before processing'.

Delivery: the site's optimised model is served to the web 3D preview from
storage. Object storage + signed URLs is the production plan; for the MVP the
backend serves the file directly (single operator, single site).
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import trimesh
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .. import models
from ..auth import require_operator
from ..database import get_db
from ..schemas import UploadValidation

MAX_UPLOAD_BYTES = 200 * 1024 * 1024  # LiDAR exports are big; cap per spec
ALLOWED_EXTENSIONS = {".glb", ".gltf", ".ply", ".obj", ".stl"}
STORAGE_DIR = Path(os.environ.get("GEOAR_STORAGE_DIR", "storage"))

router = APIRouter(prefix="/api/sites/{site_id}", tags=["uploads"], dependencies=[Depends(require_operator)])


def _validate_geometry(path: Path) -> list[dict]:
    checks = []
    try:
        mesh = trimesh.load(str(path), force="mesh")
        ok = isinstance(mesh, trimesh.Trimesh) and len(mesh.faces) > 0
        checks.append({"name": "loads_as_mesh", "passed": ok, "detail": f"faces={len(mesh.faces) if ok else 0}"})
        if ok:
            extents = mesh.extents
            plausible = bool(all(0.5 <= e <= 500 for e in extents))  # building-scale sanity
            checks.append({
                "name": "extents_plausible",
                "passed": plausible,
                "detail": f"extents={[round(float(e), 2) for e in extents]}m (expected building-scale, 0.5-500m)",
            })
    except Exception as e:  # malformed/hostile file: reject, never crash the API
        checks.append({"name": "loads_as_mesh", "passed": False, "detail": str(e)[:300]})
    return checks


@router.post("/scans", response_model=UploadValidation)
async def upload_scan(site_id: str, file: UploadFile, db: Session = Depends(get_db)):
    site = db.get(models.Site, site_id)
    if not site:
        raise HTTPException(404, "site not found")

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(415, f"extension '{suffix}' not allowed; expected one of {sorted(ALLOWED_EXTENSIONS)}")

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        size = 0
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                tmp.close()
                os.unlink(tmp.name)
                raise HTTPException(413, f"upload exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)}MB limit")
            tmp.write(chunk)
        tmp_path = Path(tmp.name)

    try:
        checks = _validate_geometry(tmp_path)
        accepted = all(c["passed"] for c in checks)
        if accepted:
            dest = STORAGE_DIR / site_id
            dest.mkdir(parents=True, exist_ok=True)
            final = dest / f"scan{suffix}"
            shutil.move(str(tmp_path), final)
            site.model_asset_path = str(final)
            site.recognition_target_status = "building"
            db.commit()
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    return UploadValidation(filename=file.filename or "upload", size_bytes=size, accepted=accepted, checks=checks)


@router.get("/model")
def get_model(site_id: str, db: Session = Depends(get_db)):
    site = db.get(models.Site, site_id)
    if not site:
        raise HTTPException(404, "site not found")
    if not site.model_asset_path or not Path(site.model_asset_path).exists():
        raise HTTPException(404, "no model asset for this site yet")
    return FileResponse(site.model_asset_path, media_type="model/gltf-binary")
