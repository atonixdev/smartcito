"""Cloud integration contracts for robot operations."""

from __future__ import annotations


def build_robot_cloud_contract() -> dict[str, object]:
    return {
        "cloud": {
            "platforms": ["OpenStack", "Kubernetes"],
            "services": ["mission_control", "streaming", "telemetry_ingest", "multi_robot_coordination"],
            "protocols": ["MQTT", "gRPC", "WebSocket", "ROS2 bridge"],
        },
        "storage": ["maps", "video", "sensor_logs", "detections", "maintenance_records"],
        "control": ["remote_commands", "patrol_routes", "live_tracking", "alerts"],
    }
