"""JAX mapping math components for A*, Dijkstra, and RRT/RRT*."""

from __future__ import annotations

import jax
import jax.numpy as jnp


@jax.jit
def astar_score(g_cost: jnp.ndarray, node_xy: jnp.ndarray, goal_xy: jnp.ndarray) -> jnp.ndarray:
    heuristic = jnp.linalg.norm(node_xy - goal_xy, axis=-1)
    return g_cost + heuristic


@jax.jit
def dijkstra_relaxation(adj_matrix: jnp.ndarray, start_index: int, iterations: int = 64) -> jnp.ndarray:
    n = adj_matrix.shape[0]
    inf = jnp.array(1e12, dtype=adj_matrix.dtype)
    distances = jnp.full((n,), inf)
    distances = distances.at[start_index].set(0.0)

    def relax_step(current: jnp.ndarray, _unused: None):
        candidate = current[:, None] + adj_matrix
        updated = jnp.minimum(current, jnp.min(candidate, axis=0))
        return updated, updated

    final_dist, _ = jax.lax.scan(relax_step, distances, xs=None, length=iterations)
    return final_dist


@jax.jit
def rrt_expand(nearest_node: jnp.ndarray, random_sample: jnp.ndarray, step_size: float) -> jnp.ndarray:
    direction = random_sample - nearest_node
    norm = jnp.maximum(jnp.linalg.norm(direction), 1e-6)
    return nearest_node + direction / norm * step_size


@jax.jit
def rrt_star_rewire(candidate_nodes: jnp.ndarray, new_node: jnp.ndarray, current_costs: jnp.ndarray) -> jnp.ndarray:
    distances = jnp.linalg.norm(candidate_nodes - new_node, axis=1)
    potential_costs = current_costs + distances
    return jnp.minimum(current_costs, potential_costs)
