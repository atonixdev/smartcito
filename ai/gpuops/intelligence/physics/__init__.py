"""GPUOPS physics engine primitives."""

from gpuops.intelligence.physics.engine import (
    batch_compute_lift,
    compute_drag,
    compute_lift,
    compute_thrust,
    compute_torque,
    optimize_control_signals,
    rigid_body_step,
    rollout_trajectory,
)
from gpuops.intelligence.physics.simulation import simulate_uav_rollout, simulate_uav_step
from gpuops.intelligence.physics.uav import (
    aerodynamic_force_vectors,
    batch_net_force,
    body_moment_vector,
    compute_thrust_vector,
    compute_weight,
    lift_coefficient_with_stall,
    net_force,
)

__all__ = [
    "compute_lift",
    "batch_compute_lift",
    "compute_drag",
    "compute_thrust",
    "compute_torque",
    "rigid_body_step",
    "rollout_trajectory",
    "optimize_control_signals",
    "compute_weight",
    "compute_thrust_vector",
    "lift_coefficient_with_stall",
    "aerodynamic_force_vectors",
    "body_moment_vector",
    "net_force",
    "batch_net_force",
    "simulate_uav_step",
    "simulate_uav_rollout",
]
