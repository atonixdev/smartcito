# Hardware Deployment Procedure

Reference implementation steps for a Orca pilot or production rack.

## 1. Provision Hardware

- rack controller nodes, compute nodes, storage arrays, switches, and firewalls
- verify dual PSUs, firmware versions, RAID controllers, and GPU inventory
- document serials, rack positions, and management IPs

## 2. Cable and Power

- connect dual uplinks per node to separate switches where supported
- connect redundant A/B power feeds to each device
- validate out-of-band management access on the management network

## 3. Install Firmware and Base OS

- update BIOS, BMC, RAID, NIC, and GPU firmware
- apply secure boot where supported
- harden the host OS and install container runtime + monitoring agents

## 4. Assign Roles

- controller nodes: orchestration, ingress control, dashboards, management
- compute nodes: analytics, inference, stream processing
- storage nodes: database, Kafka durability, archive services
- security appliances: HSM, VPN, IDS/IPS
- edge devices: body cameras, micro cameras, GNSS modules, and magnetic mount sensors
- quantum-ready services: PQC libraries, simulators, and optional QKD gateways

## 5. Deploy Software

- bootstrap the local software stack with Docker Compose for initial smoke tests
- apply the hardware overlay with
  `docker compose -f docker-compose.yml -f docker-compose.hardware.yml up -d --build`
- move stateful services to dedicated volumes on approved storage tiers

## 6. Validate Data Transmission

- verify camera feeds arrive at ingestion endpoints
- verify GPS and IoT device streams reach Kafka and MQTT
- check storage persistence and dashboard visibility
- confirm audit logs and security alerts are generated
- verify body camera registration, GPS telemetry, and tamper events
- verify micro camera mount and removal events update dashboard state

## 7. Secure and Monitor

- enroll HSM-backed keys where available
- enforce MFA and RBAC per [`../../security/SECURITY_POSTURE.md`](../../security/SECURITY_POSTURE.md)
- enable Prometheus/Grafana dashboards and IDS alert routing

## 8. Prepare for Quantum-Safe Migration

- keep the production backbone on classical compute by default
- validate PQC-capable libraries and hybrid key exchange in staging first
- route any QKD-derived keys through approved KMS/HSM gateways
- document rollback plans before enabling any quantum-assisted control in production

## Exit Criteria

A site is considered ready only when:
- all services pass health checks,
- redundant power and network paths are tested,
- monitoring and alerting are active,
- incident response contacts are recorded,
- PQC and QKD integration points are documented even if not yet enabled.
