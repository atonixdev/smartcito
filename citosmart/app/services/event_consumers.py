"""
================================================================================
 File: app/services/event_consumers.py
 Purpose:
   Explicit backend consumers for raw_events, clean_events, and alerts topics.
   These workers apply cleaning/validation/enrichment, persist analytics and AI
   results, and keep the service-side event flow codified outside the API path.
================================================================================
"""

from __future__ import annotations

import json
import logging

from aiokafka import AIOKafkaConsumer

from app.core.config import get_settings
from app.core.topic_config import load_topics
from app.db.models import AuditEventORM
from app.db.session import AsyncSessionLocal
from app.schemas.events import AlertEvent, NormalizedEvent
from app.schemas.sensor import SensorKind, SensorReadingIn
from app.services.event_pipeline import event_pipeline_service
from app.services.kafka_stream import KafkaPublisher

logger = logging.getLogger(__name__)


async def _consumer(topic: str, group_id: str) -> AIOKafkaConsumer:
    settings = get_settings()
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=group_id,
        enable_auto_commit=True,
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
        auto_offset_reset="latest",
    )
    await consumer.start()
    return consumer


async def consume_raw_events() -> None:
    topics = load_topics()
    consumer = await _consumer(topics["raw_events"], "orca-raw-events")
    publisher = KafkaPublisher()
    await publisher.start()
    try:
        async for message in consumer:
            event = NormalizedEvent.model_validate(message.value)
            payload = event.payload
            reading = SensorReadingIn(
                sensor_id=event.entity_id,
                kind=SensorKind(str(payload.get("kind", SensorKind.OTHER.value))),
                value=float(payload.get("value", 0.0)),
                unit=str(payload.get("unit", "unknown")),
                latitude=float(payload["latitude"]) if payload.get("latitude") is not None else None,
                longitude=float(payload["longitude"]) if payload.get("longitude") is not None else None,
                observed_at=event.occurred_at,
                metadata={key: str(value) for key, value in event.metadata.items()},
            )
            async with AsyncSessionLocal() as session:
                await event_pipeline_service.process_sensor_reading(session, reading=reading, publisher=publisher)
    finally:
        await publisher.stop()
        await consumer.stop()


async def consume_clean_events() -> None:
    topics = load_topics()
    consumer = await _consumer(topics["clean_events"], "orca-clean-events")
    try:
        async for message in consumer:
            event = NormalizedEvent.model_validate(message.value)
            async with AsyncSessionLocal() as session:
                session.add(
                    AuditEventORM(
                        id=event.event_id,
                        entity_type="clean_event",
                        entity_id=event.entity_id,
                        action="event.clean.consumed",
                        actor="clean-event-consumer",
                        payload=event.model_dump(mode="json"),
                    )
                )
                await session.commit()
    finally:
        await consumer.stop()


async def consume_alerts() -> None:
    topics = load_topics()
    consumer = await _consumer(topics["alerts"], "orca-alerts")
    try:
        async for message in consumer:
            alert = AlertEvent.model_validate(message.value)
            async with AsyncSessionLocal() as session:
                session.add(
                    AuditEventORM(
                        id=alert.id,
                        entity_type="alert",
                        entity_id=alert.id,
                        action="event.alert.consumed",
                        actor="alert-consumer",
                        payload=alert.model_dump(mode="json"),
                    )
                )
                await session.commit()
    finally:
        await consumer.stop()