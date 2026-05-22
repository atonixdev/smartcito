# Networking Layer

Reference network topology for SmartCito hardware deployments.

## Switching Tiers

- **Core switches**: 100 GbE backbone traffic
- **Distribution switches**: 40 GbE rack interconnects
- **Access switches**: 10 GbE for IoT gateways, CCTV ingest, GPS receivers

## Security and Access

- hardware firewalls plus workload-level segmentation
- VPN appliances for external official access
- load balancers for API and dashboard traffic
- dedicated management network for BMC/IPMI/iDRAC access

## Segmentation

Recommended VLANs / zones:
- `mgmt` for out-of-band management
- `control` for controller nodes and orchestration
- `data` for storage and east-west service traffic
- `ingest` for cameras, GPS, and IoT edge devices
- `public` for API ingress behind a WAF/load balancer

## Docker / Container Networking

The base compose stack is for local development only. For pilots and hardware
installs, use [`../../docker-compose.hardware.yml`](../../docker-compose.hardware.yml)
with reverse proxies, internal-only service networks, and monitoring endpoints
exposed only on admin networks.

## Protocol Standardization

Use the protocol baseline in [`protocols/`](protocols/) to keep camera, GPS,
and IoT integrations interoperable across vendors and geographies.

Quantum-ready networking guidance lives in [`quantum_ready/`](quantum_ready/)
for hybrid PQC migration and future QKD gateway integration.

## CI Coverage

- `test_network_transmission.py` validates reachability, firmware version,
  secure throughput, latency, and quantum-ready transport status.
- `ci_manifest.yaml` documents the networking metrics exported to CI.
