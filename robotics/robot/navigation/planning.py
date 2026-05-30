"""Path planning helpers for autonomous ground robots."""

from __future__ import annotations

import jax
import jax.numpy as jnp

from gpuops.intelligence.solvers.graph import shortest_path_scores


@jax.jit
def hybrid_a_star_score(g_cost: float, heuristic_cost: float, turning_cost: float) -> float:
    return g_cost + heuristic_cost + turning_cost


@jax.jit
def rrt_star_step(nearest_node: jnp.ndarray, sample: jnp.ndarray, step_size: float) -> jnp.ndarray:
    direction = sample - nearest_node
    norm = jnp.maximum(jnp.linalg.norm(direction), 1e-6)
    return nearest_node + direction / norm * step_size


@jax.jit
def plan_path_grid(cost_grid: jnp.ndarray, start_idx: int) -> jnp.ndarray:
    return shortest_path_scores(cost_grid, start_idx)


def build_navigation_contract() -> dict[str, object]:
    return {
        "planning": ["A*", "RRT*", "D* Lite", "Hybrid A*", "MPC"],
        "avoidance": ["VFH+", "DWA", "potential_fields"],
        "localization": ["EKF", "UKF", "particle_filter", "SLAM"],
        "terrain_adaptation": ["slope_detection", "roughness_detection", "traction_estimation"],
    }
