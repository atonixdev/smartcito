<!--
================================================================================
 File: docs/ARCHITECTURE.md
 Purpose:
   Deep-dive into the SmartCito architecture. This is the document to read
   after the root README and before writing your first feature.
================================================================================
-->

# SmartCito Architecture

## Goals

1. **Unify** fragmented urban data (IoT, traffic, utilities, CCTV).
2. **Secure** every byte in transit and at rest.
3. **Open** the platform to community contributions and audits.
4. **Scale** from a 3-system pilot to a multi-department deployment.

## Logical Layers

| Layer            | Responsibility                                   | Tech (default)                |
|------------------|--------------------------------------------------|-------------------------------|
| Ingestion        | Accept events from devices and city systems      | FastAPI, paho-mqtt, aiokafka  |
| Stream Processing| Filter, enrich, aggregate, detect anomalies      | asyncio · PySpark / Dask (scale) |
| Storage          | Persist time-series and relational data          | PostgreSQL, MongoDB, HBase    |
| Cache            | Hot path lookups, pub/sub fan-out                | Redis                         |
| API Gateway      | AuthN/Z, rate limit, audit, schema validation    | FastAPI + PyJWT               |
| Visualization    | Operator + analyst dashboards                    | React, Plotly Dash, Grafana   |
| Security         | Encryption, key management, audit                | cryptography (AES-GCM, HKDF)  |
| Native (opt-in)  | Hot-path packet parsing, IoT drivers             | C11 (`native/`)               |
| Observability    | Metrics, logs, traces                            | Prometheus, OTEL              |

## Data Flow (happy path)

```
Device ──MQTT/HTTP──> Ingestion API ──validate──> Kafka ──Spark──> Storage
                                              │
                                              └──> Redis (live snapshot)
Dashboard ──REST/WS──> API Gateway ──read──> Redis + Storage
```

## Trust Boundaries

- **Edge** (devices) ↔ **Ingestion**: TLS + per-device credentials.
- **API Gateway** ↔ **Clients**: TLS + OAuth2/JWT.
- **Inter-service** (within VPC): mTLS recommended in production.

## Key Design Decisions

- **Python-first.** Python is the lingua franca: APIs (FastAPI), ingestion
  (paho-mqtt, aiokafka), analytics (scikit-learn, optional PySpark/Dask),
  visualization (Plotly Dash). Contributors anywhere in the world can
  ramp up quickly.
- **C only where it matters.** A small `native/` directory holds optional
  C11 extensions for hot-path packet parsing and IoT drivers. Every C
  function has a pure-Python fallback so contributors without a compiler
  can still run the project.
- **FastAPI** for the API: async, typed, OpenAPI for free.
- **Pydantic v2** for all schemas → one source of truth between docs, runtime
  validation, and TypeScript codegen.
- **PyJWT + cryptography** for auth and at-rest encryption (AES-256-GCM,
  HKDF-derived per-purpose keys).
- **React Query** on the webapp → centralized cache, automatic refetch.
- **Kafka** as the durable bus → decouples ingestion from analytics.
- **PostgreSQL first, HBase/Mongo later** → start simple, scale when justified.

## Extension Points

| Want to add...      | Touch these files                                |
|---------------------|--------------------------------------------------|
| A new sensor type   | `citosmart/app/schemas/sensor.py` (extend `SensorKind`) |
| A new endpoint      | `citosmart/app/api/v1/endpoints/<name>.py` + register in `router.py` |
| A new dashboard panel | `webapp/src/components/<Name>Panel.tsx`      |
| A new connector     | `citosmart/app/services/connectors/<name>.py` (planned) |

## Future Work

- Kubernetes manifests + Helm chart (`infra/helm`).
- Real anomaly-detection pipeline (Spark ML).
- Identity federation via Keycloak/OIDC.
- Data residency tags for cross-border compliance.
