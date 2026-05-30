# ORCA JAX Intelligence Engine

This directory contains ORCA intelligence modules that use JAX as the primary
computation backend.

## Install

```bash
pip install -r gpuops/requirements.txt
```

## Verify backend

```python
import jax
print(jax.default_backend())
```

Expected on GPU hosts: `gpu`.

## Structure

- gpuops/intelligence/physics
- gpuops/intelligence/robotics
- gpuops/intelligence/mapping
- gpuops/intelligence/distance
- gpuops/intelligence/camera
- gpuops/intelligence/solvers
- gpuops/intelligence/optimization
- gpuops/intelligence/utils
