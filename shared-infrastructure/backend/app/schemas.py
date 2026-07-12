"""Pydantic request/response models. Field-test ingest is additionally validated
against the canonical JSON Schema so device firmware and backend can never drift."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

SCHEMA_PATH = Path(__file__).parents[2] / "schemas" / "field_test_log.schema.json"
FIELD_TEST_JSON_SCHEMA = json.loads(SCHEMA_PATH.read_text())


class SiteCreate(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,62}$")
    name: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class SiteOut(SiteCreate):
    recognition_target_status: str
    model_asset_path: str | None
    last_outcome: str | None = None
    session_count: int = 0

    model_config = {"from_attributes": True}


class AnchorCreate(BaseModel):
    anchor_handle: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    altitude_m: float | None = None
    is_live: bool = False
    confirm_overwrite_live: bool = False


class AnchorOut(AnchorCreate):
    id: int
    site_id: str

    model_config = {"from_attributes": True}


class ThresholdsOut(BaseModel):
    site_id: str
    version: int
    gps_accuracy_good_m: float
    visual_confidence_min: float
    changed_by: str
    reason: str

    model_config = {"from_attributes": True}


class ThresholdsUpdate(BaseModel):
    gps_accuracy_good_m: float = Field(gt=0, le=100)
    visual_confidence_min: float = Field(ge=0.05, le=0.99)
    changed_by: Literal["operator", "self_learning_v0"]
    reason: str


class UploadValidation(BaseModel):
    filename: str
    size_bytes: int
    accepted: bool
    checks: list[dict]
