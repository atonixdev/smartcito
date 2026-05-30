"""JAX optimization helpers for ORCA intelligence workloads."""

from __future__ import annotations

from collections.abc import Callable

import jax
import jax.numpy as jnp


@jax.jit
def gradient_descent_step(x: jnp.ndarray, grad: jnp.ndarray, learning_rate: float) -> jnp.ndarray:
    return x - learning_rate * grad


def gradient_descent(
    objective_fn: Callable[[jnp.ndarray], float],
    x0: jnp.ndarray,
    learning_rate: float = 1e-2,
    steps: int = 100,
) -> jnp.ndarray:
    grad_fn = jax.grad(objective_fn)

    @jax.jit
    def run(init_x: jnp.ndarray) -> jnp.ndarray:
        def body_fn(_: int, x: jnp.ndarray) -> jnp.ndarray:
            return gradient_descent_step(x, grad_fn(x), learning_rate)

        return jax.lax.fori_loop(0, steps, body_fn, init_x)

    return run(x0)


@jax.jit
def batch_gradient_descent(params: jnp.ndarray, grads: jnp.ndarray, learning_rate: float = 1e-2) -> jnp.ndarray:
    return jax.vmap(gradient_descent_step, in_axes=(0, 0, None))(params, grads, learning_rate)
