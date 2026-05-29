from __future__ import annotations

import jax.numpy as jnp

from gpuops.intelligence.distance.ekf_uav import ekf_predict_uav, fuse_uav_sensors
from gpuops.intelligence.robotics.uav_control import altitude_hold_pitch_command, pitch_stabilization_command


def test_pitch_stabilization_sign() -> None:
    cmd = pitch_stabilization_command(
        pitch_setpoint=0.2,
        pitch_angle=0.1,
        pitch_rate=0.0,
        kp=2.0,
        kd=0.2,
    )
    assert float(cmd) > 0.0


def test_altitude_hold_pitch_command_limits() -> None:
    cmd = altitude_hold_pitch_command(
        altitude_setpoint=120.0,
        altitude=100.0,
        vertical_speed=-2.0,
        rho=1.225,
        airspeed=20.0,
        wing_area=0.5,
        mass=2.0,
        cl_alpha=5.0,
        kp_alt=0.2,
        kd_alt=0.1,
    )
    assert -0.35 <= float(cmd) <= 0.35


def test_ekf_predict_and_fuse_shapes() -> None:
    x0 = jnp.zeros((9,))
    p0 = jnp.eye(9) * 0.5
    q = jnp.eye(9) * 0.01

    x_pred, p_pred = ekf_predict_uav(
        x0,
        p0,
        imu_accel=jnp.array([0.0, 0.0, -0.1]),
        imu_gyro=jnp.array([0.01, 0.02, 0.03]),
        dt=0.02,
        q=q,
    )

    x_new, p_new = fuse_uav_sensors(
        x_pred,
        p_pred,
        gps_position=jnp.array([1.0, 2.0, 100.0]),
        gps_velocity=jnp.array([12.0, 0.5, -0.2]),
        magnetometer_yaw=0.12,
        barometer_altitude=99.8,
        airspeed=12.1,
        r_gps=jnp.eye(6) * 0.2,
        r_mag=jnp.eye(1) * 0.05,
        r_baro=jnp.eye(1) * 0.1,
        r_airspeed=jnp.eye(1) * 0.2,
    )

    assert x_new.shape == (9,)
    assert p_new.shape == (9, 9)
