"""Physics-based interception helpers for anti-drone workflows."""

from __future__ import annotations

import jax
import jax.numpy as jnp


@jax.jit
def predict_constant_velocity(position: jnp.ndarray, velocity: jnp.ndarray, horizon_s: float) -> jnp.ndarray:
    return position + velocity * horizon_s


@jax.jit
def interception_vector(
    ownship_position: jnp.ndarray,
    target_position: jnp.ndarray,
    target_velocity: jnp.ndarray,
    horizon_s: float,
) -> jnp.ndarray:
    predicted_target = predict_constant_velocity(target_position, target_velocity, horizon_s)
    return predicted_target - ownship_position


@jax.jit
def required_intercept_speed(distance_vec: jnp.ndarray, time_to_intercept_s: float) -> float:
    distance = jnp.linalg.norm(distance_vec)
    return distance / jnp.maximum(time_to_intercept_s, 1e-6)
