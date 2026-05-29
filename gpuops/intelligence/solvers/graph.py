"""JAX graph and distance solver helpers."""

from __future__ import annotations

import jax
import jax.numpy as jnp


@jax.jit
def shortest_path_scores(cost_matrix: jnp.ndarray, start_idx: int, iterations: int = 64) -> jnp.ndarray:
    n = cost_matrix.shape[0]
    inf = jnp.array(1e12, dtype=cost_matrix.dtype)
    dist = jnp.full((n,), inf).at[start_idx].set(0.0)

    def step(current: jnp.ndarray, _unused: None):
        propagated = current[:, None] + cost_matrix
        updated = jnp.minimum(current, jnp.min(propagated, axis=0))
        return updated, updated

    out, _ = jax.lax.scan(step, dist, xs=None, length=iterations)
    return out


@jax.jit
def _pairwise(a: jnp.ndarray, b: jnp.ndarray) -> float:
    return jnp.linalg.norm(a - b)


batch_pairwise_distance = jax.jit(jax.vmap(jax.vmap(_pairwise, in_axes=(None, 0)), in_axes=(0, None)))
