"""JAX filters and fusion blocks for mapping and localization."""

from __future__ import annotations

import jax
import jax.numpy as jnp


@jax.jit
def kalman_predict(x: jnp.ndarray, p: jnp.ndarray, a: jnp.ndarray, q: jnp.ndarray) -> tuple[jnp.ndarray, jnp.ndarray]:
    x_pred = a @ x
    p_pred = a @ p @ a.T + q
    return x_pred, p_pred


@jax.jit
def kalman_update(
    x_pred: jnp.ndarray,
    p_pred: jnp.ndarray,
    z: jnp.ndarray,
    h: jnp.ndarray,
    r: jnp.ndarray,
) -> tuple[jnp.ndarray, jnp.ndarray]:
    innovation = z - h @ x_pred
    s = h @ p_pred @ h.T + r
    k = p_pred @ h.T @ jnp.linalg.inv(s)
    x_new = x_pred + k @ innovation
    i = jnp.eye(p_pred.shape[0], dtype=p_pred.dtype)
    p_new = (i - k @ h) @ p_pred
    return x_new, p_new


@jax.jit
def particle_filter_predict(particles: jnp.ndarray, control_delta: jnp.ndarray) -> jnp.ndarray:
    return particles + control_delta


@jax.jit
def particle_filter_update(particles: jnp.ndarray, measurement: jnp.ndarray, sigma: float = 1.0) -> jnp.ndarray:
    sq_dist = jnp.sum((particles - measurement) ** 2, axis=1)
    weights = jnp.exp(-0.5 * sq_dist / (sigma**2))
    return weights / jnp.sum(weights)


@jax.jit
def gps_fusion(readings: jnp.ndarray, confidences: jnp.ndarray) -> jnp.ndarray:
    normalized = confidences / jnp.sum(confidences)
    return jnp.sum(readings * normalized[:, None], axis=0)


@jax.jit
def slam_pose_step(poses: jnp.ndarray, odometry_deltas: jnp.ndarray) -> jnp.ndarray:
    def step(carry: jnp.ndarray, delta: jnp.ndarray):
        new_pose = carry + delta
        return new_pose, new_pose

    _, trajectory = jax.lax.scan(step, poses[0], odometry_deltas)
    return trajectory
