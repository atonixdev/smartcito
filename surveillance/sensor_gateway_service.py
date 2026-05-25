"""
================================================================================
 File: surveillance/sensor_gateway_service.py
 Purpose:
   Sensor Gateway Service for fixed and mobile IoT sensors. It accepts readings
   from MQTT bridges, HTTP devices, TCP adapters, LoRaWAN gateways, and vendor
   APIs, then normalizes them for Kafka and downstream analytics.
================================================================================
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field
from smartcito_shared.crypto import build_secure_envelope

from surveillance.geospatial import normalize_point, resolve_zone
from surveillance.kafka import get_publisher
from surveillance.models import NormalizedEvent, PublishEnvelope, SensorReading
from surveillance.topics import SENSOR_ALERTS_TOPIC, SENSOR_READINGS_TOPIC


load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

app = FastAPI(title="SmartCito Sensor Gateway Service")
_latest_readings: dict[str, SensorReading] = {}


class SensorBatch(BaseModel):
    readings: list[SensorReading] = Field(..., min_length=1, max_length=500)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "sensor-gateway"}


@app.get("/ready")
async def ready() -> dict[str, object]:
    return {
        "service": "sensor-gateway",
        "protocols": ["mqtt", "http", "tcp", "lorawan", "vendor-api"],
        "topics": {"readings": SENSOR_READINGS_TOPIC, "alerts": SENSOR_ALERTS_TOPIC},
    }


@app.post("/readings", response_model=PublishEnvelope)
async def ingest_reading(reading: SensorReading) -> PublishEnvelope:
    _latest_readings[reading.device_id] = reading
    topic = SENSOR_ALERTS_TOPIC if reading.alert else SENSOR_READINGS_TOPIC
    normalized = normalize_point(reading.position)
    normalized_position = normalized["position"] or reading.position
    reading_payload = {
        **reading.model_dump(mode="json"),
        "position": normalized_position.model_dump(mode="json"),
        "coordinate_system": normalized["coordinate_system"],
        "map_projection": normalized["map_projection"],
        "projected_position": normalized["projected"],
        "zone": resolve_zone(normalized_position),
    }
    event = NormalizedEvent(
        event_type="sensor.alert" if reading.alert else "sensor.reading",
        source="sensor-gateway",
        entity_id=reading.device_id,
        timestamp=reading.timestamp,
        topic=topic,
        payload={
            **reading_payload,
            "security": build_secure_envelope(reading_payload, purpose="sensor-reading", signer_id=reading.device_id, associated=reading.device_id),
        },
    )
    return PublishEnvelope(event=event, publish=get_publisher().publish_event(event))


@app.post("/readings/batch")
async def ingest_batch(batch: SensorBatch) -> dict[str, object]:
    envelopes = [await ingest_reading(reading) for reading in batch.readings]
    return {
        "accepted": len(envelopes),
        "published": sum(1 for envelope in envelopes if envelope.publish.published),
        "topics": sorted({envelope.event.topic for envelope in envelopes}),
    }


@app.get("/readings/latest")
async def latest_readings() -> dict[str, list[dict[str, object]]]:
    return {"readings": [reading.model_dump(mode="json") for reading in _latest_readings.values()]}
