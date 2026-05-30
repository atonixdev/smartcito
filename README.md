<!--
================================================================================
 Orca Installation And Usage Guide
================================================================================
 File: README.md
 Purpose:
   Top-level installation, startup, and project-usage guide for the local-first
   Orca platform.

 Audience:
   - Operators bringing up the local container stack.
   - Developers installing the API, CLI, SDK, and web documentation site.
   - Contributors looking for the main project entry points.

 Conventions:
   - Every file in this repository starts with a documentation header similar
     to this one. Keep that pattern when contributing.
================================================================================
-->

# Orca

Orca is a local-first device operations platform for drones, robots, sensors,
camera systems, and edge infrastructure. The main user surfaces are local CLI,
SDK, terminal-first workflows, and a documentation/downloads website.

## What You Install

The repository contains these main runtime surfaces:

| Surface | Path | Purpose |
| ------ | ------ | ------- |
| API | `orcaapi/` | FastAPI backend for device registry, telemetry, maps, firmware, and service orchestration |
| Web site | `webapp/` | Documentation and downloads site |
| Drone services | `surveillance/` | Drone gateway, mission control, mapping, threat detection, and camera ingestion |
| CLI | `orca` + `cli/orca_cli/` | Local operational commands and template export |
| Python SDK | `sdk/python/orca_sdk/` | Local programmatic client for API workflows |
| AI runtime | `ai/` | Training, inference, datasets, and model workflow assets |

## Installation Prerequisites

Install these tools on the host before using the repo:

- Docker with Compose support
- Python 3.11+ and `pip`
- Node.js 20+ and `npm`
- GNU Make

Optional but useful:

- `uvicorn` for direct API development
- a Python virtual environment tool such as `venv`

## Quick Start With Containers

The fastest way to run Orca is the root Docker Compose stack.

```bash
docker compose build
docker compose up -d
```

Main local endpoints after startup:

| Service | URL | Purpose |
| ------ | ------ | ------- |
| Web site | http://localhost:5173 | Documentation and downloads |
| API router | http://localhost:8000 | Main API entrypoint |
| Drone gateway | http://localhost:8020 | Drone telemetry and command gateway |
| Sensor gateway | http://localhost:8021 | Sensor ingestion gateway |
| Drone camera ingestion | http://localhost:8022 | Camera stream registration |
| Threat detection | http://localhost:8023 | AI alert correlation service |
| Mapping geospatial | http://localhost:8024 | Map and geofence service |
| Mission control | http://localhost:8025 | Mission validation and upload |

The static documentation and downloads site is also configured for GitHub Pages
deployment at `https://atonixcorp.github.io/Orca/`. Pushes to `main` trigger the
Pages workflow in `.github/workflows/deploy-github-pages.yml`.

To stop the stack:

```bash
docker compose down
```

To rebuild everything from scratch again:

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

## Local Development Installation

### API

```bash
cd orcaapi
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Web site

```bash
cd webapp
npm install
npm run dev
```

For the hosted static site, enable GitHub Pages with **Source: GitHub Actions**
in the repository settings. The existing workflow builds `webapp/`, publishes
`webapp/dist`, and adds a `404.html` SPA fallback for client-side routes.

### Root package, CLI, and SDK

Install the repository package from the root to get the `orca` command and
packaged Python modules:

```bash
python3 -m pip install .
```

Install service extras when you need the full local backend dependency set:

```bash
python3 -m pip install .[services]
```

## Project Usage

### Use The CLI

The root package installs the `orca` command.

```bash
orca --help
orca workspace template-write-all --output-dir ./orca-templates
```

### Use The Python SDK

```python
from orca_sdk.client import OrcaClient

