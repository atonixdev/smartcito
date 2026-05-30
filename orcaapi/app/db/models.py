"""
================================================================================
 File: orcaapi/app/db/models.py
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

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, Float, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from geoalchemy2 import Geometry
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from app.db.base import Base


class PostGISGeometry(TypeDecorator):
    """Use native PostGIS geometry on PostgreSQL and JSON elsewhere."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):  # type: ignore[override]
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Geometry(geometry_type="GEOMETRY", srid=4326))
        return dialect.type_descriptor(JSON())


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


class GPSPointORM(Base):
    """Persistent representation of an ingested GPS point."""

    __tablename__ = "gps_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    speed: Mapped[float | None] = mapped_column(Float, nullable=True)
    heading: Mapped[float | None] = mapped_column(Float, nullable=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (Index("ix_gps_points_device_ts", "device_id", "ts"),)


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


class DroneRegistryORM(Base):
    """Persistent drone capability and registry record maintained by Drone Gateway."""

    __tablename__ = "drone_registry"

    drone_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    firmware_version: Mapped[str] = mapped_column(String(80), nullable=False)
    max_speed_mps: Mapped[float] = mapped_column(Float, nullable=False)
    max_altitude_m: Mapped[float] = mapped_column(Float, nullable=False)
    battery_capacity_mah: Mapped[int] = mapped_column(Integer, nullable=False)
    camera_types: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    sensors: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    payload_supported: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False, default="offline")
    protocol: Mapped[str] = mapped_column(String(40), nullable=False, default="simulated")
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )


class GeoFeatureORM(Base):
    """Persistent geographic feature stored in PostGIS-compatible form."""

    __tablename__ = "geo_features"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    feature_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    feature_type: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    zone: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    geometry_type: Mapped[str] = mapped_column(String(24), nullable=False)
    geometry_geojson: Mapped[dict] = mapped_column(JSON, nullable=False)
    geometry: Mapped[object | None] = mapped_column(PostGISGeometry(), nullable=True)
    properties: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    source_service: Mapped[str] = mapped_column(String(80), nullable=False, default="orcaapi")
    timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    __table_args__ = (Index("ix_geo_features_type_zone", "feature_type", "zone"),)


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
