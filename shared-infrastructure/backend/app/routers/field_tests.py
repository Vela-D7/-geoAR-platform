"""Field-test log ingest + query. Ingest validates against the canonical JSON
Schema (shared with device logger and fusion reference) before touching the DB."""

from __future__ import annotations

import jsonschema
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from ..auth import require_operator
from ..database import get_db
from ..schemas import FIELD_TEST_JSON_SCHEMA

router = APIRouter(prefix="/api/field-tests", tags=["field-tests"], dependencies=[Depends(require_operator)])


@router.post("", status_code=201)
def ingest_session(record: dict, db: Session = Depends(get_db)):
    try:
        jsonschema.validate(record, FIELD_TEST_JSON_SCHEMA)
    except jsonschema.ValidationError as e:
        raise HTTPException(422, f"log record does not match field_test_log schema v1: {e.message}")

    if not db.get(models.Site, record["site_id"]):
        raise HTTPException(404, f"unknown site '{record['site_id']}' — register the site first")
    if db.get(models.FieldTestSession, record["session_id"]):
        raise HTTPException(409, "session_id already ingested")

    row = models.FieldTestSession(
        **{k: v for k, v in record.items() if k not in ("schema_version", "time_of_day_local")}
    )
    db.add(row)
    db.commit()
    return {"ingested": record["session_id"]}


@router.get("")
def list_sessions(
    site_id: str | None = None,
    source: str | None = None,
    limit: int = 200,
    db: Session = Depends(get_db),
):
    q = select(models.FieldTestSession).order_by(models.FieldTestSession.ended_at.desc()).limit(min(limit, 1000))
    if site_id:
        q = q.where(models.FieldTestSession.site_id == site_id)
    if source:
        q = q.where(models.FieldTestSession.source == source)
    rows = db.scalars(q).all()
    return [
        {c.name: getattr(r, c.name) for c in models.FieldTestSession.__table__.columns}
        for r in rows
    ]
