"""JAX-first physics routines for ORCA aerial and robotic dynamics."""

from __future__ import annotations

import jax
import jax.numpy as jnp


@jax.jit
def compute_lift(rho: float, v: float, surface_area: float, lift_coefficient: float) -> float:
    return 0.5 * rho * v**2 * surface_area * lift_coefficient


batch_compute_lift = jax.jit(jax.vmap(compute_lift, in_axes=(None, 0, None, None)))


@jax.jit
def compute_drag(rho: float, v: float, surface_area: float, drag_coefficient: float) -> float:
    return 0.5 * rho * v**2 * surface_area * drag_coefficient


@jax.jit
def compute_thrust(mass: float, acceleration: jnp.ndarray, drag_force: float, gravity: float = 9.81) -> jnp.ndarray:
    return mass * (acceleration + jnp.array([0.0, 0.0, gravity])) + jnp.array([0.0, 0.0, drag_force])


@jax.jit
def compute_torque(moment_arm: jnp.ndarray, force: jnp.ndarray) -> jnp.ndarray:
    return jnp.cross(moment_arm, force)


@jax.jit
def rigid_body_step(position: jnp.ndarray, velocity: jnp.ndarray, acceleration: jnp.ndarray, dt: float) -> tuple[jnp.ndarray, jnp.ndarray]:
    new_velocity = velocity + acceleration * dt
    new_position = position + new_velocity * dt
    return new_position, new_velocity


@jax.jit
def _wind_component(base: float, t: float, freq: float, phase: float) -> float:
    return base * jnp.sin(freq * t + phase)


@jax.jit
def wind_model(t: float, base_speed: float = 2.0) -> jnp.ndarray:
    return jnp.array([
        _wind_component(base_speed, t, 0.7, 0.0),
        _wind_component(base_speed, t, 1.1, 1.3),
        _wind_component(base_speed * 0.3, t, 0.5, 0.5),
    ])


@jax.jit
def rollout_trajectory(position0: jnp.ndarray, velocity0: jnp.ndarray, control_accel: jnp.ndarray, dt: float) -> tuple[jnp.ndarray, jnp.ndarray]:
    def step(carry: tuple[jnp.ndarray, jnp.ndarray], accel: jnp.ndarray):
        position, velocity = carry
        new_position, new_velocity = rigid_body_step(position, velocity, accel, dt)
        return (new_position, new_velocity), (new_position, new_velocity)

    (_, _), (positions, velocities) = jax.lax.scan(step, (position0, velocity0), control_accel)
    return positions, velocities


@jax.jit
def _trajectory_cost(controls: jnp.ndarray, target: jnp.ndarray, position0: jnp.ndarray, velocity0: jnp.ndarray, dt: float) -> float:
    positions, _ = rollout_trajectory(position0, velocity0, controls, dt)
    terminal_error = jnp.sum((positions[-1] - target) ** 2)
    energy_penalty = 0.01 * jnp.sum(controls**2)
    return terminal_error + energy_penalty


@jax.jit
def optimize_control_signals(
    controls: jnp.ndarray,
    target: jnp.ndarray,
    position0: jnp.ndarray,
    velocity0: jnp.ndarray,
    dt: float,
    learning_rate: float = 0.05,
    steps: int = 25,
) -> jnp.ndarray:
    grad_fn = jax.grad(_trajectory_cost)

    def body_fn(_: int, current: jnp.ndarray) -> jnp.ndarray:
        grads = grad_fn(current, target, position0, velocity0, dt)
        return current - learning_rate * grads

    return jax.lax.fori_loop(0, steps, body_fn, controls)
