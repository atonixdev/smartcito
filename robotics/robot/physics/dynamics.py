"""JAX-based robot motion, traction, and stability dynamics."""

from __future__ import annotations

from dataclasses import dataclass

import jax
import jax.numpy as jnp


@dataclass(frozen=True, slots=True)
class RobotState:
    x: float
    y: float
    heading: float
    velocity: float
    wheel_base: float
    mass: float
    center_of_mass_height: float


@jax.jit
def compute_forward_motion(left_wheel_speed: float, right_wheel_speed: float, wheel_radius: float, dt: float) -> float:
    linear_speed = 0.5 * (left_wheel_speed + right_wheel_speed) * wheel_radius
    return linear_speed * dt


@jax.jit
def compute_turning_radius(left_wheel_speed: float, right_wheel_speed: float, wheel_base: float, wheel_radius: float) -> float:
    linear_left = left_wheel_speed * wheel_radius
    linear_right = right_wheel_speed * wheel_radius
    omega = (linear_right - linear_left) / jnp.maximum(wheel_base, 1e-6)
    v = 0.5 * (linear_left + linear_right)
    return jnp.where(jnp.abs(omega) < 1e-6, jnp.inf, v / omega)


@jax.jit
def compute_motor_torque(mass: float, desired_acceleration: float, wheel_radius: float, drivetrain_efficiency: float = 0.85) -> float:
    force = mass * desired_acceleration
    return force * wheel_radius / jnp.maximum(drivetrain_efficiency, 1e-6)


@jax.jit
def compute_acceleration_limit(traction_force: float, mass: float) -> float:
    return traction_force / jnp.maximum(mass, 1e-6)


@jax.jit
def brake_distance(speed: float, deceleration: float) -> float:
    decel = jnp.maximum(jnp.abs(deceleration), 1e-6)
    return speed**2 / (2.0 * decel)


@jax.jit
def terrain_resistance_force(mass: float, slope_angle_rad: float, rolling_resistance: float = 0.02) -> float:
    gravity = 9.81
    normal_force = mass * gravity * jnp.cos(slope_angle_rad)
    slope_force = mass * gravity * jnp.sin(slope_angle_rad)
    rolling_force = rolling_resistance * normal_force
    return slope_force + rolling_force


@jax.jit
def traction_force_limit(normal_force: float, mu: float) -> float:
    return mu * normal_force


@jax.jit
def center_of_mass_shift(load_mass: float, load_offset_m: float, robot_mass: float) -> float:
    total_mass = robot_mass + load_mass
    return (load_mass * load_offset_m) / jnp.maximum(total_mass, 1e-6)


@jax.jit
def tipping_moment(load_mass: float, load_offset_m: float, gravity: float = 9.81) -> float:
    return load_mass * gravity * load_offset_m


@jax.jit
def stability_margin(track_width: float, com_height: float, lateral_accel: float, gravity: float = 9.81) -> float:
    # Positive margin indicates stability; negative values imply rollover risk.
    return (track_width / 2.0) - com_height * (lateral_accel / jnp.maximum(gravity, 1e-6))


def build_robot_physics_contract() -> dict[str, object]:
    return {
        "physics": {
            "motion": ["forward_motion", "turning_radius", "acceleration_limit", "braking_distance"],
            "stability": ["center_of_mass_shift", "tipping_moment", "stability_margin"],
            "terrain": ["slope_resistance", "rolling_resistance", "traction_limits"],
            "energy": ["motor_torque", "battery_discharge", "runtime_estimation"],
        },
        "backend": "jax",
        "execution": ["jax.jit", "jax.vmap", "jax.lax.scan"],
    }
