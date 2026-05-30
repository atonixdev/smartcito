from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class GeoPoint:
    latitude: float
    longitude: float
    altitude_m: float | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return {key: value for key, value in payload.items() if value is not None}


@dataclass(slots=True)
class DroneProfile:
    drone_id: str
    model: str
    firmware_version: str
    max_speed_mps: float
    max_altitude_m: float
    battery_capacity_mah: int
    camera_types: list[str]
    sensors: list[str]
    payload_supported: bool
    protocol: str = "mavlink"
    endpoint: str | None = None
    auth_profile: str | None = None

    def to_connect_payload(self) -> dict[str, Any]:
        return {
            "drone_id": self.drone_id,
            "protocol": self.protocol,
            "endpoint": self.endpoint,
            "auth_profile": self.auth_profile,
        }

    def to_capabilities_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("endpoint", None)
        payload.pop("auth_profile", None)
        payload["status"] = "online"
        payload["last_seen_at"] = datetime.now(UTC).isoformat()
        return payload


@dataclass(slots=True)
class TelemetrySample:
    drone_id: str
    position: GeoPoint
    speed_mps: float
    heading_deg: float
    battery_percent: float
    flight_mode: str
    status: str
    protocol: str = "mavlink"
    link_quality: float | None = None
    health_flags: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_gateway_payload(self) -> dict[str, Any]:
        return {
            "drone_id": self.drone_id,
            "protocol": self.protocol,
            "position": self.position.to_dict(),
            "speed_mps": self.speed_mps,
            "heading_deg": self.heading_deg,
            "battery_percent": self.battery_percent,
            "flight_mode": self.flight_mode,
            "status": self.status,
            "link_quality": self.link_quality,
            "health_flags": self.health_flags,
            "timestamp": self.timestamp,
        }


@dataclass(slots=True)
class CameraStreamProfile:
    drone_id: str
    stream_url: str
    protocol: str = "rtsp"
    camera_id: str = "rgb-main"
    preview_enabled: bool = True
    position: GeoPoint | None = None

    def to_registration_payload(self) -> dict[str, Any]:
        payload = {
            "drone_id": self.drone_id,
            "stream_url": self.stream_url,
            "protocol": self.protocol,
            "preview_enabled": self.preview_enabled,
        }
        if self.position is not None:
            payload["position"] = self.position.to_dict()
        return payload


@dataclass(slots=True)
class FrameSample:
    drone_id: str
    width: int
    height: int
    stream_url: str | None = None
    preview_url: str | None = None
    position: GeoPoint | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "drone_id": self.drone_id,
            "width": self.width,
            "height": self.height,
            "timestamp": self.timestamp,
        }
        if self.stream_url is not None:
            payload["stream_url"] = self.stream_url
        if self.preview_url is not None:
            payload["preview_url"] = self.preview_url
        if self.position is not None:
            payload["position"] = self.position.to_dict()
        return payload


@dataclass(slots=True)
class SensorSnapshot:
    device_id: str
    sensor_type: str
    position: GeoPoint
    value: float
    unit: str
    alert: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_payload(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "sensor_type": self.sensor_type,
            "position": self.position.to_dict(),
            "value": self.value,
            "unit": self.unit,
            "alert": self.alert,
            "timestamp": self.timestamp,
        }