<!--
================================================================================
 File: docs/ISSUE_BACKLOG.md
 Purpose:
   Suggested GitHub issue backlog for SmartCito maintainers and contributors.
   Use this document to create roadmap-aligned issues, labels, and milestones.
================================================================================
-->

# SmartCito Issue Backlog

This file contains suggested GitHub issues for SmartCito. Copy the titles into
GitHub Issues, then expand the description using the notes under each section.

## Suggested Labels

- `enhancement`
- `bug`
- `good first issue`
- `help wanted`
- `backend`
- `frontend`
- `docs`
- `security`
- `infra`
- `testing`
- `analytics`
- `hardware`
- `compliance`
- `observability`
- `needs-triage`

## Suggested Milestones

- `Phase 0 - Foundation Polish`
- `Phase 1 - Pilot Ingestion`
- `Phase 2 - Live Dashboard`
- `Phase 3 - Analytics`
- `Phase 4 - Compliance Toolkit`
- `Phase 5 - Production Deployment`
- `Good First Issues`
- `Security Hardening`

---

## Phase 0 - Foundation Polish

### `[docs] Add first contributor onboarding checklist`

Labels: `docs`, `good first issue`, `help wanted`

Problem: New contributors need a short checklist for setting up the repo,
running tests, and finding a first issue.

Proposed solution: Add a contributor onboarding checklist that links to setup,
testing, issue labels, and pull request expectations.

### `[docs] Add architecture diagram image to README`

Labels: `docs`, `enhancement`

Problem: The README has an ASCII architecture diagram, but a rendered diagram
would be easier to understand on GitHub.

Proposed solution: Add a visual diagram under `docs/` and reference it from the
README architecture section.

### `[docs] Document local development troubleshooting`

Labels: `docs`, `good first issue`

Problem: Contributors may hit common setup issues with Python, Node.js, Docker,
ports, or environment variables.

Proposed solution: Add a troubleshooting section covering common errors and
their fixes.

### `[docs] Add example .env values for local testing`

Labels: `docs`, `backend`, `infra`

Problem: Local development is easier when contributors know which environment
values are safe defaults.

Proposed solution: Expand `.env.example` or docs with local-only example values
for API, database, Redis, Kafka, and MQTT settings.

### `[maintenance] Add issue templates for docs, security, and infra tasks`

Labels: `enhancement`, `maintenance`, `docs`

Problem: The repo currently has bug and feature templates, but common task types
need more focused templates.

Proposed solution: Add issue templates for documentation improvements, security
hardening, infrastructure work, and good first issues.

---

## Phase 1 - Pilot Ingestion

### `[backend] Persist sensor readings to PostgreSQL`

Labels: `backend`, `enhancement`, `help wanted`

Problem: Sensor readings need durable persistence so dashboard and analytics
features can query historical data.

Proposed solution: Store validated sensor readings in PostgreSQL through the
existing SQLAlchemy model and session layer.

### `[backend] Add database query filters for recent sensor readings`

Labels: `backend`, `enhancement`

Problem: Consumers need to filter recent readings by sensor kind, sensor ID,
time range, and location.

Proposed solution: Add query parameters to the recent readings endpoint and
cover the filtering behavior with tests.

### `[backend] Add pagination to /sensors/recent`

Labels: `backend`, `enhancement`, `good first issue`

Problem: Returning all recent readings can become slow as the dataset grows.

Proposed solution: Add limit/offset or cursor-style pagination with documented
defaults and maximum limits.

### `[backend] Add validation for sensor units by sensor kind`

Labels: `backend`, `enhancement`, `testing`

Problem: Invalid unit combinations can make analytics unreliable.

Proposed solution: Validate accepted units per sensor kind and return clear API
errors for unsupported combinations.

### `[backend] Add Kafka publishing for ingested sensor events`

Labels: `backend`, `enhancement`, `streaming`

Problem: Ingested events should be mirrored to Kafka for downstream analytics
and stream processing.

Proposed solution: Publish normalized sensor events to Kafka after successful
validation and persistence.

### `[backend] Add MQTT to Kafka bridge`

Labels: `backend`, `enhancement`, `streaming`, `iot`

Problem: MQTT device messages need a durable path into the SmartCito event bus.

Proposed solution: Subscribe to configured MQTT topics, validate payloads, and
forward normalized messages to Kafka.

### `[backend] Add retry logic for Kafka producer failures`

Labels: `backend`, `reliability`, `streaming`

Problem: Temporary Kafka failures should not immediately drop valid events.

Proposed solution: Add bounded retries, logging, and metrics around Kafka
publish failures.

### `[backend] Add dead-letter queue handling for invalid events`

