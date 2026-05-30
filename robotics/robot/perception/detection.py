"""Heuristic perception helpers for robot obstacles, terrain, and targets."""

from __future__ import annotations

import jax
import jax.numpy as jnp


@jax.jit
def detect_obstacle_risk(distance_m: float, speed_mps: float, braking_distance_m: float) -> float:
    urgency = jnp.clip(1.0 - distance_m / jnp.maximum(braking_distance_m, 1e-6), 0.0, 1.0)
    speed_factor = jnp.clip(speed_mps / 10.0, 0.0, 1.0)
    return jnp.clip(0.7 * urgency + 0.3 * speed_factor, 0.0, 1.0)


@jax.jit
def terrain_classification_score(slope_rad: float, roughness: float, traction_margin: float) -> jnp.ndarray:
    terrain_type = jnp.where(slope_rad > 0.35, 3, jnp.where(roughness > 0.5, 2, 1))
    risk = jnp.clip(1.0 - traction_margin, 0.0, 1.0)
    return jnp.array([terrain_type, roughness, risk])


def build_robot_perception_contract() -> dict[str, object]:
    return {
        "sensors": ["lidar", "stereo_camera", "depth_camera", "ultrasonic", "infrared", "imu", "gps", "wheel_encoders"],
        "targets": ["humans", "vehicles", "drones", "animals", "obstacles", "terrain"],
        "outputs": ["obstacle_risk", "terrain_score", "target_tracks"],
    }
