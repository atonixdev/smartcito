# SmartCito Hardware Integration

This folder captures the reference hardware footprint for SmartCito pilot and
production deployments. It complements the software implementation in
[`../citosmart/`](../citosmart/) and [`../webapp/`](../webapp/) and the local
Docker stack in [`../docker-compose.yml`](../docker-compose.yml).

## Layout

```
hardware/
├── Dockerfile       # Container image for hardware-domain API
├── requirements.txt # Runtime dependencies
├── service.py       # FastAPI hardware-domain service
├── camera_module/   # Hardware-facing camera standards, drivers, and docs
├── gps_module/      # Hardware-facing GNSS standards and API guidance
├── body_cameras/   # Body-worn camera reference builds and firmware notes
├── micro_cameras/  # Compact magnetic camera designs and streaming notes
├── gps_modules/    # GNSS chip configs and device-side location guidance
├── api_connectors/ # Registration, heartbeat, and stream API contracts
├── quantum/        # Quantum-ready procedures and contributor guidance
├── compute/        # Controller + GPU compute node specs
├── storage/        # Storage tiers, arrays, RAID, object/block mapping
├── networking/     # Switching, firewalling, VPN, rack uplinks
├── security/       # HSMs, biometric access, IDS/IPS appliances
├── racks/          # Rack placement, power, cabling patterns
├── monitoring/     # Thermal, power, UPS, Prometheus/Grafana hooks
└── docs/           # Runbooks, setup procedures, deployment mapping
```

## Deployment Model

- **Controller nodes** host orchestration, API control-plane services, and
  shared infrastructure.
- **Compute nodes** host GPU-heavy analytics, streaming, and CV inference.
- **Storage nodes** absorb ingestion bursts and long-term archives.
- **Network and security appliances** enforce segmentation, VPN access,
  intrusion detection, and key protection.

## Software Mapping

- Local development: [`../docker-compose.yml`](../docker-compose.yml)
- Hardware-aware container overlay: [`../docker-compose.hardware.yml`](../docker-compose.hardware.yml)
- Security posture: [`../security/SECURITY_POSTURE.md`](../security/SECURITY_POSTURE.md)
- Deployment guide: [`docs/deployment.md`](docs/deployment.md)
- Camera device integration: [`docs/camera_hardware_integration.md`](docs/camera_hardware_integration.md)
- Prototyping notes: [`docs/prototyping.md`](docs/prototyping.md)
- Open protocol baseline: [`networking/protocols/`](networking/protocols/)
- Quantum-ready procedures: [`quantum/`](quantum/)

## Technologies Used

- Python 3.11
- FastAPI
- monitoring helpers for hardware telemetry

## How To Run Its Container

```bash
docker build -f hardware/Dockerfile -t smartcito-hardware-domain .
docker run --rm -p 8014:8014 smartcito-hardware-domain
```

## Example Usage

```bash
curl http://localhost:8014/monitoring/sample
```
