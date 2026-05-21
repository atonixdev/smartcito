# Compute Layer

Reference compute profile for SmartCito.

Subfolders:
- [`classical/`](classical/) — current production backbone guidance
- [`quantum/`](quantum/) — future-facing simulator, QPU, and PQC integration notes

## Roles

### Controller Nodes

Use smaller, resilient servers for:
- API gateways and auth control-plane services
- orchestration (OpenStack APIs, schedulers, automation)
- monitoring control services
- CI runners and maintenance workloads

Recommended baseline:
- CPU: Intel Xeon Silver/Gold or AMD EPYC with 16-32 cores
- RAM: 64-128 GB
- Storage: mirrored SSD boot volumes
- NICs: dual 25/40 GbE uplinks
- Power: dual PSUs

### Compute Nodes

Use GPU-capable servers for:
- AI video analytics
- stream processing and enrichment
- anomaly detection and geospatial joins
- burst ingestion transforms

Recommended baseline:
- CPU: Intel Xeon Gold/Platinum or AMD EPYC, 32+ cores
- GPU: NVIDIA A100/H100 for heavy inference and training
- RAM: 256 GB minimum
- Storage: local NVMe scratch for hot pipelines
- NICs: dual 40/100 GbE uplinks
- Power: dual PSUs

## Container Placement

- `citosmart`, `kafka`, and processing workers can run on compute nodes.
- control-plane services should avoid GPU hosts unless capacity is abundant.
- pin GPU workloads with node labels such as `smartcito.role=compute-gpu`.

## Hybrid Compute Strategy

- classical Xeon/EPYC + GPU nodes remain the default execution plane
- quantum simulators or cloud quantum services are attached through modular APIs
- no operational dependency on quantum services is allowed in the core path

## CI Coverage

- `test_compute_nodes.py` validates endpoint reachability, firmware baseline,
  thermal envelope, power draw, and compute throughput.
- `ci_manifest.yaml` defines the metrics exported by the hardware CI stage.
