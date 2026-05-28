"""Traction and slip helpers for ground robots."""

from __future__ import annotations

import jax
import jax.numpy as jnp


@jax.jit
def wheel_traction_force(normal_force: float, mu: float) -> float:
    return mu * normal_force


@jax.jit
def slip_ratio(wheel_speed_mps: float, ground_speed_mps: float) -> float:
    return (wheel_speed_mps - ground_speed_mps) / jnp.maximum(jnp.abs(wheel_speed_mps), 1e-6)


@jax.jit
def estimate_slip_angle(lateral_velocity: float, longitudinal_velocity: float) -> float:
    return jnp.arctan2(lateral_velocity, jnp.maximum(longitudinal_velocity, 1e-6))
