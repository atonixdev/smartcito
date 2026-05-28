# Tests

Cross-module unit and integration tests for Orca.

Backend-specific tests live next to the backend at
[`../citosmart/tests/`](../citosmart/tests/). Frontend tests live under
[`../webapp/src/`](../webapp/src/). This folder is for tests that span
multiple modules (ingestion ↔ ai_models ↔ database, etc.) or that
exercise contributions from [`../contrib/`](../contrib/).

## Layout

```
tests/
├── ingestion/
├── ai_models/
├── gps_module/
├── camera_module/
├── database/
├── security/
└── integration/     # End-to-end scenarios
```

## Running

```bash
# From the repo root
pytest tests/ -v
```

Backend test suite:

```bash
cd citosmart
pytest -v
```

Frontend test suite:

```bash
cd webapp
npm test
```

## Conventions

- Use **pytest** for Python tests.
- Name files `test_*.py`, name tests `test_*`.
- Mock external services (Kafka, MQTT, S3, model registries) — integration
  tests that hit real services must be marked `@pytest.mark.integration`
  and skipped by default in CI.
- Every new module under the repo root must add at least one test here.
