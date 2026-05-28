"""
================================================================================
 File: surveillance/threat_detection_service.py
 Purpose:
   Threat Detection and Intelligence Service. It converts AI detections, sensor
   alerts, GPS context, and geofence criticality into operator alerts.
================================================================================
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

from surveillance.geospatial import resolve_zone
from surveillance.kafka import get_publisher
from surveillance.models import AIDetection, NormalizedEvent, PublishEnvelope, ThreatAlert, ThreatLevel
from surveillance.topics import DRONE_CAMERA_ALERTS_TOPIC, THREAT_ALERTS_TOPIC


load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

app = FastAPI(title="Orca Threat Detection Service")
_alerts: dict[str, ThreatAlert] = {}


class CorrelationRequest(BaseModel):
    detections: list[AIDetection] = Field(..., min_length=1, max_length=50)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "threat-detection"}


@app.get("/ready")
async def ready() -> dict[str, object]:
    return {
        "service": "threat-detection",
        "models": ["object-detection", "motion-detection", "perimeter-breach", "crowd-density"],
        "topics": {"threats": THREAT_ALERTS_TOPIC, "camera_alerts": DRONE_CAMERA_ALERTS_TOPIC},
    }


def classify_detection(detection: AIDetection) -> ThreatLevel:
    zone = resolve_zone(detection.position)
    label = detection.label.lower()
    if detection.confidence >= 0.92 and ("weapon" in label or zone["criticality"] == "critical"):
        return ThreatLevel.CRITICAL
    if detection.confidence >= 0.82 or "intrusion" in label or "breach" in label:
        return ThreatLevel.HIGH
    if detection.confidence >= 0.62 or "motion" in label or "crowd" in label:
        return ThreatLevel.MEDIUM
    return ThreatLevel.LOW


def build_alert(detections: list[AIDetection]) -> ThreatAlert:
    primary = max(detections, key=lambda item: item.confidence)
    threat_level = max((classify_detection(item) for item in detections), key=lambda level: list(ThreatLevel).index(level))
    zone = resolve_zone(primary.position)
    recommended_actions = ["notify-operator", "start-recording"]
    if threat_level in {ThreatLevel.HIGH, ThreatLevel.CRITICAL}:
        recommended_actions.extend(["dispatch-nearest-drone", "raise-alarm"])
    if threat_level == ThreatLevel.CRITICAL:
        recommended_actions.append("lock-critical-geofence")

    return ThreatAlert(
        threat_level=threat_level,
        title=f"{threat_level.value.title()} surveillance event: {primary.label}",
        source_ids=sorted({detection.source_id for detection in detections}),
        position=primary.position,
        zone=str(zone["zone_id"] or primary.zone or "unknown"),
        confidence=max(detection.confidence for detection in detections),
        recommended_actions=recommended_actions,
    )


@app.post("/detections", response_model=PublishEnvelope)
async def analyze_detection(detection: AIDetection) -> PublishEnvelope:
    alert = build_alert([detection])
    _alerts[alert.alert_id] = alert
    event = NormalizedEvent(
        event_type="threat.detected",
        source="threat-detection",
        entity_id=alert.alert_id,
        topic=THREAT_ALERTS_TOPIC,
        payload=alert.model_dump(mode="json"),
    )
    return PublishEnvelope(event=event, publish=get_publisher().publish_event(event))


@app.post("/correlate", response_model=PublishEnvelope)
async def correlate(request: CorrelationRequest) -> PublishEnvelope:
    alert = build_alert(request.detections)
    _alerts[alert.alert_id] = alert
    event = NormalizedEvent(
        event_type="threat.correlated",
        source="threat-detection",
        entity_id=alert.alert_id,
        topic=THREAT_ALERTS_TOPIC,
        payload=alert.model_dump(mode="json"),
    )
    return PublishEnvelope(event=event, publish=get_publisher().publish_event(event))


@app.get("/alerts")
async def list_alerts() -> dict[str, list[dict[str, object]]]:
    return {"alerts": [alert.model_dump(mode="json") for alert in _alerts.values()]}
