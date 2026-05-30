"""
================================================================================
 File: app/services/event_pipeline.py
 Purpose:
   End-to-end message-bus processing for Orca: cleaning, validation,
   enrichment, DB persistence, object-storage handoff, AI scoring, and alert
   emission for dashboard consumers.
================================================================================
"""

from __future__ import annotations

from collections import deque
from datetime import UTC, datetime
from typing import Deque, Iterable
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.topic_config import load_topics
from app.db.models import AuditEventORM, SensorReadingORM
from app.schemas.events import AlertEvent, HistoricalAnalyticsPoint, NormalizedEvent
from app.schemas.sensor import SensorKind, SensorReadingIn, SensorReadingOut
from app.services.ai_client import ai_client
from app.services.cache import CacheKeyBuilder, cache_service
from app.services.kafka_stream import KafkaPublisher
from app.services.object_storage import object_storage_service


class EventPipelineService:
    def __init__(self) -> None:
        self._topics = load_topics()
        self._live_events: Deque[NormalizedEvent] = deque(maxlen=200)
        self._alerts: Deque[AlertEvent] = deque(maxlen=100)
        self._history_cache_limits = (20, 50, 100, 200)

    def normalize_sensor_reading(self, reading: SensorReadingIn) -> NormalizedEvent:
        return NormalizedEvent(
            event_id=str(uuid4()),
            source="iot",
            entity_id=reading.sensor_id,
            event_type="sensor.reading",
            occurred_at=reading.observed_at,
            received_at=datetime.now(UTC),
            payload={
                "kind": reading.kind.value,
                "value": reading.value,
                "unit": reading.unit,
                "latitude": reading.latitude,
                "longitude": reading.longitude,
            },
            metadata={key: value for key, value in reading.metadata.items()},
        )

    def clean_event(self, event: NormalizedEvent) -> NormalizedEvent:
        payload = dict(event.payload)
        if isinstance(payload.get("value"), str):
            payload["value"] = float(payload["value"])
        return event.model_copy(update={"payload": payload})

    def validate_event(self, event: NormalizedEvent) -> NormalizedEvent:
        if event.payload.get("value") is None:
            raise ValueError("Normalized event payload must contain a value")
        return event

    def enrich_event(self, event: NormalizedEvent) -> NormalizedEvent:
        metadata = dict(event.metadata)
        metadata.setdefault(
            "geo_enriched",
            bool(
                event.payload.get("latitude") is not None
                and event.payload.get("longitude") is not None
            ),
        )
        metadata.setdefault("time_bucket", event.occurred_at.strftime("%Y-%m-%dT%H:00:00Z"))
        metadata.setdefault("processed_by", "orcaapi.event_pipeline")
        return event.model_copy(update={"metadata": metadata})

    async def persist_sensor_event(
        self,
        session: AsyncSession,
        *,
        event: NormalizedEvent,
    ) -> SensorReadingOut:
        payload = event.payload
        kind = str(payload.get("kind", SensorKind.OTHER.value))
        kind_enum = SensorKind(kind) if kind in SensorKind._value2member_map_ else SensorKind.OTHER
        record = SensorReadingORM(
            sensor_id=event.entity_id,
            kind=kind_enum.value,
            value=float(payload.get("value", 0.0)),
            unit=str(payload.get("unit", "unknown")),
            latitude=float(payload["latitude"]) if payload.get("latitude") is not None else None,
            longitude=float(payload["longitude"]) if payload.get("longitude") is not None else None,
            observed_at=event.occurred_at,
            extra={"metadata": event.metadata, "event_id": event.event_id},
        )
        session.add(record)
        await session.flush()
        return SensorReadingOut(
            id=record.id,
            sensor_id=record.sensor_id,
            kind=kind_enum,
            value=record.value,
            unit=record.unit,
            latitude=record.latitude,
            longitude=record.longitude,
            observed_at=record.observed_at,
            metadata={key: str(value) for key, value in event.metadata.items()},
            received_at=record.received_at,
        )

    async def store_blob_if_present(self, event: NormalizedEvent) -> str | None:
        blob_text = event.metadata.get("blob_text")
        if not isinstance(blob_text, str) or not blob_text:
            return None
        return await object_storage_service.store_blob(
            data=blob_text.encode("utf-8"), suffix=".txt"
        )

    async def analyze_event(self, event: NormalizedEvent) -> float:
        try:
            return await ai_client.score_anomaly(
                [
                    float(event.payload.get("value", 0.0)),
                    float(event.payload.get("latitude", 0.0) or 0.0),
                    float(event.payload.get("longitude", 0.0) or 0.0),
                ]
            )
        except Exception:  # noqa: BLE001
            return 0.0

    async def emit_pipeline_events(
        self,
        *,
        clean_event: NormalizedEvent,
        anomaly_score: float,
        publisher: KafkaPublisher | None,
    ) -> AlertEvent | None:
        self._live_events.appendleft(clean_event)
        if publisher is not None:
            await publisher.publish_event(
                clean_event.model_dump(mode="json"), topic=self._topics["clean_events"]
            )

        if anomaly_score < 0.8:
            return None

        classification_payload = {
            "category": "general",
            "severity": "high" if anomaly_score >= 0.95 else "medium",
            "confidence": anomaly_score,
            "recommended_action": (
                "Escalate to mission control and request operator acknowledgement."
            ),
            "requires_human_review": True,
        }
        summary = f"Anomaly score {anomaly_score:.2f} for {clean_event.entity_id}"

        try:
            classification_payload = await ai_client.classify_alert(
                message=summary,
                source=clean_event.source,
                tags=[
                    clean_event.event_type,
                    str(clean_event.payload.get("kind", "unknown")),
                    str(clean_event.metadata.get("processed_by", "event-pipeline")),
                ],
                anomaly_score=anomaly_score,
            )
            summary = await ai_client.summarize_event(
                title=f"{str(classification_payload.get('category', 'general')).title()} alert",
                classification=str(classification_payload.get("category", "general")),
                severity=str(classification_payload.get("severity", "medium")),
                location=clean_event.entity_id,
                alerts=[
                    f"Anomaly score {anomaly_score:.2f}",
                    f"Sensor kind {clean_event.payload.get('kind', 'unknown')}",
                ],
                sensor_readings={
                    "value": float(clean_event.payload.get("value", 0.0)),
                },
                max_sentences=2,
            )
        except Exception:  # noqa: BLE001  # nosec B110
            pass

        alert = AlertEvent(
            id=str(uuid4()),
            severity=str(classification_payload.get("severity", "medium")),
            title=f"{str(classification_payload.get('category', 'general')).title()} alert",
            message=summary,
            created_at=datetime.now(UTC),
            payload={
                "event_id": clean_event.event_id,
                "score": anomaly_score,
                "classification": classification_payload,
                "source": clean_event.source,
            },
        )
        self._alerts.appendleft(alert)
        if publisher is not None:
            await publisher.publish_event(
                alert.model_dump(mode="json"), topic=self._topics["alerts"]
            )
        return alert

    async def process_sensor_reading(
        self,
        session: AsyncSession,
        *,
        reading: SensorReadingIn,
        publisher: KafkaPublisher | None,
    ) -> SensorReadingOut:
        raw_event = self.normalize_sensor_reading(reading)
        if publisher is not None:
            await publisher.publish_event(
                raw_event.model_dump(mode="json"), topic=self._topics["raw_events"]
            )

        clean_event = self.enrich_event(self.validate_event(self.clean_event(raw_event)))
        blob_uri = await self.store_blob_if_present(clean_event)
        if blob_uri is not None:
            clean_event = clean_event.model_copy(
                update={"metadata": {**clean_event.metadata, "blob_uri": blob_uri}},
            )

        stored = await self.persist_sensor_event(session, event=clean_event)
        anomaly_score = await self.analyze_event(clean_event)
        session.add(
            AuditEventORM(
                id=str(uuid4()),
                entity_type="ai_inference",
                entity_id=clean_event.entity_id,
                action="ai.inference.completed",
                actor="event-pipeline",
                payload={
                    "event_id": clean_event.event_id,
                    "score": anomaly_score,
                    "topic": self._topics["clean_events"],
                },
            )
        )
        alert = await self.emit_pipeline_events(
            clean_event=clean_event,
            anomaly_score=anomaly_score,
            publisher=publisher,
        )

        if alert is not None:
            session.add(
                AuditEventORM(
                    id=alert.id,
                    entity_type="alert",
                    entity_id=clean_event.entity_id,
                    action="event.alert.emitted",
                    actor="event-pipeline",
                    payload=alert.model_dump(mode="json"),
                )
            )

        await session.commit()
        self._invalidate_history_cache()
        return stored

    def live_events(self, limit: int = 25) -> Iterable[NormalizedEvent]:
        return list(self._live_events)[:limit]

    def alerts(self, limit: int = 25) -> Iterable[AlertEvent]:
        return list(self._alerts)[:limit]

    async def historical_analytics(
        self, session: AsyncSession, limit: int = 20
    ) -> list[HistoricalAnalyticsPoint]:
        cache_key = CacheKeyBuilder.build("api", "historical-analytics", f"history-{limit}")
        cached = cache_service.get_json(cache_key)
        if cached is not None:
            return [HistoricalAnalyticsPoint.model_validate(item) for item in cached]

        stmt = (
            select(
                SensorReadingORM.sensor_id,
                func.count(SensorReadingORM.id),
                func.avg(SensorReadingORM.value),
                func.max(SensorReadingORM.observed_at),
            )
            .group_by(SensorReadingORM.sensor_id)
            .order_by(func.max(SensorReadingORM.observed_at).desc())
            .limit(limit)
        )
        rows = (await session.execute(stmt)).all()
        points = [
            HistoricalAnalyticsPoint(
                sensor_id=sensor_id,
                samples=int(samples),
                average_value=float(average_value),
                latest_observed_at=latest_observed_at,
            )
            for sensor_id, samples, average_value, latest_observed_at in rows
        ]
        cache_service.set_json(
            cache_key,
            [point.model_dump(mode="json") for point in points],
            cache_service.policies.api,
        )
        return points

    def _invalidate_history_cache(self) -> None:
        cache_service.delete_many(
            [
                CacheKeyBuilder.build("api", "historical-analytics", f"history-{limit}")
                for limit in self._history_cache_limits
            ]
        )


event_pipeline_service = EventPipelineService()
