<!--
================================================================================
 File: docs/REPOSITORY_STRUCTURE.md
 Purpose:
   Canonical repository structure and ownership guide for Orca.
   This document defines what each top-level folder is responsible for and
   clarifies current overlaps that contributors should avoid growing.
================================================================================
-->

# Orca Repository Structure

## Canonical Ownership

The repository is organized by domain. To keep it understandable, contributors
should follow these top-level ownership rules:

- `orcaapi/` is the backend API application.
- `services/` holds separately deployable service runtimes.
- `webapp/` is the primary frontend application.
- `domains/` is the contributor-facing grouping layer for air, robotics,
  vision, sensors, platform, and AI discovery.
- `air/` is the physical home for drone and surveillance Python packages.
- `vision/` is the physical home for camera and vision service packages.
- `robotics/` is the physical home for robotics Python packages.
- `sensors/` is the physical home for GPS and sensor service packages.
- `services/` now also contains the migrated Python security-domain package root.
- `edge/` is the physical home for migrated hardware-domain packages.
- `cli/` is the packaged command-line surface.
- `sdk/` is the repository home for shipped developer SDKs.

This document is the source of truth for those boundaries.

## Grouping Layer

The repository now includes a top-level `domains/` folder that groups related
surfaces for discovery. Some groups are now also reflected in physical Python
package roots such as `air/` and `robotics/`.

Use `domains/` when you need a contributor-facing discovery map such as:

- all drone and air-system paths in one place
- all robotics and autonomy paths in one place
- all camera and vision paths in one place
- all platform, CLI, and SDK paths in one place

Where migrations have already happened, compatibility shims stay behind at the
old import roots so runtime code can transition without a flag day.

### `air/`

**Responsibility:** Drone, surveillance, and aerial mission Python packages.

**Put here:**

- Drone gateway, mission control, aerial camera, and related surveillance code.
- Supporting drone-oriented models, Kafka publishers, and zone resolution code.

### `vision/`

**Responsibility:** Camera-facing Python packages and video service modules.

**Put here:**

- Camera service code and protocol driver helpers.
- Standalone vision-side FastAPI services and related runtime assets.

### `robotics/`

**Responsibility:** Ground robotics, autonomy, physics, perception, and ROS2
Python packages.

**Put here:**

- Robot service code.
- Navigation, perception, physics, cloud, and ROS2 workspace packages.

### `sensors/`

**Responsibility:** GPS and sensor-oriented Python service packages.

**Put here:**

- GPS parsing services.
- Sensor-edge FastAPI services and related runtime assets.

### `services/`

**Responsibility:** Deployable service assets and selected migrated Python
service-domain packages.

**Put here:**

- Standalone service folders such as `ai-service/`, `camera-service/`, and `gps-service/`.
- The migrated `security_domain/` Python package and related runtime assets.

### `edge/`

**Responsibility:** Hardware-facing Python packages and edge device validation helpers.

**Put here:**

- The migrated `hardware/` Python package.
- Edge runtime helpers, device references, and hardware validation assets.

## Server Rule

There is one default backend home today: `orcaapi/`.

Use `orcaapi/` when you are adding:

- API endpoints for the current FastAPI server.
- Shared application logic, schemas, or config.
- Server-owned database models and Alembic migrations.

Use `services/` only when you are creating or maintaining a backend component
that is intentionally deployed as its own service.

That means the server does not have two equal homes. `orcaapi/` is the
backend API; folders in `services/` are separate service units.

## Core Folders

### `ingestion/`

**Responsibility:** Data ingestion pipelines and external system adapters.

**Put here:**

- Connectors for Kafka, MQTT, REST polling, and WebSockets.
- Input normalization and validation before data enters queues or raw storage.
- Lightweight producer jobs that bridge external systems into Orca.

**Do not put here:**

- Long-lived business APIs.
- UI code.
- Core authorization logic.

### `services/`

**Responsibility:** Deployable microservices and service boundaries outside the
main backend.

**Put here:**

- Independently deployable services such as camera, GPS, AI, and security
  services.
- Service-specific Dockerfiles, configs, and runtime wiring.
- REST or gRPC interfaces exposed as standalone service units.

**Current note:**

Today `orcaapi/` is the default home for the backend API. New backend code
should either:

