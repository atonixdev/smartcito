# Database

Schemas, connectors, and migrations for SmartCito.

## Engines

- **PostgreSQL** — primary relational store (sensors, events, users, RBAC)
- **MongoDB** — optional document store for unstructured event metadata
- **TimescaleDB** (PostgreSQL extension) — time-series sensor data

The authoritative SQLAlchemy models and Alembic migrations live in the
backend at [`../citosmart/`](../citosmart/) (see `app/db/` and `migrations/`).
This folder collects **shared schema artifacts** and **non-backend
connectors**.

## Layout

```
database/
├── Dockerfile       # PostgreSQL-based container image
├── bootstrap.py     # Local schema bootstrap helper
├── init/            # SQL bootstrap scripts
└── README.md
```

## Conventions

- Every schema change ships with a migration. No edits to applied
  migrations.
- Use UUIDs for primary keys on user-facing entities.
- All timestamps are `TIMESTAMPTZ` in UTC.
- Sensitive columns must be encrypted at rest (see
  [`../security/`](../security/)).

## Backups

Backups are configured at the infra layer (see
[`../infra/`](../infra/)). Never store backups in this repo.

## Technologies Used

- PostgreSQL 16
- SQL schema bootstrap scripts
- Python bootstrap helper

## How To Run Its Container

```bash
docker run --rm -p 5432:5432 \
  -e POSTGRES_DB=smartcito \
  -e POSTGRES_USER=smartcito \
  -e POSTGRES_PASSWORD=smartcito \
  -v "$PWD/database/init/001_schema.sql:/docker-entrypoint-initdb.d/001_schema.sql:ro" \
  cgr.dev/chainguard/postgres:latest@sha256:34a4d686aa44583457bbdbdeb662243e7ab29e89e5c9b40df8e33baa6b75dc47
```

## Example Usage

```bash
python database/bootstrap.py
```
