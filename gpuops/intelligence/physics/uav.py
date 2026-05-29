"""UAV flight physics primitives implemented with JAX."""

from __future__ import annotations

import jax
import jax.numpy as jnp


@jax.jit
def compute_lift(rho: float, airspeed: float, wing_area: float, cl: float) -> float:
    return 0.5 * rho * airspeed**2 * wing_area * cl


@jax.jit
def compute_drag(rho: float, airspeed: float, wing_area: float, cd: float) -> float:
    return 0.5 * rho * airspeed**2 * wing_area * cd


@jax.jit
def compute_weight(mass: float, gravity: float = 9.81) -> jnp.ndarray:
    return jnp.array([0.0, 0.0, -mass * gravity])


@jax.jit
def compute_thrust_vector(throttle: float, max_thrust_newtons: float, body_x_axis: jnp.ndarray) -> jnp.ndarray:
    throttle_clamped = jnp.clip(throttle, 0.0, 1.0)
    direction = body_x_axis / jnp.maximum(jnp.linalg.norm(body_x_axis), 1e-6)
    return direction * (throttle_clamped * max_thrust_newtons)


@jax.jit
def lift_coefficient_with_stall(alpha_rad: float, cl_alpha: float, cl_max: float = 1.4, stall_alpha_rad: float = 0.26) -> float:
    linear_cl = cl_alpha * alpha_rad
    saturated = jnp.clip(linear_cl, -cl_max, cl_max)
    post_stall = cl_max * jnp.exp(-8.0 * jnp.maximum(jnp.abs(alpha_rad) - stall_alpha_rad, 0.0))
    return jnp.where(jnp.abs(alpha_rad) > stall_alpha_rad, jnp.sign(alpha_rad) * post_stall, saturated)


@jax.jit
def aerodynamic_force_vectors(
    rho: float,
    air_velocity_world: jnp.ndarray,
    wing_area: float,
    alpha_rad: float,
    cl_alpha: float,
    cd: float,
    lift_axis_world: jnp.ndarray = jnp.array([0.0, 0.0, 1.0]),
) -> tuple[jnp.ndarray, jnp.ndarray]:
    airspeed = jnp.maximum(jnp.linalg.norm(air_velocity_world), 1e-6)
    cl = lift_coefficient_with_stall(alpha_rad, cl_alpha)
    lift_mag = compute_lift(rho, airspeed, wing_area, cl)
    drag_mag = compute_drag(rho, airspeed, wing_area, cd)

    drag_dir = -air_velocity_world / airspeed
    lift_dir = lift_axis_world / jnp.maximum(jnp.linalg.norm(lift_axis_world), 1e-6)

    return lift_dir * lift_mag, drag_dir * drag_mag


@jax.jit
def body_moment_vector(
    rho: float,
    airspeed: float,
    wing_area: float,
    wingspan: float,
    mean_chord: float,
    roll_coeff: float,
    pitch_coeff: float,
    yaw_coeff: float,
) -> jnp.ndarray:
    qbar = 0.5 * rho * airspeed**2
    roll_m = qbar * wing_area * wingspan * roll_coeff
    pitch_m = qbar * wing_area * mean_chord * pitch_coeff
    yaw_m = qbar * wing_area * wingspan * yaw_coeff
    return jnp.array([roll_m, pitch_m, yaw_m])


@jax.jit
def net_force(
    lift_vec: jnp.ndarray,
    drag_vec: jnp.ndarray,
    thrust_vec: jnp.ndarray,
    weight_vec: jnp.ndarray,
    wind_force_vec: jnp.ndarray,
) -> jnp.ndarray:
    return lift_vec + drag_vec + thrust_vec + weight_vec + wind_force_vec


batch_net_force = jax.jit(jax.vmap(net_force, in_axes=(0, 0, 0, 0, 0)))
