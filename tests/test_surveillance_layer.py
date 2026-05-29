import os
from urllib.error import URLError

os.environ["ORCA_KAFKA_ENABLED"] = "0"
os.environ["DRONE_REGISTRY_ENABLED"] = "0"

from fastapi.testclient import TestClient

from surveillance.drone_camera_service import app as camera_app
from surveillance.drone_gateway_service import app as drone_app
from surveillance import geospatial
from surveillance.mapping_service import app as mapping_app
from surveillance.mission_control_service import app as mission_app
from surveillance import mission_control_service
from surveillance import drone_camera_service
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
    assert payload["event"]["topic"] == "orca.drone.telemetry"
    assert payload["event"]["payload"]["coordinate_system"] == "WGS84"
    assert payload["event"]["payload"]["zone"]["zone_id"] == "zone-1-cbd"
    assert payload["event"]["payload"]["security"]["algorithm"] == "AES-256-GCM"
    assert payload["event"]["payload"]["security"]["integrity"]["hash"]["sha256"]
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
    assert "orca_drone_gateway_events_total" in response.text


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
    assert telemetry.json()["event"]["topic"] == "orca.robot.telemetry"

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


def test_robot_gateway_surveillance_architecture_contract() -> None:
    client = TestClient(robot_app)
    response = client.get("/surveillance/architecture")

    assert response.status_code == 200
    payload = response.json()
    assert "sections" in payload
    assert len(payload["sections"]) == 10
    assert payload["sections"][0]["name"] == "system_overview"


