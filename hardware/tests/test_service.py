from fastapi.testclient import TestClient

from hardware.service import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "hardware-domain"}


def test_monitoring_sample() -> None:
    response = client.get("/monitoring/sample")

    assert response.status_code == 200
    payload = response.json()
    assert payload["rack_id"] == "rack-a1"
    assert isinstance(payload["temperature_c"], float)
    assert isinstance(payload["power_kw"], float)


def test_drone_edge_reference_stack() -> None:
    response = client.get("/drone-edge/reference-stack")

    assert response.status_code == 200
    payload = response.json()
    assert payload["hardware_layer"]["autopilot"] == "PX4 Autopilot"
    assert "MAVLink telemetry stream via Orca drone SDK" == payload["communication_layer"]["telemetry"]


def test_drone_edge_hardware_spec() -> None:
    response = client.get("/drone-edge/hardware-spec")

    assert response.status_code == 200
    payload = response.json()
    assert "PX4" in payload["flight_stack"]["autopilot"]
    assert "SSH access to companion computer" in payload["operator_access"]["required"]


def test_drone_edge_ros2_contract() -> None:
    response = client.get("/drone-edge/ros2-contract")

    assert response.status_code == 200
    payload = response.json()
    assert payload["runtime"]["middleware"] == "ROS2"
    assert payload["nodes"][0]["name"].startswith("orca_")


def test_drone_edge_rfp_packet() -> None:
    response = client.get("/drone-edge/rfp-packet")

    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "Orca Drone Platform RFP Packet"
    assert "battery capacity" in payload["bom_fields"]