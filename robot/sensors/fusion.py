"""Robot sensor fusion contracts and normalization helpers."""

from __future__ import annotations

import jax
import jax.numpy as jnp


@jax.jit
def normalize_robot_sensors(lidar: jnp.ndarray, imu: jnp.ndarray, gps: jnp.ndarray, encoders: jnp.ndarray) -> jnp.ndarray:
    lidar_mean = jnp.mean(lidar)
    imu_mean = jnp.mean(imu)
    gps_mean = jnp.mean(gps)
    encoder_mean = jnp.mean(encoders)
    return jnp.array([lidar_mean, imu_mean, gps_mean, encoder_mean])


def build_robot_sensor_contract() -> dict[str, object]:
    return {
        "primary": ["lidar", "stereo_camera", "depth_camera", "ultrasonic", "infrared", "imu", "gps", "wheel_encoders"],
        "advanced": ["thermal_camera", "gas_sensor", "radiation_sensor", "magnetic_sensor", "acoustic_sensor", "rf_detector"],
        "fusion_backend": "jax",
    }
