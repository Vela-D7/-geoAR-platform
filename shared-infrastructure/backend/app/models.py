"""ORM models: sites, anchors, field-test sessions, threshold config history."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # slug, e.g. oystermouth-chapel
    name: Mapped[str] = mapped_column(String(200))
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    recognition_target_status: Mapped[str] = mapped_column(
        String(32), default="none"
    )  # none | building | ready | degraded
    model_asset_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    anchors: Mapped[list["Anchor"]] = relationship(back_populates="site", cascade="all, delete-orphan")
    sessions: Mapped[list["FieldTestSession"]] = relationship(back_populates="site", cascade="all, delete-orphan")
    threshold_versions: Mapped[list["ThresholdVersion"]] = relationship(
        back_populates="site", cascade="all, delete-orphan", order_by="ThresholdVersion.version"
    )


class Anchor(Base):
    __tablename__ = "anchors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id"))
    anchor_handle: Mapped[str] = mapped_column(String(128))  # provider-scoped handle
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    altitude_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_live: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    site: Mapped[Site] = relationship(back_populates="anchors")


class FieldTestSession(Base):
    __tablename__ = "field_test_sessions"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id"), index=True)
    device_profile: Mapped[str] = mapped_column(String(32))
    started_at: Mapped[str] = mapped_column(String(32))
    ended_at: Mapped[str] = mapped_column(String(32))
    gps_accuracy_m: Mapped[float] = mapped_column(Float)
    visual_confidence: Mapped[float] = mapped_column(Float)
    time_to_lock_s: Mapped[float] = mapped_column(Float)
    drift_m: Mapped[float] = mapped_column(Float)
    lighting: Mapped[str] = mapped_column(String(16))
    final_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    outcome: Mapped[str] = mapped_column(String(16), index=True)
    relock_attempts: Mapped[int] = mapped_column(Integer, default=0)
    flags: Mapped[list] = mapped_column(JSON, default=list)
    source: Mapped[str] = mapped_column(String(16), index=True)  # field | synthetic | replay
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    site: Mapped[Site] = relationship(back_populates="sessions")


class ProcessingJob(Base):
    """One optimisation run for an uploaded scan. Steps are recorded as an
    ordered JSON list [{name, status, detail}] the web Processing page polls.
    On failure the job retries once with alternative (more conservative)
    pipeline settings before reporting a clear error + capture recommendation
    (spec: AI Orchestration Logic, reconstruction failure branch)."""

    __tablename__ = "processing_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id"), index=True)
    scan_path: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(16), default="queued")  # queued|running|succeeded|failed
    attempt: Mapped[int] = mapped_column(Integer, default=1)
    settings_profile: Mapped[str] = mapped_column(String(32), default="standard")
    steps: Mapped[list] = mapped_column(JSON, default=list)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_manifest: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Deploy(Base):
    """A deploy = versioned bundle (LOD GLBs + manifest + target placeholder)
    staged for the device build. Deploying to a site with a live anchor
    requires explicit confirmation (spec security check)."""

    __tablename__ = "deploys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id"), index=True)
    bundle_path: Mapped[str] = mapped_column(String(500))
    manifest: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(16), default="staged")  # staged|delivered
    triggered_by: Mapped[str] = mapped_column(String(64), default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LearningReport(Base):
    """One self-learning v0 cycle result (action + before/after replay), stored
    so the web panel shows history without reading files off the worker."""

    __tablename__ = "learning_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id"), index=True)
    action: Mapped[str] = mapped_column(String(16))  # loosen|tighten|hold
    report: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ThresholdVersion(Base):
    """Per-site fusion thresholds. Append-only: every change (manual or from the
    self-learning loop) is a new version so regressions can be rolled back."""

    __tablename__ = "threshold_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    gps_accuracy_good_m: Mapped[float] = mapped_column(Float)
    visual_confidence_min: Mapped[float] = mapped_column(Float)
    changed_by: Mapped[str] = mapped_column(String(64))  # "operator" | "self_learning_v0"
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    site: Mapped[Site] = relationship(back_populates="threshold_versions")
