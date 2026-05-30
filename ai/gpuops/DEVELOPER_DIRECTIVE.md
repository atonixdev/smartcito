# ORCA Developer Directive: JAX Integration & Best Practices

This directive standardizes JAX-first implementation across ORCA intelligence modules.

## Required Rules

- Use `jax.numpy` (`jnp`) for numerical operations.
- JIT compile heavy functions with `@jax.jit`.
- Use `jax.vmap` for batch operations.
- Use `jax.lax.scan` or `jax.lax` loops instead of Python loops in hot paths.
- Keep functions pure (no mutation, no global state side effects).
- Use `jax.grad` for differentiable optimization and control.

## Intelligence Pipeline

Sensors -> ORCA JAX Engine -> Optimization -> Control -> Actuators

## Installation

```bash
pip install -U "jax[cuda12_local]" -f https://storage.googleapis.com/jax-releases/jax_cuda_releases.html
```

## Developer Follow-up Links

- https://docs.jax.dev/en/latest/installation.html
- https://jax.readthedocs.io/en/latest/notebooks/Common_Gotchas_in_JAX.html
- https://docs.jax.dev/en/latest/jax-101/index.html