Labels: `backend`, `streaming`, `reliability`

Problem: Invalid events should be inspectable instead of silently discarded.

Proposed solution: Route invalid payloads to a dead-letter topic or table with
failure reasons and timestamps.

### `[backend] Add OpenAPI-generated TypeScript client`

Labels: `backend`, `frontend`, `enhancement`

Problem: The frontend should share API types with the FastAPI OpenAPI schema.

Proposed solution: Add a script that generates a TypeScript client from
`/openapi.json` and document how to refresh it.

### `[testing] Add integration tests for sensor ingestion`

Labels: `testing`, `backend`

Problem: Sensor ingestion touches validation, persistence, and optional event
publishing.

Proposed solution: Add integration tests for successful ingestion, invalid
payloads, persistence, and role-based access.

---

## Phase 2 - Live Dashboard

### `[frontend] Add live city map view`

Labels: `frontend`, `enhancement`, `help wanted`

Problem: Operators need a spatial view of active city sensors and events.

Proposed solution: Add a map panel using Leaflet or Mapbox GL that displays
recent sensor readings by location.

### `[frontend] Add sensor marker clustering to map`

Labels: `frontend`, `enhancement`

Problem: Dense sensor areas can make the map hard to scan.

Proposed solution: Add marker clustering and sensible zoom behavior for large
numbers of readings.

### `[frontend] Add map filters by sensor type`

Labels: `frontend`, `enhancement`, `good first issue`

Problem: Operators need to focus on specific sensor categories.

Proposed solution: Add filter controls for traffic, air quality, utility,
camera, GPS, and other configured sensor kinds.

### `[frontend] Add time-series chart for traffic readings`

Labels: `frontend`, `analytics`, `enhancement`

Problem: Traffic trends are easier to understand as time-series charts than raw
recent-reading lists.

Proposed solution: Add a chart panel that plots traffic readings over time with
clear labels and loading states.

### `[frontend] Add time-series downsampling for large datasets`

Labels: `frontend`, `analytics`, `performance`

Problem: Rendering too many chart points can slow the dashboard.

Proposed solution: Add downsampling before rendering large time-series datasets.

### `[frontend] Add role-based dashboard views`

Labels: `frontend`, `security`, `enhancement`

Problem: Viewers, operators, and admins should see controls that match their
permissions.

Proposed solution: Gate dashboard views and actions based on authenticated user
roles.

### `[frontend] Add loading, empty, and error states to dashboard panels`

Labels: `frontend`, `good first issue`, `accessibility`

Problem: Dashboard panels need clear states while data is loading, unavailable,
or failing.

Proposed solution: Add consistent loading, empty, and error UI across dashboard
components.

### `[testing] Add frontend tests for dashboard data loading`

Labels: `frontend`, `testing`

Problem: Dashboard data fetching should be protected against regressions.

Proposed solution: Add tests for successful responses, loading states, empty
responses, and API errors.

---

## Phase 3 - Analytics

### `[analytics] Add traffic summary aggregation service`

Labels: `analytics`, `backend`, `enhancement`

Problem: Operators need summarized traffic metrics instead of only individual
readings.

Proposed solution: Add a service that aggregates traffic readings by time window
and location.

### `[analytics] Add baseline anomaly detection for sensor values`

Labels: `analytics`, `backend`, `help wanted`

Problem: SmartCito should flag unusual readings for operator review.

Proposed solution: Implement a simple statistical anomaly detector as a baseline
before adding advanced ML pipelines.

### `[analytics] Add anomaly event schema`

Labels: `analytics`, `backend`

Problem: Anomalies need a consistent wire format for APIs, dashboards, and
notifications.

Proposed solution: Add a Pydantic schema for anomaly events with severity,
source reading, explanation, and timestamps.

### `[analytics] Add anomaly alert endpoint`

Labels: `analytics`, `backend`, `frontend`

Problem: Dashboard and external tools need a way to fetch anomaly alerts.

Proposed solution: Add an endpoint that lists recent alerts with filtering by
severity, status, sensor kind, and time range.

### `[analytics] Add Spark Structured Streaming job skeleton`

Labels: `analytics`, `streaming`, `help wanted`

Problem: The roadmap calls for Spark streaming jobs, but contributors need a
starter structure.

Proposed solution: Add a minimal Spark job that reads from Kafka, parses sensor
events, and writes a sample aggregation output.

### `[analytics] Add webhook notifications for alerts`

Labels: `analytics`, `backend`, `integrations`

Problem: City systems may need alert notifications outside the dashboard.

Proposed solution: Add configurable webhook delivery for selected alert types.

---

## Phase 4 - Compliance Toolkit

### `[compliance] Add data retention policy model`

