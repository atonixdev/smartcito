"""
================================================================================
 File: surveillance/registry.py
 Purpose:
   PostgreSQL-backed Drone Registry used by the Drone Gateway Service. The
   service keeps an in-memory mirror for local development and syncs capability
   records to PostgreSQL when a database is reachable.
================================================================================
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

from surveillance.models import DroneCapabilities, DroneRegistryStatus


class DroneRegistry:
    def __init__(self) -> None:
        self._cache: dict[str, DroneCapabilities] = {}
        self._engine: Any | None = None
        self._db_status = "not-initialized"

    @property
    def db_status(self) -> str:
        return self._db_status

    def _database_url(self) -> str:
        explicit_url = os.getenv("DRONE_REGISTRY_DATABASE_URL") or os.getenv("DATABASE_URL")
        if explicit_url:
            return explicit_url.replace("postgresql+asyncpg://", "postgresql+psycopg://")

        host = os.getenv("DB_HOST", "postgres")
        port = os.getenv("DB_PORT", "5432")
        name = os.getenv("DB_NAME", "orca")
        user = os.getenv("DB_USER", "orca")
        password = os.getenv("DB_PASSWORD", "orca")
        return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"

    def _load_engine(self) -> Any | None:
        if os.getenv("DRONE_REGISTRY_ENABLED", "1").lower() in {"0", "false", "no"}:
            self._db_status = "disabled"
            return None
        if self._engine is not None:
            return self._engine

        try:
            from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, MetaData, String, Table, create_engine
            from sqlalchemy.dialects.postgresql import insert
        except ModuleNotFoundError:
            self._db_status = "sqlalchemy-unavailable"
            return None

        metadata = MetaData()
        self._table = Table(
            "drone_registry",
            metadata,
            __import__("sqlalchemy").Column("drone_id", String(80), primary_key=True),
            __import__("sqlalchemy").Column("model", String(120), nullable=False),
            __import__("sqlalchemy").Column("firmware_version", String(80), nullable=False),
            __import__("sqlalchemy").Column("max_speed_mps", Float, nullable=False),
            __import__("sqlalchemy").Column("max_altitude_m", Float, nullable=False),
            __import__("sqlalchemy").Column("battery_capacity_mah", Integer, nullable=False),
            __import__("sqlalchemy").Column("camera_types", JSON, nullable=False, default=list),
            __import__("sqlalchemy").Column("sensors", JSON, nullable=False, default=list),
            __import__("sqlalchemy").Column("payload_supported", Boolean, nullable=False, default=False),
            __import__("sqlalchemy").Column("status", String(32), nullable=False, default=DroneRegistryStatus.OFFLINE.value),
            __import__("sqlalchemy").Column("protocol", String(40), nullable=False, default="simulated"),
            __import__("sqlalchemy").Column("last_seen_at", DateTime(timezone=True), nullable=False),
            __import__("sqlalchemy").Column("updated_at", DateTime(timezone=True), nullable=False),
        )
        self._insert = insert

        try:
            self._engine = create_engine(self._database_url(), pool_pre_ping=True, future=True)
            metadata.create_all(self._engine)
        except Exception as exc:  # pragma: no cover - depends on external database availability
            self._db_status = f"database-unavailable:{exc.__class__.__name__}"
            self._engine = None
            return None

        self._db_status = "ready"
        return self._engine

    def upsert(self, capabilities: DroneCapabilities) -> str:
        self._cache[capabilities.drone_id] = capabilities
        engine = self._load_engine()
        if engine is None:
            return self._db_status

        payload = capabilities.model_dump(mode="python")
        payload["updated_at"] = datetime.now(UTC)
        try:
            statement = self._insert(self._table).values(**payload)
            update_payload = {key: statement.excluded[key] for key in payload if key != "drone_id"}
            statement = statement.on_conflict_do_update(
                index_elements=["drone_id"],
                set_=update_payload,
            )
            with engine.begin() as connection:
                connection.execute(statement)
        except Exception as exc:  # pragma: no cover - depends on external database availability
            self._db_status = f"sync-failed:{exc.__class__.__name__}"
            return self._db_status

        self._db_status = "synced"
        return self._db_status

    def get(self, drone_id: str) -> DroneCapabilities | None:
        if drone_id in self._cache:
            return self._cache[drone_id]

        engine = self._load_engine()
        if engine is None:
            return None

        try:
            from sqlalchemy import select

            with engine.begin() as connection:
                row = connection.execute(select(self._table).where(self._table.c.drone_id == drone_id)).mappings().first()
        except Exception as exc:  # pragma: no cover - depends on external database availability
            self._db_status = f"read-failed:{exc.__class__.__name__}"
            return None

        if row is None:
            return None

        capabilities = DroneCapabilities(
            drone_id=str(row["drone_id"]),
            model=str(row["model"]),
            firmware_version=str(row["firmware_version"]),
            max_speed_mps=float(row["max_speed_mps"]),
            max_altitude_m=float(row["max_altitude_m"]),
            battery_capacity_mah=int(row["battery_capacity_mah"]),
            camera_types=list(row["camera_types"] or []),
            sensors=list(row["sensors"] or []),
            payload_supported=bool(row["payload_supported"]),
            status=DroneRegistryStatus(str(row["status"])),
            protocol=str(row["protocol"]),
            last_seen_at=row["last_seen_at"],
        )
        self._cache[drone_id] = capabilities
        return capabilities

    def list(self) -> list[DroneCapabilities]:
        return sorted(self._cache.values(), key=lambda item: item.drone_id)


registry = DroneRegistry()
