"""
================================================================================
 File: ingestion/kafka_producer.py
 Purpose:
   Small JSON producer helper for SmartCito ingestion experiments.
================================================================================
"""

from __future__ import annotations

import json
from typing import Any

from kafka import KafkaProducer


class JsonProducer:
    """Kafka JSON producer wrapper with a tiny publish surface."""

    def __init__(self, bootstrap_servers: str, topic: str) -> None:
        self._producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        )
        self._topic = topic

    def publish(self, payload: dict[str, Any]) -> None:
        self._producer.send(self._topic, payload)
        self._producer.flush()
