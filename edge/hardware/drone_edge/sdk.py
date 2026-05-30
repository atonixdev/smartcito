from __future__ import annotations

import json
from typing import Any
from urllib import request

from hardware.drone_edge.schemas import CameraStreamProfile, DroneProfile, FrameSample, SensorSnapshot, TelemetrySample


class OrcaDroneSDK:
    def __init__(
        self,
        *,
        drone_gateway_base_url: str = "http://localhost:8020",
        sensor_gateway_base_url: str = "http://localhost:8021",
        camera_service_base_url: str = "http://localhost:8022",
        timeout_seconds: float = 5.0,
    ) -> None:
        self.drone_gateway_base_url = drone_gateway_base_url.rstrip("/")
        self.sensor_gateway_base_url = sensor_gateway_base_url.rstrip("/")
        self.camera_service_base_url = camera_service_base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _request_json(self, method: str, url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        req = request.Request(url=url, data=body, headers={"content-type": "application/json"}, method=method)
        with request.urlopen(req, timeout=self.timeout_seconds) as response:
            raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}

    def connect_drone(self, profile: DroneProfile) -> dict[str, Any]:
        return self._request_json("POST", f"{self.drone_gateway_base_url}/connect", profile.to_connect_payload())

    def sync_capabilities(self, profile: DroneProfile) -> dict[str, Any]:
        return self._request_json("POST", f"{self.drone_gateway_base_url}/capabilities", profile.to_capabilities_payload())

    def publish_telemetry(self, sample: TelemetrySample) -> dict[str, Any]:
        return self._request_json("POST", f"{self.drone_gateway_base_url}/telemetry", sample.to_gateway_payload())

    def register_camera_stream(self, profile: CameraStreamProfile) -> dict[str, Any]:
        return self._request_json("POST", f"{self.camera_service_base_url}/streams/register", profile.to_registration_payload())

    def publish_frame(self, frame: FrameSample) -> dict[str, Any]:
        return self._request_json("POST", f"{self.camera_service_base_url}/frames", frame.to_payload())

    def publish_sensor_snapshot(self, snapshot: SensorSnapshot) -> dict[str, Any]:
        return self._request_json("POST", f"{self.sensor_gateway_base_url}/readings", snapshot.to_payload())