"""JAX camera pipeline primitives for ORCA intelligence."""

from __future__ import annotations

import jax
import jax.numpy as jnp


@jax.jit
def preprocess_image(image: jnp.ndarray) -> jnp.ndarray:
    image = image.astype(jnp.float32) / 255.0
    if image.ndim == 3 and image.shape[-1] == 3:
        return jnp.mean(image, axis=-1)
    return image


@jax.jit
def extract_grad_features(gray_image: jnp.ndarray) -> tuple[jnp.ndarray, jnp.ndarray]:
    gx = gray_image[:, 1:] - gray_image[:, :-1]
    gy = gray_image[1:, :] - gray_image[:-1, :]
    return gx, gy


@jax.jit
def optical_flow_delta(frame_t: jnp.ndarray, frame_t1: jnp.ndarray) -> jnp.ndarray:
    return frame_t1 - frame_t


@jax.jit
def segment_by_threshold(gray_image: jnp.ndarray, threshold: float = 0.5) -> jnp.ndarray:
    return (gray_image > threshold).astype(jnp.float32)


@jax.jit
def depth_from_disparity(focal_length: float, baseline: float, disparity: jnp.ndarray, eps: float = 1e-6) -> jnp.ndarray:
    return (focal_length * baseline) / jnp.maximum(disparity, eps)


def _calibration_loss(focal: float, baseline: float, disparity: jnp.ndarray, target_depth: jnp.ndarray) -> float:
    pred = depth_from_disparity(focal, baseline, disparity)
    return jnp.mean((pred - target_depth) ** 2)


@jax.jit
def optimize_focal_length(
    focal_init: float,
    baseline: float,
    disparity: jnp.ndarray,
    target_depth: jnp.ndarray,
    learning_rate: float = 1e-3,
    steps: int = 50,
) -> float:
    grad_fn = jax.grad(_calibration_loss)

    def body_fn(_: int, focal: float) -> float:
        return focal - learning_rate * grad_fn(focal, baseline, disparity, target_depth)

    return jax.lax.fori_loop(0, steps, body_fn, focal_init)
