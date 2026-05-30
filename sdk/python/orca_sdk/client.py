from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request


class OrcaApiError(RuntimeError):
    def __init__(self, status_code: int, message: str, payload: Any | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


@dataclass(slots=True)
class OrcaClient:
    base_url: str
    token: str | None = None
    timeout: float = 10.0

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")

    def health_live(self) -> dict[str, Any]:
        return self._request_json("GET", "/api/v1/health/live")

    def health_ready(self) -> dict[str, Any]:
        return self._request_json("GET", "/api/v1/health/ready")

    def health_status(self) -> dict[str, Any]:
        return self._request_json("GET", "/api/v1/health/status")

    def control_plane_overview(self) -> dict[str, Any]:
        return self._request_json("GET", "/api/v1/control-plane/overview")

    def map_overview(self) -> dict[str, Any]:
        return self._request_json("GET", "/api/v1/control-plane/map")

    def scene_overview(self) -> dict[str, Any]:
        return self._request_json("GET", "/api/v1/control-plane/scene")

    def live_fleet(self, active_within_minutes: int = 15) -> dict[str, Any]:
        return self._request_json(
            "GET",
            "/api/v1/fleet/live",
            query={"active_within_minutes": active_within_minutes},
        )

    def get_last_position(self, device_id: str) -> dict[str, Any]:
        return self._request_json("GET", f"/api/v1/devices/{urllib_parse.quote(device_id)}/last-position")

    def get_device_track(
        self,
        device_id: str,
        *,
        from_ts: str | None = None,
        to_ts: str | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {"limit": limit}
        if from_ts is not None:
            query["from"] = from_ts
        if to_ts is not None:
            query["to"] = to_ts
        return self._request_json(
            "GET",
            f"/api/v1/devices/{urllib_parse.quote(device_id)}/track",
            query=query,
        )

    def list_cameras(self) -> list[dict[str, Any]]:
        return self._request_json("GET", "/api/v1/cameras")

    def register_camera(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request_json("POST", "/api/v1/cameras/register", payload=payload)

    def update_camera_telemetry(self, device_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request_json(
            "POST",
            f"/api/v1/cameras/{urllib_parse.quote(device_id)}/telemetry",
            payload=payload,
        )

    def register_map_device(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request_json("POST", "/api/v1/control-plane/map/register", payload=payload)

    def update_operator_control(self, control_id: str, desired_state: str) -> dict[str, Any]:
        return self._request_json(
            "POST",
            f"/api/v1/control-plane/operator-controls/{urllib_parse.quote(control_id)}",
            payload={"desired_state": desired_state},
        )

    def ingest_gps_point(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request_json("POST", "/api/v1/ingest/gps", payload=payload)

    def ingest_gps_gateway_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request_json("POST", "/api/v1/gps/gateway/ingest", payload=payload)

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        if query:
            encoded_query = urllib_parse.urlencode({key: value for key, value in query.items() if value is not None})
            url = f"{url}?{encoded_query}"

        body: bytes | None = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        request = urllib_request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib_request.urlopen(request, timeout=self.timeout) as response:
                raw_body = response.read().decode("utf-8")
                if not raw_body:
                    return None
                return json.loads(raw_body)
        except urllib_error.HTTPError as exc:
            raw_error = exc.read().decode("utf-8", errors="replace")
            payload_obj: Any | None = None
            message = raw_error or exc.reason or "Orca API request failed"
            if raw_error:
                try:
                    payload_obj = json.loads(raw_error)
                    if isinstance(payload_obj, dict) and isinstance(payload_obj.get("detail"), str):
                        message = payload_obj["detail"]
                except json.JSONDecodeError:
                    payload_obj = raw_error
            raise OrcaApiError(exc.code, message, payload_obj) from exc
