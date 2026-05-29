"""UAV simulation layer built on top of flight physics primitives."""

from __future__ import annotations

import jax
import jax.numpy as jnp

from gpuops.intelligence.physics.engine import rigid_body_step, wind_model
from gpuops.intelligence.physics.uav import aerodynamic_force_vectors, compute_thrust_vector, compute_weight, net_force


@jax.jit
def simulate_uav_step(
    position: jnp.ndarray,
    velocity: jnp.ndarray,
    body_x_axis: jnp.ndarray,
    throttle: float,
    mass: float,
    max_thrust_newtons: float,
    rho: float,
    wing_area: float,
    alpha_rad: float,
    cl_alpha: float,
    cd: float,
    dt: float,
    t: float,
) -> tuple[jnp.ndarray, jnp.ndarray, jnp.ndarray]:
    wind_velocity = wind_model(t)
    air_velocity = velocity - wind_velocity

    lift_vec, drag_vec = aerodynamic_force_vectors(
        rho=rho,
        air_velocity_world=air_velocity,
        wing_area=wing_area,
        alpha_rad=alpha_rad,
        cl_alpha=cl_alpha,
        cd=cd,
    )
    thrust_vec = compute_thrust_vector(throttle, max_thrust_newtons, body_x_axis)
    weight_vec = compute_weight(mass)

    # Wind here acts through changed air-relative velocity; direct force term stays zero.
    total_force = net_force(lift_vec, drag_vec, thrust_vec, weight_vec, jnp.zeros((3,)))
    acceleration = total_force / jnp.maximum(mass, 1e-6)

    next_position, next_velocity = rigid_body_step(position, velocity, acceleration, dt)
    return next_position, next_velocity, total_force


@jax.jit
def simulate_uav_rollout(
    position0: jnp.ndarray,
    velocity0: jnp.ndarray,
    body_x_axis: jnp.ndarray,
    throttle_profile: jnp.ndarray,
    alpha_profile: jnp.ndarray,
    mass: float,
    max_thrust_newtons: float,
    rho: float,
    wing_area: float,
    cl_alpha: float,
    cd: float,
    dt: float,
) -> tuple[jnp.ndarray, jnp.ndarray, jnp.ndarray]:
    time = jnp.arange(throttle_profile.shape[0], dtype=jnp.float32) * dt

    def step(carry: tuple[jnp.ndarray, jnp.ndarray], inputs: tuple[jnp.ndarray, jnp.ndarray, jnp.ndarray]):
        position, velocity = carry
        throttle, alpha, t = inputs
        next_position, next_velocity, force = simulate_uav_step(
            position,
            velocity,
            body_x_axis,
            throttle,
            mass,
            max_thrust_newtons,
            rho,
            wing_area,
            alpha,
            cl_alpha,
            cd,
            dt,
            t,
        )
        return (next_position, next_velocity), (next_position, next_velocity, force)

    (_, _), (positions, velocities, forces) = jax.lax.scan(step, (position0, velocity0), (throttle_profile, alpha_profile, time))
    return positions, velocities, forces
