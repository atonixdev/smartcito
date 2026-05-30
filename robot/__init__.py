"""Compatibility shim for the migrated robotics.robot package."""

from __future__ import annotations

from pathlib import Path
from typing import Any

_CURRENT_DIR = Path(__file__).resolve().parent
_MIGRATED_DIR = _CURRENT_DIR.parent / "robotics" / "robot"

__path__ = [str(_CURRENT_DIR), str(_MIGRATED_DIR)]

__all__ = [
    "RobotState",
    "compute_forward_motion",
    "compute_turning_radius",
    "build_robot_cloud_contract",
]


def __getattr__(name: str) -> Any:
    if name == "build_robot_cloud_contract":
        from .cloud.contracts import build_robot_cloud_contract

        return build_robot_cloud_contract
    if name in {"RobotState", "compute_forward_motion", "compute_turning_radius"}:
        from .physics.dynamics import RobotState, compute_forward_motion, compute_turning_radius

        return {
            "RobotState": RobotState,
            "compute_forward_motion": compute_forward_motion,
            "compute_turning_radius": compute_turning_radius,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
