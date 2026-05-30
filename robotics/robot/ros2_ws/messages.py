"""ROS2/PX4 message contracts for the Orca robot stack."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class RobotTelemetryMessage:
    robot_id: str
    front_distance_m: float
    left_distance_m: float
    right_distance_m: float
    battery_percent: float
    obstacle_risk: float
    stability_margin: float
    localization_confidence: float
    target_speed_mps: float
    speed_limit_mps: float
    mission_mode: str = "autonomous"
    emergency_stop: bool = False
    source_topic: str = "/robot/telemetry"
    px4_topic: str = "/robot/px4/telemetry"
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RobotCommandMessage:
    robot_id: str
    px4_mode: str
    linear_speed_mps: float
    angular_rate_rad_s: float
    brake: bool
    return_to_base: bool
    ros2_action: str
    reason: str
    source_model: str
    target_topic: str = "/robot/command"
    px4_topic: str = "/robot/px4/command"
    safety_flags: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
