from __future__ import annotations

from hardware.drone_edge.manufacturer_spec import build_manufacturer_spec
from hardware.drone_edge.rfp_packet import build_rfp_packet
from hardware.drone_edge.ros2_contract import build_ros2_node_contract


def build_reference_stack() -> dict[str, object]:
    return {
        "hardware_layer": {
            "autopilot": "PX4 Autopilot",
            "autonomy": ["ROS2 autonomy nodes", "SLAM", "obstacle avoidance", "visual odometry"],
            "protocol": "MAVLink",
            "sensors": ["imu", "gps", "barometer", "magnetometer"],
            "cameras": ["rgb", "thermal", "zoom"],
        },
        "communication_layer": {
            "telemetry": "MAVLink telemetry stream via SmartCito drone SDK",
            "video": ["rtsp", "webrtc"],
            "links": ["4g", "5g", "wifi"],
            "sdk": "hardware.drone_edge.sdk.SmartCitoDroneSDK",
        },
        "cloud_surfaces": {
            "drone_gateway": "http://drone-gateway:8020",
            "sensor_gateway": "http://sensor-gateway:8021",
            "camera_service": "http://drone-camera-ingestion:8022",
            "mission_control": "http://mission-control:8025",
        },
        "ros2_contract": build_ros2_node_contract(),
        "manufacturer_spec": build_manufacturer_spec(),
        "rfp_packet": build_rfp_packet(),
    }