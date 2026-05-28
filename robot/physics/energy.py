"""Battery and motor energy helpers for robot motion planning."""

from __future__ import annotations

import jax
import jax.numpy as jnp


@jax.jit
def motor_power_draw(torque_nm: float, angular_speed_rad_s: float, efficiency: float = 0.85) -> float:
    mechanical_power = torque_nm * angular_speed_rad_s
    return mechanical_power / jnp.maximum(efficiency, 1e-6)


@jax.jit
def battery_discharge_voltage(open_circuit_voltage: float, internal_resistance: float, current_a: float) -> float:
    return open_circuit_voltage - internal_resistance * current_a


@jax.jit
def estimate_runtime_seconds(battery_wh: float, average_power_w: float) -> float:
    return battery_wh * 3600.0 / jnp.maximum(average_power_w, 1e-6)