Labels: `compliance`, `backend`, `security`

Problem: Different data classes may require different retention periods.

Proposed solution: Add a model that maps data classes to retention periods,
legal basis, and enforcement status.

### `[compliance] Add retention policy enforcement worker`

Labels: `compliance`, `backend`, `security`

Problem: Retention policies need automated enforcement.

Proposed solution: Add a scheduled worker that deletes or anonymizes expired
records according to configured policies.

### `[compliance] Add consent record schema`

Labels: `compliance`, `backend`

Problem: Consent-aware workflows need a consistent data model.

Proposed solution: Add a schema for consent records, purposes, timestamps,
status, and source system references.

### `[compliance] Add data subject request flow`

Labels: `compliance`, `backend`, `frontend`

Problem: GDPR/POPIA workflows require handling access, export, correction, and
deletion requests.

Proposed solution: Add backend models and endpoints for tracking data subject
requests through their lifecycle.

### `[compliance] Add export endpoint for subject data`

Labels: `compliance`, `backend`, `security`

Problem: Authorized users need to export subject-related records.

Proposed solution: Add an authenticated endpoint that exports subject data in a
structured format with audit logging.

### `[frontend] Add audit log explorer UI`

Labels: `frontend`, `compliance`, `security`

Problem: Compliance users need to inspect audit events without direct database
access.

Proposed solution: Add a searchable audit log page with filters for actor,
action, resource, and time range.

---

## Phase 5 - Production Deployment

### `[infra] Add Helm chart for SmartCito services`

Labels: `infra`, `kubernetes`, `enhancement`

Problem: Production Kubernetes deployments need a reusable package format.

Proposed solution: Add a Helm chart covering API, webapp, workers, service
configuration, probes, and secrets references.

### `[infra] Add Kubernetes manifests for local cluster deployment`

Labels: `infra`, `kubernetes`, `good first issue`

Problem: Contributors need a simple Kubernetes path before production Helm
configuration is complete.

Proposed solution: Add local manifests for kind or minikube with documented
commands.

### `[infra] Add production-ready ingress example`

Labels: `infra`, `security`, `kubernetes`

Problem: Operators need a clear example for exposing SmartCito over HTTPS.

Proposed solution: Add ingress examples for common controllers and TLS setup.

### `[infra] Add health probes for all services`

Labels: `infra`, `reliability`, `backend`

Problem: Production orchestrators need liveness and readiness checks for every
service.

Proposed solution: Ensure each service has documented health endpoints and
Kubernetes probe examples.

### `[infra] Add resource requests and limits`

Labels: `infra`, `kubernetes`, `reliability`

Problem: Kubernetes workloads should define predictable CPU and memory behavior.

Proposed solution: Add default requests and limits for API, webapp, workers,
Kafka, Redis, and PostgreSQL examples.

### `[infra] Add cosign container image signing`

Labels: `infra`, `security`, `ci`

Problem: Production users need a way to verify SmartCito container provenance.

Proposed solution: Add CI support and docs for signing images with cosign.

---

## Security Hardening

### `[security] Add rate limiting to API endpoints`

Labels: `security`, `backend`, `enhancement`

Problem: Public or semi-public APIs need protection from abusive request rates.

Proposed solution: Add configurable rate limiting by IP, user, or API token.

### `[security] Add audit logging for auth events`

Labels: `security`, `backend`, `compliance`

Problem: Login attempts and identity-sensitive actions should be auditable.

Proposed solution: Record successful logins, failed logins, token refreshes,
role changes, and logout events where applicable.

### `[security] Add audit logging for ingestion events`

Labels: `security`, `backend`, `compliance`

Problem: Operators need traceability for data accepted into the platform.

Proposed solution: Record ingestion source, validation result, actor/device, and
event identifiers in an audit trail.

### `[security] Add JWT expiration and refresh token strategy`

Labels: `security`, `backend`, `docs`

Problem: Token lifetime and refresh behavior should be explicit and tested.

Proposed solution: Document and implement access token expiration, refresh
tokens, revocation behavior, and related tests.

### `[security] Add secret scanning to CI`

Labels: `security`, `ci`, `good first issue`

Problem: Secrets should be caught before they land in the repository.

Proposed solution: Add a CI job for secret scanning and document how to handle
false positives.

### `[security] Add RBAC tests for protected endpoints`

Labels: `security`, `testing`, `backend`

Problem: Role-based access control needs regression coverage.

Proposed solution: Add tests that verify viewer, operator, and admin behavior
for protected endpoints.

---

## Observability

### `[observability] Add structured JSON logs`

Labels: `observability`, `backend`, `infra`

