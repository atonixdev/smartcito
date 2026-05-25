"""
================================================================================
 File: citosmart/app/api/v1/endpoints/sensors.py
 Purpose:
   CRUD-lite endpoints for generic IoT sensor ingestion and retrieval.
   This is the most-used path on the platform; keep it tiny, well-typed,
   and well-tested.

 Endpoints:
   POST /api/v1/sensors        Ingest one reading.        (operator+)
   GET  /api/v1/sensors/recent List the most recent N.    (viewer+)
================================================================================
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_role
from app.db.session import get_session
from app.schemas.sensor import SensorReadingIn, SensorReadingOut
from app.services.cache import CacheKeyBuilder, cache_service
from app.services.event_pipeline import event_pipeline_service
from app.services.ingestion import ingestion_service

logger = logging.getLogger(__name__)
router = APIRouter()
RECENT_SENSOR_CACHE_LIMITS = (10, 50, 100, 500)


def _recent_cache_key(limit: int) -> str:
    return CacheKeyBuilder.build("api", "sensor-readings", f"recent-{limit}")


def _invalidate_recent_sensor_cache(limit: int) -> None:
    candidate_limits = set(RECENT_SENSOR_CACHE_LIMITS)
    candidate_limits.add(limit)
    cache_service.delete_many([_recent_cache_key(candidate_limit) for candidate_limit in sorted(candidate_limits)])


@router.post(
    "",
    response_model=SensorReadingOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("operator"))],
    summary="Ingest a single sensor reading",
)
async def ingest_reading(
    reading: SensorReadingIn,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> SensorReadingOut:
    """Validate the reading, store it, and (best-effort) publish to Kafka.

    The Kafka publisher is only attached to `app.state.kafka` when the
    `KAFKA_PUBLISHER_ENABLED` flag is on AND the broker accepted the
    connection at startup. Failures here are logged but do NOT fail the
    request — the canonical record is the local store.
    """
    record = ingestion_service.ingest(reading)
    kafka = getattr(request.app.state, "kafka", None)
    try:
        response = await event_pipeline_service.process_sensor_reading(
            session,
            reading=reading,
            publisher=kafka,
        )
        _invalidate_recent_sensor_cache(limit=50)
        return response
    except Exception as exc:  # noqa: BLE001
        logger.warning("Event pipeline failed for %s: %s", record.sensor_id, exc)
        if kafka is not None:
            try:
                await kafka.publish_reading(record)
            except Exception as kafka_exc:  # noqa: BLE001
                logger.warning("Kafka publish failed for %s: %s", record.sensor_id, kafka_exc)
        _invalidate_recent_sensor_cache(limit=50)
        return record


@router.get(
    "/recent",
    response_model=list[SensorReadingOut],
    dependencies=[Depends(require_role("viewer"))],
    summary="List the most recent sensor readings",
)
async def list_recent(
    limit: int = Query(50, ge=1, le=500, description="Max number of readings"),
) -> list[SensorReadingOut]:
    """Return the latest `limit` readings, newest last."""
    cache_key = _recent_cache_key(limit)
    cached = cache_service.get_json(cache_key)
    if cached is not None:
        return [SensorReadingOut.model_validate(item) for item in cached]

    readings = list(ingestion_service.recent(limit=limit))
    cache_service.set_json(
        cache_key,
        [reading.model_dump(mode="json") for reading in readings],
        cache_service.policies.api,
    )
    return readings
