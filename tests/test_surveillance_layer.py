import os

os.environ["SMARTCITO_KAFKA_ENABLED"] = "0"
os.environ["DRONE_REGISTRY_ENABLED"] = "0"

from fastapi.testclient import TestClient

from surveillance.drone_camera_service import app as camera_app
from surveillance.drone_gateway_service import app as drone_app
from surveillance.mapping_service import app as mapping_app
from surveillance.mission_control_service import app as mission_app
from surveillance.robot_gateway_service import app as robot_app
from surveillance.sensor_gateway_service import app as sensor_app
from surveillance.threat_detection_service import app as threat_app


def test_drone_gateway_normalizes_telemetry() -> None:
    client = TestClient(drone_app)
    response = client.post(
        "/telemetry",
        json={
            "drone_id": "drone-001",
            "protocol": "mavlink",
            "position": {"latitude": -25.7479, "longitude": 28.2293, "altitude_m": 120},
            "speed_mps": 8.2,
            "heading_deg": 90,
            "battery_percent": 87,
            "status": "in_mission",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["event"]["topic"] == "smartcito.drone.telemetry"
    assert payload["event"]["payload"]["coordinate_system"] == "WGS84"
    assert payload["event"]["payload"]["zone"]["zone_id"] == "zone-1-cbd"
    assert payload["publish"]["status"] == "kafka-unavailable"


def test_drone_gateway_discovers_capabilities_and_accepts_command() -> None:
    client = TestClient(drone_app)
    connected = client.post(
        "/connect",
        json={"drone_id": "drone-cap-001", "protocol": "simulated", "endpoint": "sim://drone-cap-001"},
    )
    assert connected.status_code == 200
    capabilities = connected.json()
    assert capabilities["drone_id"] == "drone-cap-001"
    assert "thermal" in capabilities["camera_types"]
    assert "imu" in capabilities["sensors"]

    command = client.post(
        "/drones/drone-cap-001/commands",
        json={
            "drone_id": "drone-cap-001",
            "action": "move_to",
            "target": {"latitude": -25.7454, "longitude": 28.2438, "altitude_m": 95},
            "requested_by": "mission-control",
        },
    )
    assert command.status_code == 200
    payload = command.json()
    assert payload["accepted"] is True
    assert payload["event"]["event_type"] == "drone.command.move_to"


def test_drone_gateway_rejects_incomplete_camera_command() -> None:
    client = TestClient(drone_app)
    response = client.post(
        "/commands",
        json={"drone_id": "drone-001", "action": "camera_zoom", "zoom_level": 4},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "camera actions require camera_id"


def test_drone_gateway_metrics_endpoint() -> None:
    client = TestClient(drone_app)
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "smartcito_drone_gateway_events_total" in response.text


def test_robot_gateway_discovers_capabilities_and_accepts_command() -> None:
    client = TestClient(robot_app)
    connected = client.post(
        "/connect",
        json={"robot_id": "robot-cap-001", "protocol": "simulated", "endpoint": "sim://robot-cap-001"},
    )
    assert connected.status_code == 200
    capabilities = connected.json()
    assert capabilities["robot_id"] == "robot-cap-001"
    assert "lidar" in capabilities["sensors"]

    telemetry = client.post(
        "/telemetry",
        json={
            "robot_id": "robot-cap-001",
            "protocol": "simulated",
            "position": {"latitude": -25.7462, "longitude": 28.2372, "altitude_m": 0},
            "speed_mps": 1.4,
            "heading_deg": 118,
            "battery_percent": 74,
            "autonomy_state": "route_follow",
            "status": "patrolling",
            "slam_state": "locked",
        },
    )
    assert telemetry.status_code == 200
    assert telemetry.json()["event"]["topic"] == "smartcito.robot.telemetry"

    command = client.post(
        "/robots/robot-cap-001/commands",
        json={
            "robot_id": "robot-cap-001",
            "action": "set_waypoint",
            "target": {"latitude": -25.7460, "longitude": 28.2376, "altitude_m": 0},
            "requested_by": "robot-dashboard",
        },
    )
    assert command.status_code == 200
    payload = command.json()
    assert payload["accepted"] is True
    assert payload["event"]["event_type"] == "robot.command.set_waypoint"


def test_sensor_gateway_splits_alert_topics() -> None:
    client = TestClient(sensor_app)
    response = client.post(
        "/readings",
        json={
            "device_id": "perimeter-003",
            "sensor_type": "motion",
            "position": {"latitude": -25.744, "longitude": 28.242},
            "value": 1,
            "unit": "boolean",
            "alert": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["event"]["topic"] == "smartcito.sensor.alerts"


def test_camera_service_requires_stream_or_frame_url() -> None:
    client = TestClient(camera_app)
    missing = client.post("/frames", json={"drone_id": "drone-404"})
    assert missing.status_code == 404

    registered = client.post(
        "/streams/register",
        json={"drone_id": "drone-002", "stream_url": "rtsp://drone-002/main", "protocol": "rtsp"},
    )
    assert registered.status_code == 200

    frame = client.post("/frames", json={"drone_id": "drone-002", "width": 640, "height": 360})
    assert frame.status_code == 200
    assert frame.json()["event"]["topic"] == "smartcito.drone.camera.frames"

    feeds = client.get("/feeds")
    assert feeds.status_code == 200
    assert feeds.json()[0]["drone_id"] == "drone-002"


def test_mission_control_validates_and_uploads_patrol() -> None:
    client = TestClient(mission_app)

    review_required = client.post(
        "/missions/validate",
        json={
            "drone_id": "drone-review-001",
            "name": "Critical route",
            "altitude_m": 95,
            "speed_mps": 8,
            "waypoints": [
                {"latitude": -25.7454, "longitude": 28.2438, "altitude_m": 95},
                {"latitude": -25.7444, "longitude": 28.2441, "altitude_m": 95},
            ],
        },
    )
    assert review_required.status_code == 200
    assert review_required.json()["requires_operator_review"] is True

    uploaded = client.post(
        "/missions",
        json={
            "drone_id": "drone-safe-001",
            "name": "Transport patrol",
            "altitude_m": 80,
            "speed_mps": 8,
            "waypoints": [
                {"latitude": -25.7480, "longitude": 28.1800, "altitude_m": 80},
                {"latitude": -25.7460, "longitude": 28.1820, "altitude_m": 80},
            ],
        },
    )
    assert uploaded.status_code == 200
    payload = uploaded.json()
    assert payload["status"] in {"uploaded", "failed"}
    assert payload["validation"]["zones"]

    missions = client.get("/missions")
    assert missions.status_code == 200
    assert len(missions.json()) >= 1


def test_mission_control_creates_city_mission() -> None:
    client = TestClient(mission_app)

    response = client.post(
        "/city-missions",
        json={
            "name": "Pretoria CBD coordinated patrol",
            "city": "Pretoria",
            "district": "CBD",
            "radius_km": 4,
            "assignments": [
                {
                    "asset_type": "drone",
                    "asset_id": "drone-safe-001",
                    "altitude_m": 90,
                    "speed_mps": 8,
                    "path": [
                        {"latitude": -25.7480, "longitude": 28.1800, "altitude_m": 90},
                        {"latitude": -25.7460, "longitude": 28.1820, "altitude_m": 90},
                    ],
                },
                {
                    "asset_type": "robot",
                    "asset_id": "robot-cap-001",
                    "speed_mps": 1.5,
                    "path": [
                        {"latitude": -25.7480, "longitude": 28.1800, "altitude_m": 0},
                        {"latitude": -25.7460, "longitude": 28.1820, "altitude_m": 0},
                    ],
                },
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"uploaded", "failed"}
    assert len(payload["dispatch_results"]) == 2

    missions = client.get("/city-missions")
    assert missions.status_code == 200
    assert len(missions.json()) >= 1


def test_threat_detection_classifies_critical_zone() -> None:
    client = TestClient(threat_app)
    response = client.post(
        "/detections",
        json={
            "source_id": "drone-003-camera",
            "source_type": "drone_camera",
            "label": "weapon detected",
            "confidence": 0.94,
            "position": {"latitude": -25.745, "longitude": 28.245},
        },
    )

    assert response.status_code == 200
    alert = response.json()["event"]["payload"]
    assert alert["threat_level"] == "critical"
    assert "dispatch-nearest-drone" in alert["recommended_actions"]


def test_mapping_service_exposes_overlays() -> None:
    client = TestClient(mapping_app)
    response = client.post(
        "/overlays/drone",
        json={
            "drone_id": "drone-map-001",
            "position": {"latitude": -25.7479, "longitude": 28.2293},
            "battery_percent": 72,
        },
    )

    assert response.status_code == 200
    overview = client.get("/overlays")
    assert overview.status_code == 200
    assert overview.json()["drones"][0]["overlay_id"] == "drone-map-001"
    assert overview.json()["geofences"]
