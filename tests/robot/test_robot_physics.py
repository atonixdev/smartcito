from __future__ import annotations

import jax.numpy as jnp

from robot.physics.dynamics import (
    brake_distance,
    build_robot_physics_contract,
    compute_acceleration_limit,
    compute_forward_motion,
    compute_motor_torque,
    compute_turning_radius,
)
from robot.physics.energy import battery_discharge_voltage, estimate_runtime_seconds, motor_power_draw
from robot.physics.traction import estimate_slip_angle, slip_ratio, wheel_traction_force


def test_robot_motion_and_turning() -> None:
    assert compute_forward_motion(8.0, 8.0, 0.1, 2.0) == 1.6
    turning_radius = float(compute_turning_radius(8.0, 10.0, 0.5, 0.1))
    assert turning_radius != 0.0
    assert turning_radius != float("inf")


def test_robot_force_and_energy_helpers() -> None:
    torque = float(compute_motor_torque(20.0, 1.5, 0.08))
    traction = float(wheel_traction_force(120.0, 0.7))
    accel_limit = float(compute_acceleration_limit(traction, 20.0))
    runtime = float(estimate_runtime_seconds(360.0, 180.0))
    voltage = float(battery_discharge_voltage(24.0, 0.05, 10.0))
    power = float(motor_power_draw(12.0, 4.0))
    assert torque > 0.0
    assert traction > 0.0
    assert accel_limit > 0.0
    assert runtime > 0.0
    assert voltage < 24.0
    assert power > 0.0


def test_robot_stability_and_slip_helpers() -> None:
    assert float(brake_distance(3.0, 1.5)) > 0.0
    assert float(slip_ratio(2.5, 2.0)) > 0.0
    assert float(estimate_slip_angle(0.2, 1.0)) > 0.0


def test_robot_physics_contract() -> None:
    contract = build_robot_physics_contract()
    assert contract["backend"] == "jax"
    assert "motion" in contract["physics"]
