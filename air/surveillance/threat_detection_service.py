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

try:
    from surveillance.geospatial import resolve_zone
except ModuleNotFoundError:
    def resolve_zone(_position):  # type: ignore[no-redef]
        return {
            "zone_id": "zone-unknown",
            "zone_name": "Fallback Zone",
            "zone_type": "geofence",
            "criticality": "medium",
            "contains": True,
            "distance_to_boundary_m": None,
            "point": None,
        }
from surveillance.kafka import get_publisher
from surveillance.models import AIDetection, NormalizedEvent, PublishEnvelope, ThreatAlert, ThreatLevel
from surveillance.topics import DRONE_CAMERA_ALERTS_TOPIC, THREAT_ALERTS_TOPIC


load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

app = FastAPI(title="Orca Threat Detection Service")
_alerts: dict[str, ThreatAlert] = {}


class CorrelationRequest(BaseModel):
    detections: list[AIDetection] = Field(..., min_length=1, max_length=50)


class SurveillanceEscalationRequest(BaseModel):
    robot_id: str = Field(..., min_length=2, max_length=80)
    threat_detection: dict[str, object]
    perception: dict[str, object] = Field(default_factory=dict)
    reaction: dict[str, object] = Field(default_factory=dict)


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


def build_alert_from_surveillance_cycle(request_payload: SurveillanceEscalationRequest) -> ThreatAlert:
    threat_level_raw = str(request_payload.threat_detection.get("level", "low")).lower()
    try:
        threat_level = ThreatLevel(threat_level_raw)
    except ValueError:
        threat_level = ThreatLevel.LOW

    detected = request_payload.threat_detection.get("detected", {})
    detected_labels = [key for key, value in detected.items() if bool(value)] if isinstance(detected, dict) else []
    primary_label = ", ".join(detected_labels) if detected_labels else "unknown-threat"

    recommended_actions = ["notify-operator", "start-recording"]
    if threat_level in {ThreatLevel.MEDIUM, ThreatLevel.HIGH, ThreatLevel.CRITICAL}:
        recommended_actions.append("dispatch-nearest-robot")
    if threat_level in {ThreatLevel.HIGH, ThreatLevel.CRITICAL}:
        recommended_actions.extend(["dispatch-nearest-drone", "raise-alarm"])
    if threat_level == ThreatLevel.CRITICAL:
        recommended_actions.append("lock-critical-geofence")

    confidence_raw = request_payload.threat_detection.get("threat_score", 0.0)
    confidence = float(confidence_raw) if isinstance(confidence_raw, (int, float)) else 0.0
    confidence = min(max(confidence, 0.0), 1.0)

    return ThreatAlert(
        threat_level=threat_level,
        title=f"{threat_level.value.title()} surveillance cycle escalation: {primary_label}",
        source_ids=[request_payload.robot_id],
        position=None,
        zone="cycle-derived",
        confidence=confidence,
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


@app.post("/surveillance/escalate", response_model=PublishEnvelope)
async def escalate_from_surveillance(request_payload: SurveillanceEscalationRequest) -> PublishEnvelope:
    alert = build_alert_from_surveillance_cycle(request_payload)
    _alerts[alert.alert_id] = alert
    event = NormalizedEvent(
        event_type="threat.surveillance.escalated",
        source="threat-detection",
        entity_id=alert.alert_id,
        topic=THREAT_ALERTS_TOPIC,
        payload={
            **alert.model_dump(mode="json"),
            "robot_id": request_payload.robot_id,
            "reaction": request_payload.reaction,
            "perception": request_payload.perception,
        },
    )
    return PublishEnvelope(event=event, publish=get_publisher().publish_event(event))


@app.get("/alerts")
async def list_alerts() -> dict[str, list[dict[str, object]]]:
    return {"alerts": [alert.model_dump(mode="json") for alert in _alerts.values()]}
