"""
================================================================================
 File: backend/app/services/ingestion.py
 Purpose:
   In-memory ingestion buffer used during the pilot phase. This service
   intentionally hides storage details behind a small interface so we can
   later swap it for Kafka + HBase without touching API handlers.

 Replace-with-real-implementation checklist:
   1. Persist readings to PostgreSQL / HBase.
   2. Publish them to a Kafka topic for stream processors.
   3. Emit Prometheus counters for ingestion rate.
================================================================================
"""

from __future__ import annotations

from collections import deque
from typing import Deque, Iterable

from app.schemas.sensor import SensorReadingIn, SensorReadingOut


class InMemoryIngestionService:
    """Bounded ring-buffer of recent sensor readings.

    NOT for production — this is a thread-unsafe demo store sized to keep
    `docker compose up` lightweight. It is a deliberate seam: production
    implementations should implement the same `ingest`/`recent` surface.
    """

    def __init__(self, maxlen: int = 1000) -> None:
        self._buffer: Deque[SensorReadingOut] = deque(maxlen=maxlen)

    def ingest(self, reading: SensorReadingIn) -> SensorReadingOut:
        """Accept and store a single reading, returning the enriched record."""
        record = SensorReadingOut(**reading.model_dump())
        self._buffer.append(record)
        return record

    def recent(self, limit: int = 100) -> Iterable[SensorReadingOut]:
        """Return the most recent `limit` readings (newest last)."""
        if limit <= 0:
            return []
        # deque slicing requires conversion; cheap for small buffers.
        return list(self._buffer)[-limit:]


# Module-level singleton for the demo. Real deployments should inject this
# via FastAPI's dependency system instead of a module global.
ingestion_service = InMemoryIngestionService()
