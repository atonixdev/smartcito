<!--
================================================================================
 File: docs/processes/02-local-development/PROCEDURE.md
 Purpose:
   Local development workflow for SmartCito services, dashboard, and supporting
   infrastructure.
================================================================================
-->

# Local Development Procedure

## Purpose

Provide a repeatable workflow for running SmartCito locally while keeping setup
steps discoverable for new contributors.

## Scope

This procedure covers local API, webapp, Docker service, and focused module
development workflows.

## Procedure

1. Pull the latest changes from the active development branch.
2. Review the target module README before installing dependencies.
3. Start shared services with the appropriate Compose file when the task depends
   on databases, Redis, Kafka, MQTT, or service orchestration.
4. Start the backend API from `citosmart/` when working on service behavior.
5. Start the webapp from `webapp/` when working on operator-facing flows.
6. Use focused validation commands before broad test runs.
7. Keep local-only secrets out of committed files.
8. Stop containers and background services after validation when they are not
   needed.

## Common Commands

```bash
docker compose up --build
```

```bash
cd citosmart
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

```bash
cd webapp
npm install
npm run dev
```

## Validation Checklist

- Target service starts without configuration errors.
- Frontend or API endpoint needed for the task is reachable.
- Focused tests pass for the touched area.
- No local secrets or generated runtime artifacts are staged.

## Related Documentation

- [../../DOCKER_DEPLOYMENT.md](../../DOCKER_DEPLOYMENT.md)
- [../../../webapp/README.md](../../../webapp/README.md)
- [../../../citosmart/README.md](../../../citosmart/README.md)
