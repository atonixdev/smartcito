<!--
================================================================================
 File: backend/README.md
 Purpose: Dev quickstart for the SmartCito Python backend.
================================================================================
-->

# SmartCito Backend (FastAPI)

The Python service that powers the SmartCito Urban Data Backbone API.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp ../.env.example ../.env
uvicorn app.main:app --reload
```

Visit:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- Health: <http://localhost:8000/api/v1/health/live>
- Metrics: <http://localhost:8000/metrics>

## Project Layout

```
backend/
├── app/
│   ├── main.py                # ASGI entrypoint + middleware
│   ├── core/                  # Config, logging, security
│   ├── api/v1/                # Versioned HTTP layer
│   │   ├── router.py          # Aggregates all endpoints
│   │   └── endpoints/         # One module per resource
│   ├── schemas/               # Pydantic DTOs (wire format)
│   └── services/              # Reusable business logic
├── tests/                     # Pytest suite
├── pyproject.toml             # Black / Ruff / mypy / pytest config
├── requirements.txt           # Runtime deps
├── requirements-dev.txt       # Dev / test deps
└── Dockerfile                 # Multi-stage container build
```

## Quality Gates

```bash
ruff check .
black --check .
mypy app
pytest
```

## Database Migrations (Alembic)

The first migration creates the `sensor_readings` table.

```bash
# Run pending migrations against the configured PostgreSQL instance
alembic upgrade head

# Generate a new migration from current ORM models
alembic revision --autogenerate -m "describe change"
```

Migrations live in `migrations/versions/`. The DSN is read from
`Settings.database_url` — never put credentials in `alembic.ini`.

## Background Services (opt-in)

Set these flags in `.env` to run additional workers inside the API process:

| Flag                         | Effect                                              |
|------------------------------|-----------------------------------------------------|
| `KAFKA_PUBLISHER_ENABLED=true` | Boots an aiokafka producer; every ingest is mirrored to Kafka. |
| `MQTT_ENABLED=true`          | Subscribes to `MQTT_TOPIC` and ingests every JSON message. |

Or run them as standalone processes:

```bash
python -m app.services.mqtt_ingestor     # MQTT bridge
python -m app.dash_app.server            # Plotly Dash analytics on :8050
```

## Adding a New Endpoint

1. Create a Pydantic schema in `app/schemas/`.
2. Implement business logic in `app/services/`.
3. Wire an HTTP handler in `app/api/v1/endpoints/<name>.py`.
4. Register the router in `app/api/v1/router.py`.
5. Add tests in `tests/`.

Every new file MUST begin with a documentation header (see existing files).
