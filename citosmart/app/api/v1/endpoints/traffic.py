"""
================================================================================
 File: backend/app/api/v1/endpoints/traffic.py
 Purpose:
   Domain-specific traffic endpoint that derives a real-time summary
   (per-intersection vehicle counts, average speed proxy) from the
   ingestion buffer. Demonstrates how to layer a domain view on top of
   raw sensor data without polluting the core ingestion service.
================================================================================
"""

from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.security import require_role
from app.schemas.sensor import SensorKind
from app.services.ingestion import ingestion_service

router = APIRouter()


class TrafficSummaryItem(BaseModel):
    """Aggregated reading for one traffic sensor."""

    sensor_id: str
    samples: int
    average_value: float
    unit: str


class TrafficSummary(BaseModel):
    """Top-level summary response."""

    total_samples: int
    sensors: list[TrafficSummaryItem]


@router.get(
    "/summary",
    response_model=TrafficSummary,
    dependencies=[Depends(require_role("viewer"))],
    summary="Aggregate recent traffic readings per sensor",
)
async def traffic_summary() -> TrafficSummary:
    """Compute a quick summary from the in-memory ingestion buffer.

    For production, this should run against a streaming engine (Spark
    Structured Streaming or Flink) and read from a materialized view.
    """
    by_sensor: dict[str, list[float]] = defaultdict(list)
    units: dict[str, str] = {}

    for reading in ingestion_service.recent(limit=500):
        if reading.kind is not SensorKind.TRAFFIC:
            continue
        by_sensor[reading.sensor_id].append(reading.value)
        units[reading.sensor_id] = reading.unit

    items = [
        TrafficSummaryItem(
            sensor_id=sid,
            samples=len(values),
            average_value=sum(values) / len(values),
            unit=units.get(sid, ""),
        )
        for sid, values in by_sensor.items()
    ]
    return TrafficSummary(total_samples=sum(i.samples for i in items), sensors=items)
