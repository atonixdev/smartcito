"""Autopilot-oriented UAV control helpers."""

from __future__ import annotations

import jax
import jax.numpy as jnp

from gpuops.intelligence.physics.uav import compute_lift


@jax.jit
def pitch_stabilization_command(pitch_setpoint: float, pitch_angle: float, pitch_rate: float, kp: float, kd: float) -> float:
    pitch_error = pitch_setpoint - pitch_angle
    return kp * pitch_error - kd * pitch_rate


@jax.jit
def roll_stabilization_command(roll_setpoint: float, roll_angle: float, roll_rate: float, kp: float, kd: float) -> float:
    roll_error = roll_setpoint - roll_angle
    return kp * roll_error - kd * roll_rate


@jax.jit
def yaw_stabilization_command(yaw_setpoint: float, yaw_angle: float, yaw_rate: float, kp: float, kd: float) -> float:
    yaw_error = yaw_setpoint - yaw_angle
    return kp * yaw_error - kd * yaw_rate


@jax.jit
def altitude_hold_pitch_command(
    altitude_setpoint: float,
    altitude: float,
    vertical_speed: float,
    rho: float,
    airspeed: float,
    wing_area: float,
    mass: float,
    cl_alpha: float,
    kp_alt: float,
    kd_alt: float,
) -> float:
    # Use lift requirement to derive a target angle of attack, then treat AoA as pitch setpoint proxy.
    alt_error = altitude_setpoint - altitude
    desired_vertical_force = kp_alt * alt_error - kd_alt * vertical_speed
    required_lift = mass * 9.81 + desired_vertical_force

    qbar_s = 0.5 * rho * jnp.maximum(airspeed, 1e-3) ** 2 * wing_area
    cl_required = required_lift / jnp.maximum(qbar_s, 1e-6)
    alpha_target = cl_required / jnp.maximum(cl_alpha, 1e-6)
    return jnp.clip(alpha_target, -0.35, 0.35)


@jax.jit
def waypoint_guidance_heading(current_xy: jnp.ndarray, waypoint_xy: jnp.ndarray) -> float:
    delta = waypoint_xy - current_xy
    return jnp.arctan2(delta[1], delta[0])


batch_pitch_stabilization = jax.jit(jax.vmap(pitch_stabilization_command, in_axes=(0, 0, 0, None, None)))
