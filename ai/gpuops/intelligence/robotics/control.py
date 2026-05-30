"""JAX robotics control modules for kinematics, PID, and MPC."""

from __future__ import annotations

import jax
import jax.numpy as jnp


@jax.jit
def diff_drive_kinematics(state: jnp.ndarray, wheel_vel: jnp.ndarray, wheel_base: float, dt: float) -> jnp.ndarray:
    x, y, theta = state
    vl, vr = wheel_vel
    v = 0.5 * (vl + vr)
    omega = (vr - vl) / wheel_base
    x_new = x + v * jnp.cos(theta) * dt
    y_new = y + v * jnp.sin(theta) * dt
    theta_new = theta + omega * dt
    return jnp.array([x_new, y_new, theta_new])


@jax.jit
def pid_step(error: float, integral: float, prev_error: float, kp: float, ki: float, kd: float, dt: float) -> tuple[float, float]:
    new_integral = integral + error * dt
    derivative = (error - prev_error) / jnp.maximum(dt, 1e-6)
    control = kp * error + ki * new_integral + kd * derivative
    return control, new_integral


@jax.jit
def rollout_dynamics(state0: jnp.ndarray, controls: jnp.ndarray, wheel_base: float, dt: float) -> jnp.ndarray:
    def step(carry: jnp.ndarray, u: jnp.ndarray):
        new_state = diff_drive_kinematics(carry, u, wheel_base, dt)
        return new_state, new_state

    _, states = jax.lax.scan(step, state0, controls)
    return states


def _mpc_cost(controls: jnp.ndarray, state0: jnp.ndarray, target_xy: jnp.ndarray, wheel_base: float, dt: float) -> float:
    states = rollout_dynamics(state0, controls, wheel_base, dt)
    terminal_cost = jnp.sum((states[-1, :2] - target_xy) ** 2)
    smoothness_cost = 0.01 * jnp.sum((controls[1:] - controls[:-1]) ** 2)
    return terminal_cost + smoothness_cost


@jax.jit
def mpc_optimize_controls(
    controls: jnp.ndarray,
    state0: jnp.ndarray,
    target_xy: jnp.ndarray,
    wheel_base: float,
    dt: float,
    learning_rate: float = 0.05,
    steps: int = 20,
) -> jnp.ndarray:
    grad_fn = jax.grad(_mpc_cost)

    def body_fn(_: int, current_controls: jnp.ndarray) -> jnp.ndarray:
        grads = grad_fn(current_controls, state0, target_xy, wheel_base, dt)
        return current_controls - learning_rate * grads

    return jax.lax.fori_loop(0, steps, body_fn, controls)
