"""Hybrid physics + AI helpers for robot operations."""

from __future__ import annotations

from robot.cloud.contracts import build_robot_cloud_contract
from robot.navigation.localization import build_robot_localization_contract
from robot.navigation.planning import build_navigation_contract
from robot.physics.dynamics import brake_distance, stability_margin
from robot.physics.energy import estimate_runtime_seconds
from robot.perception.detection import build_robot_perception_contract
from robot.ros2_ws.contract import build_ros2_robot_contract
from robot.sensors.fusion import build_robot_sensor_contract


def predict_robot_stability() -> dict[str, object]:
    margin = float(stability_margin(track_width=0.6, com_height=0.22, lateral_accel=1.8))
    return {
        "stability_margin": margin,
        "safe": margin > 0.0,
        "notes": "Use lower center of mass and slower turns on rough terrain.",
    }


def predict_robot_energy_use() -> dict[str, object]:
    runtime = float(estimate_runtime_seconds(battery_wh=420.0, average_power_w=180.0))
    stopping = float(brake_distance(speed=2.5, deceleration=1.1))
    return {
        "runtime_seconds": runtime,
        "safe_brake_distance_m": stopping,
        "battery_profile": "high-capacity Li-ion + smart BMS",
    }


def build_robot_ai_model() -> dict[str, object]:
    physics = {
        "stability": predict_robot_stability(),
        "energy": predict_robot_energy_use(),
        "motion": {
            "brake_distance_m": float(brake_distance(speed=2.5, deceleration=1.1)),
        },
    }
    sensors = build_robot_sensor_contract()
    perception = build_robot_perception_contract()
    navigation = build_navigation_contract()
    localization = build_robot_localization_contract()
    cloud = build_robot_cloud_contract()
    ros2 = build_ros2_robot_contract()

    return {
        "model_name": "Orca Robot AI",
        "purpose": "Fuse robot physics, sensors, perception, navigation, cloud, and ROS2 into one operational model.",
        "inputs": {
            "physics": physics,
            "sensors": sensors,
            "perception": perception,
            "navigation": navigation,
            "localization": localization,
            "cloud": cloud,
            "ros2": ros2,
        },
        "outputs": {
            "operator_goal": "safe autonomous operation",
            "primary_decisions": [
                "stabilize_robot",
                "estimate_energy_budget",
                "avoid_obstacles",
                "plan_path",
                "publish_telemetry",
                "sync_ros2_workspace",
            ],
        },
    }
