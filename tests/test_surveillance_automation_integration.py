import os

os.environ["ORCA_KAFKA_ENABLED"] = "0"
os.environ["DRONE_REGISTRY_ENABLED"] = "0"

from fastapi.testclient import TestClient

from surveillance import mission_control_service, robot_gateway_service
from surveillance.mission_control_service import app as mission_app
from surveillance.robot_gateway_service import app as robot_app
from surveillance.threat_detection_service import app as threat_app


class FakeResponse:
    def __init__(self, body: bytes):
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return self._body


def test_surveillance_cycle_inprocess_escalation_and_dispatch(monkeypatch) -> None:
    def fake_gateway_urlopen(_request_obj, timeout=5):
        return FakeResponse(b'{"accepted": true, "adapter_status": "uploaded"}')

    monkeypatch.setattr(mission_control_service.request, "urlopen", fake_gateway_urlopen)

    threat_client = TestClient(threat_app)
    mission_client = TestClient(mission_app)

    def inprocess_post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
        if url.endswith("/surveillance/escalate"):
            response = threat_client.post("/surveillance/escalate", json=payload)
            return response.json()
        if url.endswith("/surveillance/dispatch"):
            response = mission_client.post("/surveillance/dispatch", json=payload)
            return response.json()
        return {"status": "unsupported"}

    monkeypatch.setattr(robot_gateway_service, "_post_json", inprocess_post_json)

    robot_client = TestClient(robot_app)
    response = robot_client.post(
        "/surveillance/cycle",
        json={
            "robot_id": "robot-cap-001",
            "environment": "critical-infrastructure",
            "perception": {
                "object_labels": ["human", "drone", "weapon"],
                "thermal_hotspots": 2,
                "motion_score": 0.95,
                "gas_level_ppm": 72.0,
                "smoke_score": 0.4,
                "radiation_level": 0.1,
                "slope_deg": 8.0,
                "obstacle_distance_m": 1.2,
            },
            "tracking": {
                "target_speed_mps": 8.0,
                "target_heading_deg": 60.0,
                "target_distance_m": 25.0,
                "optical_flow_score": 0.88,
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()["event"]["payload"]

    assert "automation" in payload
    escalation = payload["automation"]["threat_escalation"]
    dispatch = payload["automation"]["mission_dispatch"]

    assert escalation["event"]["event_type"] == "threat.surveillance.escalated"
    assert dispatch["status"] == "uploaded"
    assert dispatch["dispatch_results"]
    assert any(result["accepted"] for result in dispatch["dispatch_results"])
    assert all("gateway-unavailable" not in result["adapter_status"] for result in dispatch["dispatch_results"])
