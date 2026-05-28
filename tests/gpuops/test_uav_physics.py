from __future__ import annotations

import jax.numpy as jnp

from gpuops.intelligence.physics.simulation import simulate_uav_step
from gpuops.intelligence.physics.uav import compute_lift, lift_coefficient_with_stall


def test_compute_lift_matches_reference_formula() -> None:
    lift = compute_lift(1.225, 20.0, 0.8, 1.1)
    expected = 0.5 * 1.225 * (20.0**2) * 0.8 * 1.1
    assert abs(float(lift) - expected) < 1e-5


def test_stall_model_reduces_lift_post_stall() -> None:
    pre_stall = float(lift_coefficient_with_stall(0.1, cl_alpha=5.2))
    post_stall = float(lift_coefficient_with_stall(0.45, cl_alpha=5.2))
    assert post_stall < pre_stall


def test_simulation_step_produces_valid_vectors() -> None:
    p1, v1, f1 = simulate_uav_step(
        position=jnp.array([0.0, 0.0, 10.0]),
        velocity=jnp.array([15.0, 0.0, 0.0]),
        body_x_axis=jnp.array([1.0, 0.0, 0.0]),
        throttle=0.5,
        mass=1.8,
        max_thrust_newtons=30.0,
        rho=1.225,
        wing_area=0.4,
        alpha_rad=0.1,
        cl_alpha=5.2,
        cd=0.04,
        dt=0.02,
        t=0.0,
    )
    assert p1.shape == (3,)
    assert v1.shape == (3,)
    assert f1.shape == (3,)
