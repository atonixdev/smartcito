# Orca Hardware Integration

This folder captures the reference hardware footprint for Orca pilot and
production deployments. It complements the software implementation in
[`../orcaapi/`](../orcaapi/) and [`../webapp/`](../webapp/) and the local
Docker stack in [`../docker-compose.yml`](../docker-compose.yml).

## Container Image

- Build file: `hardware/Dockerfile`
- What the image does: runs the FastAPI hardware-domain API on port `8014` for reference-stack, monitoring, and edge hardware contract endpoints.
- What ships in the image: the `hardware/` package and this README at `/app/hardware/README.md`.

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
├── drone_edge/     # PX4/ROS2 companion runtime, MAVLink bridge, and Orca SDK
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
- **Drone companion computers** run PX4-facing MAVLink uplinks, ROS2 autonomy
  integration, sensor fusion packaging, and camera/video registration into the
  Orca cloud services.

## Software Mapping

- Local development: [`../docker-compose.yml`](../docker-compose.yml)
- Hardware-aware container overlay: [`../docker-compose.hardware.yml`](../docker-compose.hardware.yml)
- Security posture: [`../security/SECURITY_POSTURE.md`](../security/SECURITY_POSTURE.md)
- Deployment guide: [`docs/deployment.md`](docs/deployment.md)
- Camera device integration: [`docs/camera_hardware_integration.md`](docs/camera_hardware_integration.md)
- Drone manufacturer specification: [`docs/drone_manufacturer_spec.md`](docs/drone_manufacturer_spec.md)
- Drone RFP packet and acceptance structure: [`docs/drone_manufacturer_spec.md`](docs/drone_manufacturer_spec.md)
- Prototyping notes: [`docs/prototyping.md`](docs/prototyping.md)
- Open protocol baseline: [`networking/protocols/`](networking/protocols/)
- Quantum-ready procedures: [`quantum/`](quantum/)
- Drone hardware and communication stack: [`drone_edge/README.md`](drone_edge/README.md)

## Technologies Used

- Python 3.11
- FastAPI
- monitoring helpers for hardware telemetry

## How To Run Its Container

```bash
docker build -f hardware/Dockerfile -t orca-hardware-domain .
docker run --rm -p 8014:8014 orca-hardware-domain
```

## Example Usage

```bash
curl http://localhost:8014/monitoring/sample
curl http://localhost:8014/drone-edge/reference-stack
curl http://localhost:8014/drone-edge/hardware-spec
curl http://localhost:8014/drone-edge/ros2-contract
curl http://localhost:8014/drone-edge/rfp-packet
```