def test_robot_gateway_executes_surveillance_cycle() -> None:
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
            "cloud": {
                "openstack": True,
                "kubernetes": True,
                "live_streaming": True,
                "mission_control": True,
                "multi_robot_coordination": True,
            },
            "security": {
                "encrypted_telemetry": True,
                "secure_boot": True,
                "identity_verified": True,
                "tamper_detected": False,
                "cloud_auth_ok": True,
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
    assert payload["publish"]["topic"] == "orca.robot.events"


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
    assert response.json()["event"]["topic"] == "orca.sensor.alerts"
    assert response.json()["event"]["payload"]["security"]["integrity"]["signature"]["value"]


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
    assert frame.json()["event"]["topic"] == "orca.drone.camera.frames"
    assert frame.json()["event"]["payload"]["snapshot_integrity"]["hash"]["sha256"]

    feeds = client.get("/feeds")
    assert feeds.status_code == 200
    assert feeds.json()[0]["drone_id"] == "drone-002"


def test_camera_service_enriches_frame_with_ai_detections(monkeypatch) -> None:
    async def fake_detect_objects(**kwargs) -> dict[str, object]:
        assert kwargs["backend"] == "auto"
        return {
            "backend": "opencv",
            "requested_backend": "auto",
            "image_width": 20,
            "image_height": 20,
            "detections": [
                {
                    "label": "vehicle",
                    "confidence": 0.92,
                    "bbox": [2, 3, 14, 16],
                    "area_ratio": 0.21,
                }
            ],
        }

    monkeypatch.setattr(drone_camera_service.ai_client, "detect_objects", fake_detect_objects)

    client = TestClient(camera_app)
    registered = client.post(
        "/streams/register",
        json={"drone_id": "drone-ai-001", "stream_url": "rtsp://drone-ai-001/main", "protocol": "rtsp"},
    )
    assert registered.status_code == 200

    frame = client.post(
        "/frames",
        json={
            "drone_id": "drone-ai-001",
            "width": 640,
            "height": 360,
            "image_b64": "AA==",
            "ai_labels": ["vehicle"],
        },
    )

    assert frame.status_code == 200
    payload = frame.json()["event"]["payload"]
    assert "image_b64" not in payload
    assert payload["ai_analysis"]["backend"] == "opencv"
    assert payload["ai_analysis"]["detections"][0]["label"] == "vehicle"

    feeds = client.get("/feeds")
    assert feeds.status_code == 200
    matching_feed = next(feed for feed in feeds.json() if feed["drone_id"] == "drone-ai-001")
    assert matching_feed["ai_detections"][0]["label"] == "vehicle"


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
    assert payload["integrity"]["hash"]["sha256"]
    assert payload["integrity"]["envelope"]["algorithm"] == "AES-256-GCM"

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
    assert payload["integrity"]["hash"]["sha256"]

    missions = client.get("/city-missions")
    assert missions.status_code == 200
    assert len(missions.json()) >= 1


def test_mission_control_routes_payloads_through_shared_geographic_engine(monkeypatch) -> None:
    routed_paths: list[list[dict[str, float]]] = []

    def fake_route(origin, destinations, extra_obstacles=None):
        destination = destinations[0]
        return {
            "path": [
                origin.model_dump(mode="json"),
                {
                    "latitude": (origin.latitude + destination.latitude) / 2,
                    "longitude": (origin.longitude + destination.longitude) / 2,
                    "altitude_m": origin.altitude_m,
                },
                destination.model_dump(mode="json"),
            ]
        }

    class FakeResponse:
        def __init__(self, body: bytes):
            self._body = body

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> bytes:
            return self._body

    def fake_urlopen(request_obj, timeout=5):
        routed_paths.append(__import__("json").loads(request_obj.data.decode("utf-8"))["path"])
        return FakeResponse(b'{"accepted": true, "adapter_status": "uploaded"}')

    monkeypatch.setattr(mission_control_service, "route_mission", fake_route)
    monkeypatch.setattr(mission_control_service.request, "urlopen", fake_urlopen)

    client = TestClient(mission_app)
    response = client.post(
        "/missions",
        json={
            "drone_id": "drone-route-001",
            "name": "Engine routed patrol",
            "altitude_m": 80,
            "speed_mps": 8,
            "waypoints": [
                {"latitude": -25.7480, "longitude": 28.1800, "altitude_m": 80},
                {"latitude": -25.7460, "longitude": 28.1820, "altitude_m": 80},
            ],
        },
    )

    assert response.status_code == 200
    assert routed_paths
    assert len(routed_paths[0]) == 3


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


def test_mapping_service_resolves_normalized_coordinates() -> None:
    client = TestClient(mapping_app)
    response = client.post(
        "/resolve",
        json={"latitude": -25.7479, "longitude": 28.2293, "altitude_m": 120},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["coordinate_system"] == "EPSG:4326"
    assert payload["map_projection"] == "EPSG:3857"
    assert payload["projected_position"]["x"]
    assert payload["zone"]["zone_id"] == "zone-1-cbd"


def test_mapping_service_evaluates_geofence_entries_and_violations() -> None:
    client = TestClient(mapping_app)
    response = client.post(
        "/geofences/evaluate",
        json={
            "previous_position": {"latitude": -25.7605, "longitude": 28.2170},
            "current_position": {"latitude": -25.7479, "longitude": 28.2293},
            "path": [
                {"latitude": -25.7605, "longitude": 28.2170},
                {"latitude": -25.7479, "longitude": 28.2293},
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert "zone-1-cbd" in payload["entries"]
    assert "zone-1-cbd" in payload["violations"]
    assert "zone-1-cbd" in payload["intersections"]


def test_mapping_service_search_uses_fallback_index_when_nominatim_unavailable(monkeypatch) -> None:
    def raise_url_error(*args: object, **kwargs: object) -> None:
        raise URLError("offline")

    monkeypatch.setattr(geospatial.request, "urlopen", raise_url_error)
    client = TestClient(mapping_app)
    response = client.get("/search", params={"query": "Johannesburg Winchester", "radius_km": 2})

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "fallback-index"
    assert payload["results"]
    assert payload["radius"]["type"] == "Polygon"


def test_mapping_service_builds_networkx_mission_route() -> None:
    client = TestClient(mapping_app)
    response = client.post(
        "/routes/mission",
        json={
            "origin": {"latitude": -25.7605, "longitude": 28.2170},
            "destinations": [
                {"latitude": -25.7479, "longitude": 28.2293},
                {"latitude": -25.7448, "longitude": 28.2455},
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["distance_m"] > 0
    assert len(payload["segments"]) == 2
    assert payload["geojson"]["features"]
    assert len(payload["path"]) >= 2


def test_mapping_service_renders_city_map_outputs(monkeypatch) -> None:
    client = TestClient(mapping_app)
    client.post(
        "/overlays/sensor",
        json={
            "device_id": "sensor-map-001",
            "sensor_type": "acoustic",
            "position": {"latitude": -25.7465, "longitude": 28.2315},
            "value": 42,
            "unit": "dB",
            "alert": True,
        },
    )

    monkeypatch.setattr(geospatial, "fetch_persisted_geographic_dataset", lambda: {
        "drone_paths": [
            {
                "feature_id": "geo-drone-path-demo-001",
                "name": "Drone demo path",
                "feature_type": "drone_path",
                "zone": "cbd",
                "geometry": {"type": "LineString", "coordinates": [[28.2293, -25.7479], [28.2361, -25.7461]]},
                "properties": {},
            }
        ],
        "robot_paths": [
            {
                "feature_id": "geo-robot-path-demo-001",
                "name": "Robot demo path",
                "feature_type": "robot_path",
                "zone": "cbd",
                "geometry": {"type": "LineString", "coordinates": [[28.2287, -25.7488], [28.2322, -25.7474]]},
                "properties": {},
            }
        ],
        "mission_routes": [],
        "sensors": [
            {
                "feature_id": "geo-sensor-demo-001",
                "name": "Sensor demo point",
                "feature_type": "sensor",
                "zone": "cbd",
                "geometry": {"type": "Point", "coordinates": [28.2293, -25.7479]},
                "properties": {},
            }
        ],
        "cameras": [
            {
                "feature_id": "geo-camera-demo-001",
                "name": "Camera demo point",
                "feature_type": "camera",
                "zone": "cbd",
                "geometry": {"type": "Point", "coordinates": [28.2361, -25.7461]},
                "properties": {},
            }
        ],
        "geojson_layers": {
            "mission_route": {"type": "FeatureCollection", "features": []},
        },
    })

    response = client.get("/maps/city")

    assert response.status_code == 200
    payload = response.json()
    assert "leaflet" in payload["html"].lower()
    assert payload["geojson_layers"]["geofences"]["features"]
    assert payload["geojson_layers"]["sensors"]["features"]
    assert payload["geojson_layers"]["cameras"]["features"]
    assert payload["geojson_layers"]["drone_paths"]["features"]
    assert payload["geojson_layers"]["robot_paths"]["features"]
    assert payload["marker_layers"]["sensors"]
