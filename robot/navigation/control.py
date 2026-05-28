"""Reactive robot navigation control helpers."""

from __future__ import annotations

import jax
import jax.numpy as jnp


@jax.jit
def obstacle_avoidance_command(front_distance_m: float, left_distance_m: float, right_distance_m: float) -> jnp.ndarray:
    turn_left = jnp.where(right_distance_m > left_distance_m, 1.0, -1.0)
    slowdown = jnp.clip(1.0 - front_distance_m / 2.0, 0.0, 1.0)
    forward = 1.0 - slowdown
    return jnp.array([forward, turn_left * slowdown])


@jax.jit
def smooth_return_to_base(current_xy: jnp.ndarray, base_xy: jnp.ndarray, max_speed: float) -> jnp.ndarray:
    direction = base_xy - current_xy
    distance = jnp.maximum(jnp.linalg.norm(direction), 1e-6)
    return direction / distance * jnp.minimum(distance, max_speed)
