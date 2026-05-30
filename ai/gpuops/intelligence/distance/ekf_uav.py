"""EKF-based UAV sensor fusion for position, velocity, and attitude."""

from __future__ import annotations

import jax
import jax.numpy as jnp


# State: [x, y, z, vx, vy, vz, roll, pitch, yaw]


@jax.jit
def _predict_state(x: jnp.ndarray, imu_accel: jnp.ndarray, imu_gyro: jnp.ndarray, dt: float) -> jnp.ndarray:
    pos = x[0:3] + x[3:6] * dt + 0.5 * imu_accel * dt**2
    vel = x[3:6] + imu_accel * dt
    att = x[6:9] + imu_gyro * dt
    return jnp.concatenate([pos, vel, att])


@jax.jit
def ekf_predict_uav(x: jnp.ndarray, p: jnp.ndarray, imu_accel: jnp.ndarray, imu_gyro: jnp.ndarray, dt: float, q: jnp.ndarray) -> tuple[jnp.ndarray, jnp.ndarray]:
    x_pred = _predict_state(x, imu_accel, imu_gyro, dt)

    f = jnp.eye(9)
    f = f.at[0, 3].set(dt)
    f = f.at[1, 4].set(dt)
    f = f.at[2, 5].set(dt)

    p_pred = f @ p @ f.T + q
    return x_pred, p_pred


@jax.jit
def _ekf_update(x_pred: jnp.ndarray, p_pred: jnp.ndarray, z: jnp.ndarray, h: jnp.ndarray, r: jnp.ndarray) -> tuple[jnp.ndarray, jnp.ndarray]:
    innovation = z - h @ x_pred
    s = h @ p_pred @ h.T + r
    k = p_pred @ h.T @ jnp.linalg.inv(s)
    x_new = x_pred + k @ innovation
    p_new = (jnp.eye(p_pred.shape[0]) - k @ h) @ p_pred
    return x_new, p_new


@jax.jit
def fuse_uav_sensors(
    x_pred: jnp.ndarray,
    p_pred: jnp.ndarray,
    gps_position: jnp.ndarray,
    gps_velocity: jnp.ndarray,
    magnetometer_yaw: float,
    barometer_altitude: float,
    airspeed: float,
    r_gps: jnp.ndarray,
    r_mag: jnp.ndarray,
    r_baro: jnp.ndarray,
    r_airspeed: jnp.ndarray,
) -> tuple[jnp.ndarray, jnp.ndarray]:
    # GPS update (x, y, z, vx, vy, vz)
    z_gps = jnp.concatenate([gps_position, gps_velocity])
    h_gps = jnp.zeros((6, 9))
    h_gps = h_gps.at[0, 0].set(1.0)
    h_gps = h_gps.at[1, 1].set(1.0)
    h_gps = h_gps.at[2, 2].set(1.0)
    h_gps = h_gps.at[3, 3].set(1.0)
    h_gps = h_gps.at[4, 4].set(1.0)
    h_gps = h_gps.at[5, 5].set(1.0)
    x1, p1 = _ekf_update(x_pred, p_pred, z_gps, h_gps, r_gps)

    # Magnetometer yaw update
    z_mag = jnp.array([magnetometer_yaw])
    h_mag = jnp.zeros((1, 9)).at[0, 8].set(1.0)
    x2, p2 = _ekf_update(x1, p1, z_mag, h_mag, r_mag)

    # Barometer altitude update (z)
    z_baro = jnp.array([barometer_altitude])
    h_baro = jnp.zeros((1, 9)).at[0, 2].set(1.0)
    x3, p3 = _ekf_update(x2, p2, z_baro, h_baro, r_baro)

    # Airspeed update (||v||)
    vel = x3[3:6]
    speed_pred = jnp.linalg.norm(vel)
    h_air = jnp.zeros((1, 9))
    denom = jnp.maximum(speed_pred, 1e-6)
    h_air = h_air.at[0, 3].set(vel[0] / denom)
    h_air = h_air.at[0, 4].set(vel[1] / denom)
    h_air = h_air.at[0, 5].set(vel[2] / denom)
    x4, p4 = _ekf_update(x3, p3, jnp.array([airspeed]), h_air, r_airspeed)

    return x4, p4
