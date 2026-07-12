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
