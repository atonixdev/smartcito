"""
================================================================================
 File: ingestion/pipeline.py
 Purpose:
   Normalize camera, GPS, IoT, and external API payloads into a common event
   format for publishing onto the message bus.
================================================================================
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class EventSource(str, Enum):
    CAMERA = "camera"
    DRONE = "drone"
    GPS = "gps"
    IOT = "iot"
    OPERATOR = "operator"
    ROBOT = "robot"
    SENSOR = "sensor"
    GEOGRAPHIC = "geographic"
    EXTERNAL_API = "external_api"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def build_normalized_event(
    *,
    source: EventSource,
    entity_id: str,
    event_type: str,
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "event_id": str(uuid4()),
        "source": source.value,
        "entity_id": entity_id,
        "event_type": event_type,
        "occurred_at": payload.get("occurred_at") or _now(),
        "received_at": _now(),
        "payload": payload,
        "metadata": metadata or {},
    }


def normalize_camera_payload(device_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return build_normalized_event(
        source=EventSource.CAMERA,
        entity_id=device_id,
        event_type="camera.frame.metadata",
        payload=payload,
        metadata={"format": "json", "connector": "rtsp/onvif"},
    )


def normalize_drone_payload(device_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return build_normalized_event(
        source=EventSource.DRONE,
        entity_id=device_id,
        event_type="drone.telemetry",
        payload=payload,
        metadata={"format": "json", "connector": "drone-gateway"},
    )


def normalize_gps_payload(device_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return build_normalized_event(
        source=EventSource.GPS,
        entity_id=device_id,
        event_type="gps.position",
        payload=payload,
        metadata={"format": "json", "connector": "nmea"},
    )


def normalize_iot_payload(device_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return build_normalized_event(
        source=EventSource.IOT,
        entity_id=device_id,
        event_type="iot.telemetry",
        payload=payload,
        metadata={"format": "json", "connector": "mqtt"},
    )


def normalize_robot_payload(device_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return build_normalized_event(
        source=EventSource.ROBOT,
        entity_id=device_id,
        event_type="robot.navigation",
        payload=payload,
        metadata={"format": "json", "connector": "robot-gateway"},
    )


def normalize_sensor_payload(device_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return build_normalized_event(
        source=EventSource.SENSOR,
        entity_id=device_id,
        event_type="sensor.reading",
        payload=payload,
        metadata={"format": "json", "connector": "sensor-bus"},
    )


def normalize_geographic_payload(engine_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return build_normalized_event(
        source=EventSource.GEOGRAPHIC,
        entity_id=engine_id,
        event_type="geographic.reasoning",
        payload=payload,
        metadata={"format": "json", "connector": "geo-engine"},
    )


def normalize_operator_action(operator_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return build_normalized_event(
        source=EventSource.OPERATOR,
        entity_id=operator_id,
        event_type="operator.decision",
        payload=payload,
        metadata={"format": "json", "connector": "dashboard"},
    )


def normalize_external_api_payload(source_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    return build_normalized_event(
        source=EventSource.EXTERNAL_API,
        entity_id=source_name,
        event_type="external.api.event",
        payload=payload,
        metadata={"format": "json", "connector": "rest"},
    )