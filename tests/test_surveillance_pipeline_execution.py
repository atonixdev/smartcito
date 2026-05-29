import os

os.environ["ORCA_KAFKA_ENABLED"] = "0"
os.environ["DRONE_REGISTRY_ENABLED"] = "0"

from fastapi.testclient import TestClient

from surveillance.robot_gateway_service import app as robot_app


def test_surveillance_architecture_contract_has_10_sections() -> None:
    client = TestClient(robot_app)
    response = client.get("/surveillance/architecture")

    assert response.status_code == 200
    payload = response.json()
    assert "sections" in payload
    assert len(payload["sections"]) == 10
    assert payload["sections"][0]["name"] == "system_overview"
    assert payload["sections"][-1]["name"] == "workflow"


def test_surveillance_cycle_executes_end_to_end() -> None:
    client = TestClient(robot_app)
    response = client.post(
        "/surveillance/cycle",
        json={
            "robot_id": "robot-cap-001",
            "environment": "critical-infrastructure",
            "perception": {
                "object_labels": ["human", "drone"],
                "thermal_hotspots": 2,
                "motion_score": 0.9,
                "gas_level_ppm": 10.0,
                "smoke_score": 0.1,
                "radiation_level": 0.0,
                "slope_deg": 8.0,
                "obstacle_distance_m": 1.2,
            },
            "sensor_fusion": {
                "lidar_confidence": 0.95,
                "camera_confidence": 0.9,
                "imu_confidence": 0.92,
                "gps_confidence": 0.88,
                "thermal_confidence": 0.91,
                "acoustic_confidence": 0.83,
                "rf_confidence": 0.84,
                "environmental_confidence": 0.86,
            },
            "tracking": {
                "target_speed_mps": 7.0,
                "target_heading_deg": 64.0,
                "target_distance_m": 30.0,
                "optical_flow_score": 0.82,
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    event_payload = payload["event"]["payload"]

    assert event_payload["robot_id"] == "robot-cap-001"
    assert "perception" in event_payload
    assert "intelligence" in event_payload
    assert "autonomy" in event_payload
    assert "sensor_fusion" in event_payload
    assert "threat_detection" in event_payload
    assert "tracking_interception" in event_payload
    assert "cloud_integration" in event_payload
    assert "security_encryption" in event_payload
    assert "workflow" in event_payload
    assert "reaction" in event_payload
    assert "automation" in event_payload
    assert "threat_escalation" in event_payload["automation"]
    assert "mission_dispatch" in event_payload["automation"]
    assert payload["publish"]["topic"] == "orca.robot.events"
