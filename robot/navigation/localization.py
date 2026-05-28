"""Robot localization helpers using the shared JAX EKF-style math."""

from __future__ import annotations

import jax.numpy as jnp

from gpuops.intelligence.distance.ekf_uav import ekf_predict_uav


def ekf_localize(
    state: jnp.ndarray,
    covariance: jnp.ndarray,
    imu_accel: jnp.ndarray,
    imu_gyro: jnp.ndarray,
    gps_position: jnp.ndarray,
    gps_velocity: jnp.ndarray,
    dt: float,
) -> tuple[jnp.ndarray, jnp.ndarray]:
    q = jnp.eye(state.shape[0]) * 0.02
    x_pred, p_pred = ekf_predict_uav(state, covariance, imu_accel, imu_gyro, dt, q)
    # Reuse the robot state's first six entries for pose + velocity.
    x_pred = x_pred.at[0:3].set(gps_position)
    x_pred = x_pred.at[3:6].set(gps_velocity)
    return x_pred, p_pred


def build_robot_localization_contract() -> dict[str, object]:
    return {
        "state": ["x", "y", "z", "vx", "vy", "vz", "roll", "pitch", "yaw"],
        "filters": ["EKF", "UKF", "particle_filter"],
        "inputs": ["imu", "gps", "magnetometer", "wheel_encoders", "lidar", "camera_odometry"],
    }
