"""
================================================================================
 File: backend/app/api/v1/endpoints/sensors.py
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

from app.core.security import require_role
from app.schemas.sensor import SensorReadingIn, SensorReadingOut
from app.services.ingestion import ingestion_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "",
    response_model=SensorReadingOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("operator"))],
    summary="Ingest a single sensor reading",
)
async def ingest_reading(reading: SensorReadingIn, request: Request) -> SensorReadingOut:
    """Validate the reading, store it, and (best-effort) publish to Kafka.

    The Kafka publisher is only attached to `app.state.kafka` when the
    `KAFKA_PUBLISHER_ENABLED` flag is on AND the broker accepted the
    connection at startup. Failures here are logged but do NOT fail the
    request — the canonical record is the local store.
    """
    record = ingestion_service.ingest(reading)
    kafka = getattr(request.app.state, "kafka", None)
    if kafka is not None:
        try:
            await kafka.publish_reading(record)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Kafka publish failed for %s: %s", record.sensor_id, exc)
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
    return list(ingestion_service.recent(limit=limit))
