"""
================================================================================
 File: citosmart/app/db/models.py
 Purpose:
   SQLAlchemy ORM models. Right now there is one table — `sensor_readings`
   — that mirrors the wire-format Pydantic schema. Keeping schemas and
   models separate lets us evolve either independently.

 Migration workflow (Alembic):
     alembic revision --autogenerate -m "add sensor_readings"
     alembic upgrade head
================================================================================
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, Float, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SensorReadingORM(Base):
    """Persistent representation of an ingested sensor reading."""

    __tablename__ = "sensor_readings"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    sensor_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    extra: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    __table_args__ = (
        # Composite index for common time-bounded queries per sensor.
        Index("ix_sensor_readings_sensor_observed", "sensor_id", "observed_at"),
    )


class CameraDeviceORM(Base):
    """Persistent representation of a registered camera device."""

    __tablename__ = "camera_devices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    device_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    device_type: Mapped[str] = mapped_column(String(32), nullable=False)
    firmware_version: Mapped[str] = mapped_column(String(64), nullable=False)
    capabilities: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    network: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    security: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    mounting: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    stream_status: Mapped[str] = mapped_column(String(32), nullable=False, default="offline")
    location: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    battery_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mounted: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    tamper_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )


class AuditEventORM(Base):
    """Persistent audit trail for camera registration and telemetry changes."""

    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    entity_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
