"""Shared data schema for the Orca Keras stack."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _as_float(payload: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = payload.get(key, default)
    if value is None:
        return default
    return float(value)


@dataclass(slots=True)
class GPSPoint:
    latitude: float
    longitude: float
    altitude: float = 0.0
    speed: float = 0.0
    heading: float = 0.0
    acceleration: float = 0.0
    timestamp: float = 0.0

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "GPSPoint":
        return cls(
            latitude=_as_float(payload, "latitude"),
            longitude=_as_float(payload, "longitude"),
            altitude=_as_float(payload, "altitude"),
            speed=_as_float(payload, "speed"),
            heading=_as_float(payload, "heading"),
            acceleration=_as_float(payload, "acceleration"),
            timestamp=_as_float(payload, "timestamp"),
        )


@dataclass(slots=True)
class SensorReading:
    name: str
    value: float

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "SensorReading":
        return cls(name=str(payload.get("name") or "sensor"), value=float(payload.get("value") or 0.0))


@dataclass(slots=True)
class VisionFrame:
    image_path: str
    timestamp: float = 0.0
    camera_id: str | None = None

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "VisionFrame":
        return cls(
            image_path=str(payload.get("image_path") or "").strip(),
            timestamp=_as_float(payload, "timestamp"),
            camera_id=str(payload.get("camera_id") or "").strip() or None,
        )


@dataclass(slots=True)
class SequenceClassificationExample:
    sequence: list[GPSPoint]
    label: str | int
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "SequenceClassificationExample":
        sequence = [GPSPoint.from_mapping(item) for item in payload.get("sequence", []) if isinstance(item, dict)]
        return cls(sequence=sequence, label=payload.get("label", 0), metadata=dict(payload.get("metadata") or {}))


@dataclass(slots=True)
class TrajectoryExample:
    past_sequence: list[GPSPoint]
    future_sequence: list[GPSPoint]
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "TrajectoryExample":
        past_sequence = [GPSPoint.from_mapping(item) for item in payload.get("past_sequence", []) if isinstance(item, dict)]
        future_sequence = [GPSPoint.from_mapping(item) for item in payload.get("future_sequence", []) if isinstance(item, dict)]
        return cls(past_sequence=past_sequence, future_sequence=future_sequence, metadata=dict(payload.get("metadata") or {}))


@dataclass(slots=True)
class VisionClassificationExample:
    image_path: str
    label: str | int
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "VisionClassificationExample":
        return cls(
            image_path=str(payload.get("image_path") or "").strip(),
            label=payload.get("label", 0),
            metadata=dict(payload.get("metadata") or {}),
        )


@dataclass(slots=True)
class SensorFusionExample:
    gps_sequence: list[GPSPoint]
    image_path: str | None
    metadata: dict[str, Any]
    label: float | int
    gps_embedding: list[float] | None = None
    vision_embedding: list[float] | None = None

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "SensorFusionExample":
        gps_sequence = [GPSPoint.from_mapping(item) for item in payload.get("gps_sequence", []) if isinstance(item, dict)]
        gps_embedding = payload.get("gps_embedding") if isinstance(payload.get("gps_embedding"), list) else None
        vision_embedding = payload.get("vision_embedding") if isinstance(payload.get("vision_embedding"), list) else None
        image_path = str(payload.get("image_path") or "").strip() or None
        return cls(
            gps_sequence=gps_sequence,
            image_path=image_path,
            metadata=dict(payload.get("metadata") or {}),
            label=float(payload.get("label") or 0.0),
            gps_embedding=[float(value) for value in gps_embedding] if gps_embedding else None,
            vision_embedding=[float(value) for value in vision_embedding] if vision_embedding else None,
        )