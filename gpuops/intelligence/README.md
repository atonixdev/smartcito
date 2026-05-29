# ORCA Intelligence Modules (JAX)

This package contains JAX-first implementations for:

- physics
- robotics
- mapping
- distance
- camera
- solvers
- optimization
- utils

## Performance Rules

- JIT compile heavy routines.
- Prefer `jax.vmap` for batch computations.
- Keep data in `jnp.ndarray` where possible.
- Use `jax.lax.scan`/`jax.lax.fori_loop` for iterative kernels.
- Keep functions pure and side-effect free.

## Typical Pipeline

Sensors -> JAX engine -> optimization -> control -> actuators
