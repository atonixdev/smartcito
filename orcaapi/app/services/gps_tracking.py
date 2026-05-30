"""
================================================================================
 File: orcaapi/app/services/gps_tracking.py
 Purpose:
   DB-backed GPS ingestion and query service.
================================================================================
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import GPSPointORM
from app.schemas.gps import GPSPointIn, GPSPointOut


class GPSTrackingService:
    """Persistence and retrieval logic for device GPS history."""

    async def ingest(self, session: AsyncSession, point: GPSPointIn) -> GPSPointOut:
        record = GPSPointORM(
            device_id=point.device_id,
            lat=point.lat,
            lon=point.lon,
            speed=point.speed,
            heading=point.heading,
            ts=point.ts,
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return self._to_schema(record)

    async def get_last_position(self, session: AsyncSession, device_id: str) -> GPSPointOut | None:
        record = await session.scalar(
            select(GPSPointORM)
            .where(GPSPointORM.device_id == device_id)
            .order_by(GPSPointORM.ts.desc(), GPSPointORM.id.desc())
            .limit(1)
        )
        return self._to_schema(record) if record is not None else None

    async def get_track(
        self,
        session: AsyncSession,
        device_id: str,
        *,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
        limit: int = 1000,
    ) -> list[GPSPointOut]:
        stmt = select(GPSPointORM).where(GPSPointORM.device_id == device_id)
        if from_ts is not None:
            stmt = stmt.where(GPSPointORM.ts >= from_ts)
        if to_ts is not None:
            stmt = stmt.where(GPSPointORM.ts <= to_ts)

        rows = await session.scalars(
            stmt.order_by(GPSPointORM.ts.asc(), GPSPointORM.id.asc()).limit(limit)
        )
        return [self._to_schema(record) for record in rows.all()]

    async def get_live_fleet(
        self,
        session: AsyncSession,
        *,
        active_within_minutes: int = 15,
    ) -> list[GPSPointOut]:
        active_since = datetime.now(timezone.utc) - timedelta(minutes=active_within_minutes)
        latest_ts_by_device = (
            select(
                GPSPointORM.device_id.label("device_id"),
                func.max(GPSPointORM.ts).label("latest_ts"),
            )
            .where(GPSPointORM.ts >= active_since)
            .group_by(GPSPointORM.device_id)
            .subquery()
        )

        rows = await session.scalars(
            select(GPSPointORM)
            .join(
                latest_ts_by_device,
                (GPSPointORM.device_id == latest_ts_by_device.c.device_id)
                & (GPSPointORM.ts == latest_ts_by_device.c.latest_ts),
            )
            .order_by(GPSPointORM.ts.desc(), GPSPointORM.id.desc())
        )
        return [self._to_schema(record) for record in rows.all()]

    @staticmethod
    def _to_schema(record: GPSPointORM) -> GPSPointOut:
        return GPSPointOut(
            id=record.id,
            device_id=record.device_id,
            lat=record.lat,
            lon=record.lon,
            speed=record.speed,
            heading=record.heading,
            ts=record.ts,
            received_at=record.received_at,
        )


gps_tracking_service = GPSTrackingService()
