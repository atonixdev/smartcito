"""
================================================================================
 File: backend/app/services/kafka_stream.py
 Purpose:
   Thin async wrappers around aiokafka for publishing and consuming sensor
   events on the SmartCito event bus.

   - `KafkaPublisher` is used by the API and the MQTT bridge to fan out
     readings to downstream consumers (analytics, dashboards, archives).
   - `consume_sensor_stream()` is a generic async iterator used by workers
     such as the analytics service.

 Topic naming convention:
     smartcito.<domain>.<stage>
     e.g. smartcito.sensors.raw   smartcito.sensors.enriched

 Notes:
   - We deliberately keep this module small. Anything that smells like
     "business logic" should live in `app/services/analytics.py` instead.
================================================================================
"""

from __future__ import annotations

import json
import logging
from typing import AsyncIterator

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from app.core.config import get_settings
from app.schemas.sensor import SensorReadingIn, SensorReadingOut

logger = logging.getLogger(__name__)


class KafkaPublisher:
    """Lazily-initialized async Kafka producer.

    Usage:
        publisher = KafkaPublisher()
        await publisher.start()
        await publisher.publish_reading(reading)
        await publisher.stop()
    """

    def __init__(self, topic: str | None = None) -> None:
        settings = get_settings()
        self._topic = topic or settings.kafka_sensor_topic
        self._bootstrap = settings.kafka_bootstrap_servers
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        if self._producer is not None:
            return
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._bootstrap,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            enable_idempotence=True,  # exactly-once semantics within a session
        )
        await self._producer.start()
        logger.info("KafkaPublisher started → %s [topic=%s]", self._bootstrap, self._topic)

    async def stop(self) -> None:
        if self._producer is None:
            return
        await self._producer.stop()
        self._producer = None
        logger.info("KafkaPublisher stopped")

    async def publish_reading(self, reading: SensorReadingIn | SensorReadingOut) -> None:
        """Send one reading to the configured topic.

        Partitioning is by `sensor_id` so all events from one device land on
        the same partition (preserves per-sensor ordering for analytics).
        """
        if self._producer is None:
            raise RuntimeError("KafkaPublisher.start() must be called first")
        key = reading.sensor_id.encode("utf-8")
        await self._producer.send_and_wait(self._topic, reading.model_dump(), key=key)


async def consume_sensor_stream(
    group_id: str,
    topic: str | None = None,
) -> AsyncIterator[SensorReadingIn]:
    """Yield validated `SensorReadingIn` objects from a Kafka topic.

    Cleanly handles shutdown via `async for` cancellation. Skips malformed
    messages with a warning rather than crashing the consumer.
    """
    settings = get_settings()
    consumer = AIOKafkaConsumer(
        topic or settings.kafka_sensor_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=group_id,
        enable_auto_commit=True,
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
        auto_offset_reset="latest",
    )
    await consumer.start()
    logger.info("Kafka consumer group=%s started", group_id)
    try:
        async for msg in consumer:
            try:
                yield SensorReadingIn.model_validate(msg.value)
            except ValueError as exc:
                logger.warning("Skipping invalid Kafka message: %s", exc)
    finally:
        await consumer.stop()
        logger.info("Kafka consumer group=%s stopped", group_id)
