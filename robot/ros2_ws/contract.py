"""ROS2 workspace contract for the robot stack."""

from __future__ import annotations


def build_ros2_robot_contract() -> dict[str, object]:
    return {
        "workspace": "ros2_ws",
        "packages": ["robot_bringup", "robot_localization", "robot_navigation", "robot_perception", "robot_bridge"],
        "topics": [
            "/robot/telemetry",
            "/robot/odometry",
            "/robot/command",
            "/robot/perception",
            "/robot/mission_status",
            "/robot/px4/telemetry",
            "/robot/px4/command",
        ],
        "nodes": ["sensor_bridge", "pose_estimator", "planner", "mission_executor", "cloud_bridge", "px4_bridge"],
        "message_types": ["RobotTelemetryMessage", "RobotCommandMessage"],
        "control_loop": ["sense", "fuse", "decide", "publish_ros2", "bridge_px4"],
    }
