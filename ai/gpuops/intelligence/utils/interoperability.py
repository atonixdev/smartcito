"""Interoperability adapters for JAX <-> PyTorch/CuPy/OpenCV pipelines."""

from __future__ import annotations

from typing import Any

import jax.numpy as jnp
from jax import dlpack as jax_dlpack


def torch_to_jax_dlpack(torch_tensor: Any) -> jnp.ndarray:
    """Convert a Torch tensor to a JAX array using DLPack."""
    capsule = torch_tensor.__dlpack__()
    return jax_dlpack.from_dlpack(capsule)


def jax_to_torch_dlpack(jax_array: jnp.ndarray, torch_module: Any) -> Any:
    """Convert a JAX array to a Torch tensor using DLPack."""
    capsule = jax_dlpack.to_dlpack(jax_array)
    return torch_module.from_dlpack(capsule)


def cv2_frame_to_jax(frame: Any) -> jnp.ndarray:
    """Convert an OpenCV frame (numpy-like) to a JAX array."""
    return jnp.asarray(frame)


def cupy_to_jax_dlpack(cupy_array: Any) -> jnp.ndarray:
    """Convert a CuPy array to a JAX array using DLPack."""
    return jax_dlpack.from_dlpack(cupy_array.toDlpack())