- live in `orcaapi/` if it belongs to the main API service, or
- live in `services/<service-name>/` if it is intentionally being built as an
  independently deployable service.

Do not duplicate the same capability in both places.

### `database/`

**Responsibility:** Shared database bootstrap and storage infrastructure.

**Put here:**

- Bootstrap scripts, seed/setup helpers, and container init assets.
- Shared database provisioning logic.
- Environment-driven connection setup used across services.

**Current note:**

Application-specific ORM models and Alembic migrations should live with the
backend API service that owns them. For the main backend, that means
`orcaapi/`. If the code base moves toward fully split services, each service
should own its migrations, while `database/` remains the shared infrastructure
layer.

### `ai/`

**Responsibility:** Consolidated AI workspace for inference, training, datasets,
notebooks, runtime code, and model artifacts.

**Put here:**

- `ai/ai_models/` for inference services and model packaging.
- `ai/training/` for fine-tuning, evaluation, and Kaggle packaging scripts.
- `ai/datasets/` for synthetic and private AI datasets.
- `ai/examples/` for notebooks and demo assets.
- `ai/orca_runtime/` for the runtime model code.
- `ai/orca_datasets/` for generated ingestion batches.
- `ai/models/` and `ai/output/` for versioned artifacts and adapter outputs.

**Compatibility rule:**

AI work should target the `ai/` tree directly. The duplicate top-level AI
paths have been removed.

### `ai/ai_models/`

**Responsibility:** AI and ML inference assets.

**Put here:**

- Detection, prediction, and analytics models.
- Inference services or batch jobs.
- Model packaging and runtime dependencies.

**Integration rule:**

Expose inference through stable service interfaces consumed by `services/` or
`orcaapi/`; avoid coupling model internals directly to frontend or ingestion
layers.

### `webapp/`

**Responsibility:** Operator-facing frontend application.

**Put here:**

- `webapp/` is the primary frontend application.
- Dashboard pages, maps, 3D views, and reusable UI components.
- Migrated legacy frontend components that still have reuse value.

**Rule:**

New general-purpose operator UI work should go to `webapp/`. Do not create a
parallel frontend root for dashboard-only work.

### `cli/`

**Responsibility:** Packaged command-line entrypoints and operator/developer
workflow commands.

**Put here:**

- Modular CLI code that is launched by stable entrypoints such as `./orca`.
- SDK-backed operational commands that query running Orca control-plane APIs.
- Workspace inspection commands that help contributors navigate the repo.

### `sdk/`

**Responsibility:** Shipped software development kits for external consumers,
automation, and integration clients.

**Put here:**

- Language-specific SDK packages.
- Lightweight API clients that follow the supported Orca backend contract.
- Examples and README files for SDK consumers.

### `security/`

**Responsibility:** Security policy, authentication, IAM, secrets handling, and
hardening artifacts.

**Put here:**

- JWT or OAuth2 support assets.
- RBAC policy definitions.
- Hardening, compliance, crypto, incident-response, and audit materials.
- Shared security middleware or service code when separated from the main API.

### `scripts/`

**Responsibility:** Developer and operator helper scripts.

**Put here:**

- Bootstrap scripts.
- DB seeding and migration wrappers.
- Health checks, diagnostics, and log collection.
- Repeatable local maintenance commands.

### `docs/`

**Responsibility:** Architecture, runbooks, API references, and decision
records.

**Put here:**

- System diagrams.
- Deployment and operational documentation.
- API and module ownership documentation.

## Related Folders

- `orcaapi/`: backend API application, schemas, migrations, and business logic.
- `infra/`: deployment infrastructure such as Kubernetes, Terraform,
  Prometheus, and Mosquitto.
- `hardware/`: hardware integration assets, drivers, and operational support.
- `map/`: location intelligence and mapping subsystem.
- `tests/`: cross-module and system-level test coverage.

## Recommended Working Rules

1. Treat `orcaapi/` as the default backend API location.
2. Keep shared DB infrastructure in `database/`, but keep app-local migrations
   with the app or service that owns the schema.
3. Treat `webapp/` as the default destination for new frontend work.
4. Keep ingestion adapters in `ingestion/`, not inside UI or security folders.
5. Update this document whenever a top-level folder gains a new responsibility.