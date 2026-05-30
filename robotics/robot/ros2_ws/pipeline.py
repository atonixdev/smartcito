"""ROS2/PX4 control pipeline for the Orca robot stack."""

from __future__ import annotations

from robot.ai.hybrid import build_robot_ai_model
from robot.navigation.control import obstacle_avoidance_command
from robot.ros2_ws.contract import build_ros2_robot_contract
from robot.ros2_ws.messages import RobotCommandMessage, RobotTelemetryMessage


def build_robot_px4_pipeline_contract() -> dict[str, object]:
    return {
        "ai_model": build_robot_ai_model()["model_name"],
        "ros2": build_ros2_robot_contract(),
        "stages": ["telemetry_ingest", "state_fusion", "policy_decision", "command_publish", "px4_bridge"],
        "messages": {
            "telemetry": "RobotTelemetryMessage",
            "command": "RobotCommandMessage",
        },
    }


def synthesize_robot_command(telemetry: RobotTelemetryMessage) -> RobotCommandMessage:
    model_name = str(build_robot_ai_model()["model_name"])
    obstacle_stop = telemetry.emergency_stop or telemetry.obstacle_risk >= 0.85 or telemetry.stability_margin <= 0.0

    safety_flags: list[str] = []
    if telemetry.emergency_stop:
        safety_flags.append("emergency_stop")
    if telemetry.obstacle_risk >= 0.85:
        safety_flags.append("obstacle_risk_high")
    if telemetry.stability_margin <= 0.0:
        safety_flags.append("instability_detected")
    if telemetry.battery_percent < 12.0:
        safety_flags.append("low_battery")

    if obstacle_stop:
        return RobotCommandMessage(
            robot_id=telemetry.robot_id,
            px4_mode="HOLD",
            linear_speed_mps=0.0,
            angular_rate_rad_s=0.0,
            brake=True,
            return_to_base=telemetry.battery_percent < 12.0,
            ros2_action="publish_emergency_stop",
            reason="safety_stop",
            source_model=model_name,
            safety_flags=safety_flags,
        )

    avoidance = obstacle_avoidance_command(
        telemetry.front_distance_m,
        telemetry.left_distance_m,
        telemetry.right_distance_m,
    )
    turn_rate = float(avoidance[1])
    speed_scale = max(0.15, 1.0 - telemetry.obstacle_risk)
    commanded_speed = min(telemetry.speed_limit_mps, telemetry.target_speed_mps * speed_scale)

    if telemetry.battery_percent < 12.0:
        px4_mode = "RTL"
        ros2_action = "publish_return_to_base"
        reason = "battery_low"
        return_to_base = True
    else:
        px4_mode = "AUTO"
        ros2_action = "publish_navigation_command"
        reason = "autonomous_navigation"
        return_to_base = False

    return RobotCommandMessage(
        robot_id=telemetry.robot_id,
        px4_mode=px4_mode,
        linear_speed_mps=float(commanded_speed),
        angular_rate_rad_s=turn_rate,
        brake=False,
        return_to_base=return_to_base,
        ros2_action=ros2_action,
        reason=reason,
        source_model=model_name,
        safety_flags=safety_flags,
    )


def build_robot_control_packet(telemetry: RobotTelemetryMessage) -> dict[str, object]:
    command = synthesize_robot_command(telemetry)
    return {
        "pipeline": build_robot_px4_pipeline_contract(),
        "telemetry": telemetry.to_dict(),
        "command": command.to_dict(),
    }