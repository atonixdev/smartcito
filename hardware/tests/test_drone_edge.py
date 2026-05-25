from hardware.drone_edge.companion import DroneCompanionRuntime
from hardware.drone_edge.manufacturer_spec import build_manufacturer_spec
from hardware.drone_edge.mavlink_bridge import build_drone_profile, normalize_mavlink_telemetry
from hardware.drone_edge.rfp_packet import build_rfp_packet
from hardware.drone_edge.ros2_contract import build_ros2_node_contract
from hardware.drone_edge.schemas import CameraStreamProfile, GeoPoint, SensorSnapshot
from hardware.drone_edge.sdk import SmartCitoDroneSDK
from hardware.drone_edge.streamer import VideoEncodingProfile, build_camera_stream_profile


class RecordingDroneSDK(SmartCitoDroneSDK):
    def __init__(self) -> None:
        super().__init__()
        self.calls: list[tuple[str, dict[str, object]]] = []

    def _request_json(self, method: str, url: str, payload: dict[str, object] | None = None) -> dict[str, object]:
        self.calls.append((url, payload or {}))
        return {"method": method, "url": url, "payload": payload or {}}


def test_normalize_mavlink_telemetry() -> None:
    telemetry = normalize_mavlink_telemetry(
        drone_id="drone-edge-001",
        mavlink_payload={
            "latitude": -25.7454,
            "longitude": 28.2438,
            "relative_alt_m": 95,
            "groundspeed_mps": 7.8,
            "heading_deg": 42,
            "battery_remaining_pct": 83,
            "flight_mode": "patrol",
            "status": "in_mission",
            "link_quality": 0.91,
            "gps_lock": True,
            "ekf_ok": False,
        },
    )

    payload = telemetry.to_gateway_payload()
    assert payload["drone_id"] == "drone-edge-001"
    assert payload["position"]["altitude_m"] == 95
    assert payload["battery_percent"] == 83
    assert "ekf_ok" in payload["health_flags"]


def test_companion_runtime_bootstraps_and_uplinks() -> None:
    sdk = RecordingDroneSDK()
    profile = build_drone_profile(
        drone_id="drone-edge-002",
        mavlink_endpoint="udp://0.0.0.0:14540",
        autopilot_payload={"model": "PX4 Patrol Airframe", "firmware_version": "px4-1.15.2", "thermal_camera": True},
    )
    runtime = DroneCompanionRuntime(
        sdk=sdk,
        drone_profile=profile,
        camera_profile=CameraStreamProfile(
            drone_id="drone-edge-002",
            stream_url="rtsp://127.0.0.1:8554/main",
            position=GeoPoint(latitude=-25.7454, longitude=28.2438, altitude_m=95),
        ),
    )

    bootstrap = runtime.bootstrap()
    assert bootstrap["connect"]["payload"]["protocol"] == "mavlink"
    assert bootstrap["capabilities"]["payload"]["status"] == "online"

    uplink = runtime.uplink_snapshot(
        mavlink_payload={
            "latitude": -25.7454,
            "longitude": 28.2438,
            "relative_alt_m": 95,
            "groundspeed_mps": 8.4,
            "heading_deg": 90,
            "battery_remaining_pct": 88,
            "flight_mode": "patrol",
            "status": "in_mission",
        },
        sensor_snapshots=[
            SensorSnapshot(
                device_id="drone-edge-002-imu",
                sensor_type="imu-vibration",
                position=GeoPoint(latitude=-25.7454, longitude=28.2438, altitude_m=95),
                value=0.14,
                unit="g",
            )
        ],
        frame_size=(1280, 720),
    )

    assert uplink["telemetry"]["payload"]["drone_id"] == "drone-edge-002"
    assert uplink["frame"]["payload"]["width"] == 1280
    assert uplink["sensors"][0]["payload"]["sensor_type"] == "imu-vibration"
    assert len(sdk.calls) >= 5


def test_video_encoding_profile_builds_camera_behavior() -> None:
    encoder = VideoEncodingProfile(
        input_source="/dev/video0",
        stream_host="edge-gateway.local:8554",
        stream_path="patrol/main",
        protocol="rtsp",
        codec="h265",
        width=1280,
        height=720,
        fps=25,
        bitrate_kbps=2500,
        hardware_acceleration="jetson",
    )

    profile = build_camera_stream_profile(drone_id="drone-edge-003", encoder_profile=encoder)

    assert profile.stream_url == "rtsp://edge-gateway.local:8554/patrol/main"
    assert profile.protocol == "rtsp"
    assert encoder.behavior_contract()["codec"] == "h265"
    assert "hevc_nvenc" in encoder.ffmpeg_command()


def test_companion_runtime_includes_camera_pipeline_plan() -> None:
    sdk = RecordingDroneSDK()
    profile = build_drone_profile(
        drone_id="drone-edge-004",
        mavlink_endpoint="udp://0.0.0.0:14540",
        autopilot_payload={"model": "PX4 Patrol Airframe", "firmware_version": "px4-1.15.2"},
    )
    runtime = DroneCompanionRuntime(
        sdk=sdk,
        drone_profile=profile,
        encoder_profile=VideoEncodingProfile(
            input_source="/dev/video1",
            stream_host="edge-gateway.local:8554",
            stream_path="drone-edge-004/main",
        ),
    )

    bootstrap = runtime.bootstrap()

    assert bootstrap["camera_pipeline"] is not None
    assert bootstrap["camera_pipeline"]["behavior"]["protocol"] == "rtsp"
    assert bootstrap["camera"]["payload"]["stream_url"] == "rtsp://edge-gateway.local:8554/drone-edge-004/main"


def test_manufacturer_spec_covers_vendor_requirements() -> None:
    spec = build_manufacturer_spec()

    assert "PX4" in spec["flight_stack"]["autopilot"]
    assert "MAVLink" in spec["flight_stack"]["required_protocols"]
    assert "SSH access to companion computer" in spec["operator_access"]["required"]


def test_ros2_contract_covers_autonomy_nodes() -> None:
    contract = build_ros2_node_contract()

    node_names = [node["name"] for node in contract["nodes"]]
    assert "smartcito_slam_node" in node_names
    assert "smartcito_obstacle_avoidance_node" in node_names
    assert "smartcito_visual_odometry_node" in node_names
    assert "Mission Control" in contract["cloud_publish_contract"]["operator_surfaces"]


def test_rfp_packet_includes_bom_and_acceptance_sections() -> None:
    packet = build_rfp_packet()

    assert packet["title"] == "SmartCito Drone Platform RFP Packet"
    assert "companion computer SKU" in packet["bom_fields"]
    assert any("SSH" in item for item in packet["acceptance_checklist"])