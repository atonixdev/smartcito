# OpenStack Role Mapping

Suggested mapping between Orca workloads and an OpenStack-backed hardware
estate.

## Node Roles

| Role | OpenStack Services | Orca Responsibilities |
|------|--------------------|----------------------------|
| Controller | Keystone, Neutron API, Glance, Horizon, schedulers | auth, network control, orchestration integration |
| Compute | Nova compute, GPU passthrough / vGPU | `orcaapi`, analytics workers, AI inference |
| Storage | Cinder, Swift, Ceph-backed storage | PostgreSQL volumes, event/object storage, archives |
| Network | Neutron gateways, hardware firewalls, VPN | ingress, segmentation, secure remote access |

## Workload Mapping

- `webapp` sits behind a load balancer or ingress controller.
- `orcaapi` runs on controller or compute-adjacent nodes depending on scale.
- Kafka, PostgreSQL, and Redis should use dedicated storage-backed placements.
- GPU inference services should be isolated to labelled compute hosts.

## Operational Notes

- prefer anti-affinity for replicas of critical services
- keep management interfaces off public or ingest networks
- route object and block storage through approved encryption controls