client = OrcaClient("http://localhost:8000")
status = client.health_live()
print(status)
```

### Use The API Directly

```bash
curl http://localhost:8000/api/v1/health/live
```

### Use The Workflow Helpers

The repo includes make targets and workflow scripts for repeatable checks.

```bash
make workflow-help
make workflow-preflight
make workflow-test
make workflow-local
make workflow-docker
```

Equivalent direct script entrypoints:

```bash
python3 scripts/project_workflow.py preflight
python3 scripts/project_workflow.py test
python3 scripts/project_workflow.py local --smoke-only
python3 scripts/project_workflow.py docker --compose-file docker-compose.services.yml --build
```

## Project Structure

Use these paths as the main entry points when navigating the repository:

| Path | Use |
| ---- | --- |
| `orcaapi/` | Backend API application |
| `webapp/` | Web documentation and downloads site |
| `surveillance/` | Drone and field-device service layer |
| `services/` | Separately deployable service domains |
| `hardware/` | Hardware integrations and support modules |
| `ai/` | AI, model training, datasets, and runtime workflows |
| `robot/` | Ground robotics stack |
| `map/` | Location intelligence module |
| `docs/` | Architecture, deployment, and reference docs |
| `scripts/` | Build, validation, and developer helper scripts |

## Additional Documentation

Use these documents next, depending on what you are doing:

- `docs/DOCKER_DEPLOYMENT.md` for deployment details
- `docs/REPOSITORY_STRUCTURE.md` for ownership and directory intent
- `docs/WORKSPACE_ORGANIZATION.md` for placement rules
- `docs/WIKI.md` for a broad documentation hub
- `infra/openstack/orca-os/README.md` for the OpenStack and Kubernetes node image

## Validation Commands

These are the most useful quick checks after installation:

```bash
make repo-check
python3 -m py_compile orcaapi/app/core/security.py orcaapi/app/api/v1/router.py
```

- Dataset schema: [ai/training/dataset_format.md](ai/training/dataset_format.md)
- Training scripts: [ai/training/lora_training.py](ai/training/lora_training.py) and [ai/training/qlora_training.py](ai/training/qlora_training.py)
- Evaluation script: [ai/training/evaluate_adapters.py](ai/training/evaluate_adapters.py)
- Kaggle bundle packager: [ai/training/package_kaggle_bundle.py](ai/training/package_kaggle_bundle.py)
- Kaggle publish helper: [ai/training/publish_kaggle_dataset.py](ai/training/publish_kaggle_dataset.py)
- One-command workflow: [Makefile](Makefile)
- Shell workflow wrapper: [scripts/ai.sh](scripts/ai.sh)
- Public Kaggle demo notebook: [ai/examples/Orca_Training_Demo.ipynb](ai/examples/Orca_Training_Demo.ipynb)
- Public Kaggle inference notebook: [ai/examples/orca_inference_demo.ipynb](ai/examples/orca_inference_demo.ipynb)
- AI runtime package: [ai/orca_runtime](ai/orca_runtime)
- ORCA JAX intelligence engine: [gpuops/README.md](gpuops/README.md)
- ORCA developer directive: [gpuops/DEVELOPER_DIRECTIVE.md](gpuops/DEVELOPER_DIRECTIVE.md)
- Model documentation: [docs/MODEL_CARD.md](docs/MODEL_CARD.md)
- Operational flow: [docs/OPERATIONAL_FLOW.md](docs/OPERATIONAL_FLOW.md)
- Kaggle workflow: [docs/KAGGLE_USAGE.md](docs/KAGGLE_USAGE.md)
- Runtime documentation: [docs/ORCA_MODEL_RUNTIME.md](docs/ORCA_MODEL_RUNTIME.md)

### Runtime

- Ingestion/DataStream batches operational events into `ai/orca_datasets/batch_YYYYMMDD_HHMMSS.json`
- Versioned model artifacts are stored under `ai/models/orca_model_vN/`
- The active deployed model is tracked via `ai/models/active_model.json`
- FastAPI inference exposes Orca task endpoints under `/orca/*`
- The project CLI supports `orca ingest`, `orca train`, `orca deploy`, and `orca dataset export`
- The packaged CLI now lives in `cli/orca_cli/` while `./orca` remains the stable launcher
- The repository now ships a Python SDK in `sdk/python/orca_sdk/` for health, fleet, camera, and control-plane calls
- Domain indexes under `domains/` group air, robotics, vision, sensors, platform, and AI surfaces without relocating existing runtime paths
- The drone and surveillance Python stack now lives under `air/surveillance/` with a compatibility shim at `surveillance/`
- The robotics Python stack now lives under `robotics/robot/` with a compatibility shim at `robot/`
- The camera service now lives under `vision/camera_module/` with a compatibility shim at `camera_module/`
- The GPS service now lives under `sensors/gps_module/` with a compatibility shim at `gps_module/`
- The GPU intelligence service now lives under `ai/gpuops/` with a compatibility shim at `gpuops/`
- The security domain package now lives under `services/security_domain/` with a compatibility shim at `security/`
- The hardware domain package now lives under `edge/hardware/` with a compatibility shim at `hardware/`
- The repository now has root packaging metadata so `pip install -e .` exposes the `orca` CLI and bundled SDK packages
- Bundled JSON payload templates can be inspected with `orca workspace templates` and `orca workspace template <name>`
- Bundled JSON payload templates can also be written directly to disk with `orca workspace template-write <name> --output path.json`
- Bundled JSON payload templates can be written as a starter directory with `orca workspace template-write-all --output-dir templates/`

### Install

Install the repository package in non-editable mode with:

```bash
python3 -m pip install .
```

Install it with the service runtime extras needed for the lightweight FastAPI service roots with:

```bash
python3 -m pip install ".[services]"
```

Build a distributable wheel with:

```bash
python3 -m pip wheel . --no-deps -w dist/
```

Important: the repository does not ship base foundation-model weights. Contributors should only publish LoRA adapters generated from Orca training runs.

---

## Releases


- [Orca Edge v1.0](docs/ORCA_EDGE_V1_RELEASE.md) — IoT, GPS, Map & Camera Integration

If you find a vulnerability, please **do not open a public issue**. Follow the
disclosure process in [`SECURITY.md`](SECURITY.md).

Orca targets compatibility with:

- **GDPR**
- **POPIA**
- **ISO/IEC 27001** practices
- **NIST Cybersecurity Framework** controls


---

## CI/CD

`.env.example` is the single source of truth for local and deployment
configuration. Copy it to `.env` for local development, keep placeholder values
only in version control, and inject the same variables as runtime environment
values in production.

Important environment variables include:

- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `KAFKA_BROKER_URL` or `MESSAGE_BUS_URL`
- `OBJECT_STORAGE_ENDPOINT`, `OBJECT_STORAGE_BUCKET`
- `AUTH_JWT_SECRET`, `AUTH_ISSUER`, `AUTH_AUDIENCE`
- `OPENSTACK_AUTH_URL`, `OPENSTACK_PROJECT`, `OPENSTACK_USER`, `OPENSTACK_PASSWORD`, `OPENSTACK_REGION`

Orca now standardizes CI/CD across GitHub Actions and GitLab around these
stages: **build → test → package → deploy-staging → deploy-production**.

- CI builds one Docker image per service tagged with the commit SHA.
- CI runs backend, frontend, and service-specific test suites.
- CD deploys to OpenStack VMs through scripts in `infra/deploy/`.

See [`.github/workflows/ci.yml`](.github/workflows/ci.yml),
[`.github/workflows/full-stack-cicd.yml`](.github/workflows/full-stack-cicd.yml),
[`.gitlab-ci.yml`](.gitlab-ci.yml), and [`infra/deploy/README.md`](infra/deploy/README.md).

---

## Security

- All device communication is encrypted and token-authenticated
- All location events are HMAC-signed into the ATP ledger
- Only authenticated, validated devices appear on the map
- Containers are Debian-based for OpenStack and Kubernetes compatibility
