<!--
================================================================================
 File: docs/WORKSPACE_ORGANIZATION.md
 Purpose:
   Practical contributor guide for where to place new code, docs, tests, and
   operations assets so the repository stays organized over time.
================================================================================
-->

# Workspace Organization Guide

This document is the quick placement guide for contributors.
For canonical ownership boundaries, see `docs/REPOSITORY_STRUCTURE.md`.

## Where To Add New Code

- Backend API endpoints and main app logic: `orcaapi/`
- Independently deployable service runtimes: `services/`
- Operator frontend and dashboards: `webapp/`
- AI training, runtime, datasets, and adapters: `ai/`
- JAX intelligence modules (physics/robotics/mapping/camera/control): `gpuops/`
- Ingestion and connectors: `ingestion/`
- Security controls and policy assets: `security/`
- Infrastructure automation and deployment: `infra/`
- Hardware integration assets: `hardware/`

## Where To Add Documentation

- Architecture and runbooks: `docs/`
- Module-local usage docs: nearest module folder README
- Wiki-style long-form pages: `docs/wiki/`

## Where To Add Tests

- Module-specific tests: near module in local `tests/`
- Cross-module integration/regression tests: root `tests/`

## Naming and Structure Rules

- Keep one primary home per capability.
- Avoid duplicating logic across `orcaapi/` and `services/`.
- Keep APIs and contracts stable at module boundaries.
- Place helper scripts under `scripts/` and call them from Makefile targets.
- Update structure docs when introducing a new top-level responsibility.

## Validation

Run the repository structure check:

```bash
make repo-check
```
