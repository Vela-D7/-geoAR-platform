"""GeoAR shared backend — site registry, anchors, field-test logs, thresholds.

Run:  cd shared-infrastructure/backend && uvicorn app.main:app --reload --port 8000
Auth: every /api route needs X-Operator-Token (default dev token: geoar-dev-operator;
      set GEOAR_OPERATOR_TOKEN in any non-dev deployment).
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models  # noqa: F401 — register tables before create_all
from .database import Base, engine
from .routers import field_tests, sites, thresholds, uploads

Base.metadata.create_all(bind=engine)

app = FastAPI(title="GeoAR Shared Backend", version="0.1.0")

# Web app dev origin only; tighten/replace for any non-local deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sites.router)
app.include_router(field_tests.router)
app.include_router(thresholds.router)
app.include_router(uploads.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
