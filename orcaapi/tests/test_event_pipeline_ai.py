from __future__ import annotations

import asyncio

from app.schemas.events import NormalizedEvent
from app.services.event_pipeline import EventPipelineService
from app.services import event_pipeline as event_pipeline_module


def test_emit_pipeline_events_enriches_alert_with_ai(monkeypatch) -> None:
    async def fake_classify_alert(**kwargs) -> dict[str, object]:
        assert kwargs["anomaly_score"] == 0.91
        return {
            "category": "intrusion",
            "severity": "high",
            "confidence": 0.91,
            "recommended_action": (
                "Lock the affected perimeter zone and route live video to an "
                "operator."
            ),
            "requires_human_review": True,
        }

    async def fake_summarize_event(**kwargs) -> str:
        assert kwargs["classification"] == "intrusion"
        return (
            "Intrusion alert at gate-7. Primary signals: Anomaly score 0.91; "
            "Sensor kind motion."
        )

    monkeypatch.setattr(event_pipeline_module.ai_client, "classify_alert", fake_classify_alert)
    monkeypatch.setattr(event_pipeline_module.ai_client, "summarize_event", fake_summarize_event)

    service = EventPipelineService()
    event = NormalizedEvent(
        event_id="evt-1",
        source="camera",
        entity_id="gate-7",
        event_type="sensor.reading",
        occurred_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
        received_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
        payload={"kind": "motion", "value": 12.0},
        metadata={"processed_by": "test"},
    )

    alert = asyncio.run(
        service.emit_pipeline_events(clean_event=event, anomaly_score=0.91, publisher=None)
    )

    assert alert is not None
    assert alert.severity == "high"
    assert alert.title == "Intrusion alert"
    assert "Intrusion alert at gate-7" in alert.message
    assert alert.payload["classification"]["category"] == "intrusion"


def test_emit_pipeline_events_skips_low_scores() -> None:
    service = EventPipelineService()
    event = NormalizedEvent(
        event_id="evt-2",
        source="iot",
        entity_id="sensor-2",
        event_type="sensor.reading",
        occurred_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
        received_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
        payload={"kind": "traffic", "value": 3.0},
        metadata={},
    )

    alert = asyncio.run(
        service.emit_pipeline_events(clean_event=event, anomaly_score=0.42, publisher=None)
    )

    assert alert is None