Problem: Production logs should be easy to search, parse, and correlate.

Proposed solution: Emit structured JSON logs with service name, request ID,
level, timestamp, and relevant context.

### `[observability] Add request correlation IDs`

Labels: `observability`, `backend`, `frontend`

Problem: Requests need traceable IDs across API, workers, and frontend errors.

Proposed solution: Add middleware that accepts or generates correlation IDs and
returns them in responses.

### `[observability] Add Prometheus metrics for ingestion`

Labels: `observability`, `backend`, `metrics`

Problem: Operators need visibility into ingestion rate, failures, and latency.

Proposed solution: Add metrics for accepted events, rejected events, publish
latency, validation failures, and queue errors.

### `[observability] Add Grafana dashboard example`

Labels: `observability`, `infra`, `docs`

Problem: Metrics are easier to adopt with a ready-made dashboard.

Proposed solution: Add a Grafana dashboard JSON file and setup documentation.

### `[observability] Add OpenTelemetry tracing`

Labels: `observability`, `backend`, `infra`

Problem: Distributed workflows are hard to debug without traces.

Proposed solution: Add OpenTelemetry instrumentation for API requests,
database calls, Kafka publishing, and background workers.

---

## Hardware And Connectors

### `[hardware] Add connector SDK documentation`

Labels: `hardware`, `docs`, `enhancement`

Problem: Contributors need clear guidance for adding device and city-system
connectors.

Proposed solution: Document connector structure, required interfaces, testing
expectations, and examples.

### `[hardware] Add sample HTTP sensor connector`

Labels: `hardware`, `backend`, `good first issue`

Problem: Connector authors need a simple reference implementation.

Proposed solution: Add a sample connector that submits sensor readings through
the HTTP ingestion API.

### `[hardware] Add sample MQTT sensor connector`

Labels: `hardware`, `backend`, `iot`

Problem: MQTT is a core ingestion path and needs an example connector.

Proposed solution: Add a sample connector that publishes valid SmartCito sensor
payloads to a configured MQTT topic.

### `[hardware] Add RTSP camera health checks`

Labels: `hardware`, `camera`, `backend`

Problem: Camera integrations need a way to report stream availability.

Proposed solution: Add health check logic for RTSP camera streams and expose
status through the camera registry API.

### `[hardware] Add GPS stream validation tests`

Labels: `hardware`, `testing`, `gps`

Problem: GPS parsing and normalization should be protected against malformed
NMEA messages.

Proposed solution: Add tests for valid messages, invalid checksums, missing
fields, and out-of-range coordinates.

### `[hardware] Add simulator for test sensor events`

Labels: `hardware`, `testing`, `good first issue`

Problem: Developers need realistic sample data without physical devices.

Proposed solution: Add a simulator that emits traffic, environmental, GPS, and
camera status events for local testing.

---

## Good First Issues

### `[good first issue] Add screenshots to webapp README`

Labels: `good first issue`, `frontend`, `docs`

Problem: New contributors and users should be able to preview the dashboard
before running it locally.

Proposed solution: Add screenshots and short captions to the webapp README.

### `[good first issue] Add API examples to docs/API.md`

Labels: `good first issue`, `docs`, `backend`

Problem: API users need copyable request and response examples.

Proposed solution: Add example curl commands and JSON responses for each public
endpoint.

### `[good first issue] Add test data fixtures for sensors`

Labels: `good first issue`, `testing`, `backend`

Problem: Tests should share realistic sensor payloads instead of duplicating
inline examples.

Proposed solution: Add reusable fixtures for traffic, GPS, camera, and utility
sensor readings.

### `[good first issue] Add empty state copy to dashboard panels`

Labels: `good first issue`, `frontend`

Problem: Empty dashboard panels should explain that no data is currently
available.

Proposed solution: Add concise empty states to panels that depend on API data.

### `[good first issue] Add glossary for smart-city terms`

Labels: `good first issue`, `docs`

Problem: Terms like ingestion, federation, retention, RBAC, MQTT, and Kafka may
be unfamiliar to new contributors.

Proposed solution: Add a glossary page under `docs/` and link it from the main
README or wiki.

---

## Recommended First Issues To Open

Start with these because they unlock the rest of the roadmap:

1. `[backend] Persist sensor readings to PostgreSQL`
2. `[backend] Add Kafka publishing for ingested sensor events`
3. `[backend] Add MQTT to Kafka bridge`
4. `[backend] Add OpenAPI-generated TypeScript client`
5. `[frontend] Add live city map view`
6. `[testing] Add integration tests for sensor ingestion`
7. `[security] Add RBAC tests for protected endpoints`
8. `[observability] Add Prometheus metrics for ingestion`
