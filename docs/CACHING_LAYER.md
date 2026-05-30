# Orca Caching Layer

This repository uses Memcached as the shared low-latency caching tier for
reconstructable data. Memcached accelerates dashboard summaries, recent API
responses, AI inference, streaming metadata, and short-lived session reuse.

## Key format

All services use the shared key convention below:

`<service>:<domain>:<identifier>`

Examples implemented in this repo:

- `api:dashboard-summary:control-plane-overview`
- `dashboard:summary:map-overview`
- `dashboard:summary:scene-overview`
- `api:sensor-readings:recent-50`
- `api:session:admin@orca.dev`
- `api:user:viewer@orca.dev`
- `ai:prediction:features-<hash>`
- `device:metadata:<device-id>`
- `data-platform:stream-batch:batch-<id>`

## TTL policy

The default environment contract is defined in [.env.example](../.env.example).

- API responses: `MEMCACHED_API_TTL_SECONDS=60`
- Dashboard summaries: `MEMCACHED_DASHBOARD_TTL_SECONDS=45`
- Device metadata: `MEMCACHED_DEVICE_METADATA_TTL_SECONDS=300`
- AI inference: `MEMCACHED_AI_TTL_SECONDS=1800`
- Session reuse: `MEMCACHED_SESSION_TTL_SECONDS=3600`
- Default fallback: `MEMCACHED_DEFAULT_TTL_SECONDS=60`

No cache entry is configured with infinite TTL.

## Implemented cache surfaces

### Backend / API

- [control_plane.py](../orcaapi/app/services/control_plane.py): caches dashboard overview, map overview, and scene overview.
- [sensors.py](../orcaapi/app/api/v1/endpoints/sensors.py): caches recent sensor responses by requested limit.
- [auth.py](../orcaapi/app/api/v1/endpoints/auth.py): caches short-lived session token reuse and caller profile responses.

### AI / ML

- [ai_client.py](../orcaapi/app/services/ai_client.py): caches anomaly-scoring results by hashed feature vector.

### Data engineering / streaming

- [streaming_job.py](../ingestion/streaming_job.py): caches per-batch metadata and device metadata derived by Spark Structured Streaming.
- [spark_job.py](../ingestion/spark_job.py): advertises Memcached as part of the streaming contract.

## Invalidation rules

- Operator control changes invalidate cached dashboard summaries.
- Map device registration invalidates dashboard summaries and the specific device metadata key.
- Sensor ingestion invalidates recent sensor response caches.
- AI inference cache expires by TTL; model-specific invalidation should be triggered when model versioning is introduced.
- Session cache expires by TTL; no password or user secret is cached.

## Infrastructure

- Docker Compose service stack deploys a three-node Memcached cluster and exporter in [docker-compose.services.yml](../docker-compose.services.yml).
- Kubernetes deploys a three-pod Memcached StatefulSet plus exporter in [memcached-cluster.yaml](../infra/kubernetes/memcached-cluster.yaml).
- OpenStack networking allows Memcached only on the internal services network in [main.tf](../infra/openstack/networking/main.tf).

## Constraints

- Memcached is not a source of truth.
- Cache only reconstructable, non-authoritative data.
- Sensitive payloads must not be written to cache values.
- Missing systems in this repository, such as ERP/CRM or HBase connectors, should adopt the same key and TTL conventions when they are added.