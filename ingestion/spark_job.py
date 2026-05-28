"""Declarative metadata for the Orca Spark streaming job."""

from __future__ import annotations

import os


def build_stream_description() -> dict[str, object]:
    """Return the intended Spark pipeline contract for operators and tests."""
    return {
        "source": "kafka",
        "input_topic": os.getenv("KAFKA_RAW_EVENTS_TOPIC", "orca.sensors.raw"),
        "cache_backend": "memcached",
        "cache_servers": os.getenv("MEMCACHED_SERVERS", "memcached-1:11211,memcached-2:11211,memcached-3:11211").split(","),
        "transformations": [
            "parse-json",
            "validate-schema",
            "enrich-location",
            "cache-device-metadata",
            "route-alerts",
        ],
        "sinks": ["postgres", "object-storage", "kafka-alerts", "memcached-metadata"],
        "alerts_topic": os.getenv("KAFKA_ALERTS_TOPIC", "orca.alerts"),
        "checkpoint_dir": os.getenv("SPARK_CHECKPOINT_DIR", "/opt/spark/checkpoints"),
    }


if __name__ == "__main__":
    print(build_stream_description())
