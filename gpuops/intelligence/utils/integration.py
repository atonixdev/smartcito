"""Integration stubs for ROS2/PX4 control handoff from JAX computations."""

from __future__ import annotations

from typing import Any

import jax.numpy as jnp


def ros2_command_from_control(control_vec: jnp.ndarray) -> dict[str, float]:
    """Translate JAX control vector to a ROS2-friendly dictionary payload."""
    return {
        "vx": float(control_vec[0]),
        "vy": float(control_vec[1]),
        "vz": float(control_vec[2]),
        "yaw_rate": float(control_vec[3]) if control_vec.shape[0] > 3 else 0.0,
    }


def px4_setpoint_from_control(control_vec: jnp.ndarray) -> dict[str, Any]:
    """Translate JAX control vector to a PX4 setpoint structure."""
    return {
        "position": [float(control_vec[0]), float(control_vec[1]), float(control_vec[2])],
        "velocity": [0.0, 0.0, 0.0],
        "acceleration": [0.0, 0.0, 0.0],
        "yaw": float(control_vec[3]) if control_vec.shape[0] > 3 else 0.0,
    }
