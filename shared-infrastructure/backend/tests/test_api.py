"""Backend API tests: auth, site/anchor CRUD + live-anchor guard, log ingest
validation, threshold versioning."""

import os
import sys
from pathlib import Path

os.environ["GEOAR_DATABASE_URL"] = "sqlite:///./test_geoar.db"
sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, str(Path(__file__).parents[3] / "prototype-a-xreal-now"))

import pytest
from fastapi.testclient import TestClient

from app.auth import DEV_DEFAULT_TOKEN
from app.database import Base, engine
from app.main import app

from fusion import mocks
from fusion.session import run_session

AUTH = {"X-Operator-Token": DEV_DEFAULT_TOKEN}


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
    body = {"id": "oystermouth-chapel", "name": "Oystermouth Castle Chapel", "lat": 51.572, "lon": -4.013}
    assert client.post("/api/sites", json=body, headers=AUTH).status_code == 201
    return body["id"]


def make_log(site_id="oystermouth-chapel"):
    return run_session(mocks.clean_fused_lock(), site_id=site_id, source="synthetic")


class TestAuth:
    def test_rejects_missing_token(self, client):
        assert client.get("/api/sites").status_code == 401

    def test_rejects_wrong_token(self, client):
        assert client.get("/api/sites", headers={"X-Operator-Token": "wrong"}).status_code == 401

    def test_health_is_public(self, client):
        assert client.get("/api/health").status_code == 200


class TestSitesAndAnchors:
    def test_create_and_list_site(self, client, site):
        sites = client.get("/api/sites", headers=AUTH).json()
        assert [s["id"] for s in sites] == [site]

    def test_duplicate_site_conflict(self, client, site):
        body = {"id": site, "name": "dup", "lat": 0, "lon": 0}
        assert client.post("/api/sites", json=body, headers=AUTH).status_code == 409

    def test_new_site_gets_default_thresholds_v1(self, client, site):
        t = client.get(f"/api/sites/{site}/thresholds", headers=AUTH).json()
        assert t["version"] == 1 and t["visual_confidence_min"] == 0.70

    def test_live_anchor_overwrite_requires_confirmation(self, client, site):
        anchor = {"anchor_handle": "a1", "lat": 51.572, "lon": -4.013, "is_live": True}
        assert client.post(f"/api/sites/{site}/anchors", json=anchor, headers=AUTH).status_code == 201

        second = {**anchor, "anchor_handle": "a2"}
        r = client.post(f"/api/sites/{site}/anchors", json=second, headers=AUTH)
        assert r.status_code == 409  # explicit approval gate per spec

        second["confirm_overwrite_live"] = True
        assert client.post(f"/api/sites/{site}/anchors", json=second, headers=AUTH).status_code == 201

        live = [a for a in client.get(f"/api/sites/{site}/anchors", headers=AUTH).json() if a["is_live"]]
        assert [a["anchor_handle"] for a in live] == ["a2"]


class TestFieldTestIngest:
    def test_ingest_valid_log(self, client, site):
        r = client.post("/api/field-tests", json=make_log(), headers=AUTH)
        assert r.status_code == 201

    def test_rejects_schema_violation(self, client, site):
        bad = make_log()
        bad["visual_confidence"] = 1.7  # out of range
        r = client.post("/api/field-tests", json=bad, headers=AUTH)
        assert r.status_code == 422
        assert "schema" in r.json()["detail"]

    def test_rejects_unknown_site(self, client, site):
        r = client.post("/api/field-tests", json=make_log(site_id="nowhere"), headers=AUTH)
        # unknown site slug is schema-valid but unregistered
        assert r.status_code == 404

    def test_rejects_duplicate_session(self, client, site):
        log = make_log()
        assert client.post("/api/field-tests", json=log, headers=AUTH).status_code == 201
        assert client.post("/api/field-tests", json=log, headers=AUTH).status_code == 409

    def test_query_filters_by_source(self, client, site):
        client.post("/api/field-tests", json=make_log(), headers=AUTH)
        assert len(client.get("/api/field-tests?source=synthetic", headers=AUTH).json()) == 1
        assert len(client.get("/api/field-tests?source=field", headers=AUTH).json()) == 0

    def test_site_summary_reflects_sessions(self, client, site):
        client.post("/api/field-tests", json=make_log(), headers=AUTH)
        s = client.get(f"/api/sites/{site}", headers=AUTH).json()
        assert s["session_count"] == 1 and s["last_outcome"] == "success"


class TestThresholdVersioning:
    def test_update_appends_version(self, client, site):
        body = {"gps_accuracy_good_m": 10.0, "visual_confidence_min": 0.65,
                "changed_by": "self_learning_v0", "reason": "test adjustment"}
        r = client.put(f"/api/sites/{site}/thresholds", json=body, headers=AUTH)
        assert r.status_code == 201 and r.json()["version"] == 2

        history = client.get(f"/api/sites/{site}/thresholds/history", headers=AUTH).json()
        assert [h["version"] for h in history] == [1, 2]
        assert history[0]["visual_confidence_min"] == 0.70  # v1 retained for rollback
