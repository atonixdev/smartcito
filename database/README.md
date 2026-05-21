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
├── schemas/         # SQL DDL, JSON Schema, Avro schemas
├── migrations/      # Cross-service migration helpers
├── connectors/      # Adapters for other languages/services
├── seeds/           # Reference/seed data
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
