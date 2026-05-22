<!--
================================================================================
 File: docs/ROADMAP.md
 Purpose: High-level milestones — the "north star" for contributors.
================================================================================
-->

# SmartCito Roadmap

## Phase 0 — Foundations (current)
- [x] Project scaffolding (FastAPI + React)
- [x] Contributor docs (README, CONTRIBUTING, CoC, SECURITY)
- [x] CI pipeline (lint, types, tests, build)
- [x] Docker Compose stack
- [ ] First external contributor merged 🎉

## Phase 1 — Pilot Ingestion
- [ ] PostgreSQL persistence for sensor readings
- [ ] Kafka producer for raw event stream
- [ ] MQTT bridge (Mosquitto → Kafka)
- [ ] OpenAPI-generated TypeScript client

## Phase 2 — Live Dashboard
- [x] 3D control-plane dashboard for IoT, GPS, cameras, threats, and Raspberry Pi edge nodes
- [x] Backend 3D-ready dashboard API (`/api/location/dashboard/3d`)
- [x] Trust-colored device visualization and visualization audit events
- [ ] Map view (Leaflet or Mapbox GL)
- [ ] Time-series charts (D3 + downsampling)
- [ ] Role-based dashboard views

## Phase 3 — Analytics
- [ ] Spark Structured Streaming jobs
- [ ] Anomaly detection (statistical + ML)
- [ ] Alerting (Alertmanager / webhooks)

## Phase 4 — Compliance Toolkit
- [ ] Consent + data subject request flows
- [ ] Retention policies per data class
- [ ] Audit log explorer UI

## Phase 5 — Federation & Production
- [ ] Helm chart + Kubernetes manifests
- [ ] Multi-city federation (data residency tags)
- [ ] Signed container images (cosign)

Contributions to any phase are welcome — comment on the relevant issue first.
