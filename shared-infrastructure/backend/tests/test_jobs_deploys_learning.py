"""Processing jobs (eager Celery — real task code in-process), deploy approval
gate, and self-learning API endpoints."""

import os
import sys
from pathlib import Path

os.environ["GEOAR_DATABASE_URL"] = "sqlite:///./test_geoar_jobs.db"
os.environ["GEOAR_JOBS_EAGER"] = "1"
os.environ["GEOAR_STORAGE_DIR"] = "test_storage"

sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, str(Path(__file__).parents[3] / "prototype-a-xreal-now"))

import pytest
import trimesh
from fastapi.testclient import TestClient

from app.auth import DEV_DEFAULT_TOKEN
from app.database import Base, engine
from app.main import app

from fusion import mocks
from fusion.session import run_session

AUTH = {"X-Operator-Token": DEV_DEFAULT_TOKEN}
SITE = "oystermouth-chapel"


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def site(client):
    body = {"id": SITE, "name": "Oystermouth Castle Chapel", "lat": 51.572, "lon": -4.013}
    assert client.post("/api/sites", json=body, headers=AUTH).status_code == 201
    return SITE


def upload_mesh(client, site, mesh=None, name="scan.glb"):
    mesh = mesh or trimesh.creation.icosphere(subdivisions=4, radius=3.0)
    data = trimesh.exchange.gltf.export_glb(mesh)
    return client.post(
        f"/api/sites/{site}/scans",
        files={"file": (name, data, "model/gltf-binary")},
        headers=AUTH,
    )


class TestProcessingJobs:
    def test_upload_enqueues_and_processes(self, client, site):
        r = upload_mesh(client, site)
        assert r.status_code == 200 and r.json()["accepted"]
        job_id = r.json()["job_id"]
        assert job_id is not None

        job = client.get(f"/api/jobs/{job_id}", headers=AUTH).json()
        assert job["status"] == "succeeded"
        by_name = {s["name"]: s for s in job["steps"]}
        assert by_name["mesh_cleanup"]["status"] == "passed"
        assert by_name["lod_generation"]["status"] == "passed"
        assert by_name["texture_bake"]["status"] == "stub"       # declared, not hidden
        assert by_name["recognition_target"]["status"] == "stub"
        lods = job["output_manifest"]["lods"]
        counts = [l["faces"] for l in sorted(lods, key=lambda l: l["tier"])]
        assert all(a >= b for a, b in zip(counts, counts[1:]))  # non-increasing
        assert counts[-1] <= 5000  # smallest tier within budget

    def test_process_endpoint_requires_uploaded_scan(self, client, site):
        assert client.post(f"/api/sites/{site}/process", headers=AUTH).status_code == 409

    def test_failed_job_retries_with_conservative_profile(self, client, site, monkeypatch):
        # Force the standard profile to fail so the retry path runs for real.
        from app.jobs import tasks as job_tasks

        original = job_tasks.optimise.decimate_to

        def flaky(mesh, target):
            if job_tasks.PROFILES["standard"]["budgets"][0] == target:
                raise RuntimeError("simulated decimation failure at standard budget")
            return original(mesh, target)

        monkeypatch.setattr(job_tasks.optimise, "decimate_to", flaky)

        r = upload_mesh(client, site)
        jobs = client.get(f"/api/sites/{site}/jobs", headers=AUTH).json()
        assert len(jobs) == 2  # original + retry
        retry, first = jobs[0], jobs[1]
        assert first["status"] == "failed" and "retrying with 'conservative'" in first["error"]
        assert retry["settings_profile"] == "conservative"
        assert retry["attempt"] == 2
        assert retry["status"] == "succeeded"

    def test_exhausted_retries_give_error_and_capture_recommendation(self, client, site, monkeypatch):
        from app.jobs import tasks as job_tasks

        monkeypatch.setattr(
            job_tasks.optimise, "clean_mesh",
            lambda m: (_ for _ in ()).throw(ValueError("unusable scan")),
        )
        upload_mesh(client, site)
        jobs = client.get(f"/api/sites/{site}/jobs", headers=AUTH).json()
        final = jobs[0]
        assert final["status"] == "failed"
        assert final["recommendation"] and "rescan" in final["recommendation"]


class TestDeployGate:
    def test_deploy_requires_processed_model(self, client, site):
        r = client.post(f"/api/sites/{site}/deploy", json={}, headers=AUTH)
        assert r.status_code == 409

    def test_deploy_stages_bundle(self, client, site):
        upload_mesh(client, site)
        r = client.post(f"/api/sites/{site}/deploy", json={}, headers=AUTH)
        assert r.status_code == 201
        d = r.json()
        assert Path(d["bundle_path"]).exists()
        assert d["manifest"]["site_id"] == site
        assert len(client.get(f"/api/sites/{site}/deploys", headers=AUTH).json()) == 1

    def test_live_anchor_blocks_deploy_without_confirmation(self, client, site):
        upload_mesh(client, site)
        anchor = {"anchor_handle": "a1", "lat": 51.572, "lon": -4.013, "is_live": True}
        client.post(f"/api/sites/{site}/anchors", json=anchor, headers=AUTH)

        r = client.post(f"/api/sites/{site}/deploy", json={}, headers=AUTH)
        assert r.status_code == 409 and "LIVE anchor" in r.json()["detail"]

        r = client.post(f"/api/sites/{site}/deploy", json={"confirm_live_site": True}, headers=AUTH)
        assert r.status_code == 201


class TestLearningApi:
    def seed_near_miss_sessions(self, client, site, n=8):
        for _ in range(n):
            rec = run_session(mocks.dusk_never_locks(), site_id=site, source="synthetic")
            rec["drift_m"] = 0.2
            assert client.post("/api/field-tests", json=rec, headers=AUTH).status_code == 201

    def test_run_cycle_loosens_and_versions_threshold(self, client, site):
        self.seed_near_miss_sessions(client, site)
        r = client.post(f"/api/sites/{site}/learning/run", headers=AUTH)
        assert r.status_code == 201
        report = r.json()
        assert report["action"] == "loosen"
        assert report["after"]["visual_confidence_min"] < report["before"]["visual_confidence_min"]
        assert report["data_provenance"] == ["synthetic"]

        t = client.get(f"/api/sites/{site}/thresholds", headers=AUTH).json()
        assert t["version"] == 2 and t["changed_by"] == "self_learning_v0"

    def test_hold_writes_report_but_no_threshold_version(self, client, site):
        r = client.post(f"/api/sites/{site}/learning/run", headers=AUTH)  # no sessions
        assert r.status_code == 201 and r.json()["action"] == "hold"
        t = client.get(f"/api/sites/{site}/thresholds", headers=AUTH).json()
        assert t["version"] == 1
        reports = client.get(f"/api/sites/{site}/learning/reports", headers=AUTH).json()
        assert len(reports) == 1 and reports[0]["action"] == "hold"
