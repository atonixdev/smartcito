"""
================================================================================
 File: surveillance/kafka.py
 Purpose:
   Small Kafka publishing adapter used by surveillance microservices. It keeps
   local development deterministic when Kafka is not running and publishes to
   kafka-python in deployed environments.
================================================================================
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any

from surveillance.models import NormalizedEvent, PublishResult


def _kafka_enabled() -> bool:
    return os.getenv("ORCA_KAFKA_ENABLED", "1").lower() not in {"0", "false", "no"}


class KafkaPublisher:
    def __init__(self, bootstrap_servers: str | None = None) -> None:
        self.bootstrap_servers = bootstrap_servers or os.getenv("KAFKA_BROKER_URL", "kafka:9092")
        self._producer: Any | None = None
        self._available = _kafka_enabled()

    def _load_producer(self) -> Any | None:
        if not self._available:
            return None
        if self._producer is not None:
            return self._producer
        try:
            from kafka import KafkaProducer
        except ModuleNotFoundError:
            self._available = False
            return None

        self._producer = KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            key_serializer=lambda value: value.encode("utf-8"),
            value_serializer=lambda value: json.dumps(value, default=str).encode("utf-8"),
            linger_ms=10,
        )
        return self._producer

    def publish(self, *, topic: str, key: str, payload: dict[str, Any]) -> PublishResult:
        producer = self._load_producer()
        if producer is None:
            return PublishResult(topic=topic, key=key, published=False, status="kafka-unavailable")

        try:
            producer.send(topic, key=key, value=payload)
            producer.flush(timeout=2)
        except Exception as exc:  # pragma: no cover - depends on external broker availability
            return PublishResult(topic=topic, key=key, published=False, status=f"publish-failed:{exc.__class__.__name__}")

        return PublishResult(topic=topic, key=key, published=True, status="published")

    def publish_event(self, event: NormalizedEvent) -> PublishResult:
        return self.publish(topic=event.topic, key=event.entity_id, payload=event.model_dump(mode="json"))


@lru_cache(maxsize=1)
def get_publisher() -> KafkaPublisher:
    return KafkaPublisher()
