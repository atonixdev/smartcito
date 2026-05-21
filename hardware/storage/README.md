# Storage Layer

SmartCito uses tiered storage so high-rate camera and sensor streams do not
compete with archives and analytics.

## Storage Tiers

- **Hot ingest tier**: SSD arrays for current camera and IoT traffic bursts.
- **Warm analytical tier**: NVMe or mixed SSD for indexed event metadata.
- **Archive tier**: HDD clusters or object storage for long-term retention.

## Reference Design

- RAID 10 for database and ingest volumes where low latency matters
- object storage for event exports and model artifacts
- block storage for database and queue durability
- separate backup target with immutable snapshots

## OpenStack Alignment

- **Cinder** for block volumes used by PostgreSQL and stateful middleware
- **Swift** for object storage, exports, model packages, and archives

## Practical Mapping

- `postgres` volume data belongs on the hot or warm SSD tier.
- Kafka logs belong on high-write SSD-backed volumes.
- raw video should not be retained by default; metadata belongs in the
  database and approved archives only.

## CI Coverage

- `test_storage_arrays.py` validates storage firmware, redundancy mode,
  throughput, thermal envelope, and immutable snapshot status.
- `ci_manifest.yaml` records the storage metrics required by CI.
