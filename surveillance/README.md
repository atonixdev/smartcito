# Orca Drone and Surveillance Layer

The Orca drone and surveillance layer connects mobile drones, fixed sensors, camera streams, geospatial enrichment, AI threat detection, Kafka, Spark Streaming, storage, and operator dashboards.

Drones and sensors are not baked into the Orca OS image. They run as services on Kubernetes or Docker Compose and publish normalized real-time events into the platform backbone.

## Surveillance Architecture (Sees, Thinks, Reacts)

For the complete SmartCito surveillance architecture reference, including perception, intelligence, autonomy, sensor fusion, threat classification, tracking/interception, cloud integration, security, and end-to-end workflow, see:

- `docs/SURVEILLANCE_SYSTEM.md`

## Container Image

- Build file: `surveillance/Dockerfile`
- What the image does: runs the Drone Gateway API on port `8020` with `uvicorn surveillance.drone_gateway_service:app`.
- What ships in the image: the `surveillance/` package and this README at `/app/surveillance/README.md`.

## Services

| Service | Local port | Purpose | Main topics |
| --- | ---: | --- | --- |
| Drone Gateway | 8020 | Receives drone telemetry and accepts commands such as takeoff, land, move-to, patrol path, hover, and return-to-base | `orca.drone.telemetry`, `orca.drone.events`, `orca.drone.missions` |
| Sensor Gateway | 8021 | Receives fixed/mobile sensor readings over HTTP bridge payloads from MQTT, TCP, LoRaWAN, or vendor adapters | `orca.sensors.raw`, `orca.sensor.alerts` |
| Drone Camera Ingestion | 8022 | Registers RTSP/WebRTC/vendor streams and publishes frame metadata or key-frame events | `orca.drone.camera.frames`, `orca.drone.camera.alerts` |
| Mission Control | 8025 | Validates mission routes, uploads patrol paths through Drone Gateway, and monitors mission status for operators | `orca.drone.missions`, `orca.drone.events` |
| Threat Detection | 8023 | Classifies AI detections and correlated sensor/video/GPS events into low, medium, high, or critical alerts | `orca.threat.alerts` |
| Mapping and Geospatial | 8024 | Converts WGS84 GPS into zones, geofences, routes, heatmaps, and dashboard overlays | `orca.location.enriched` |

## Drone Gateway Contract

The Drone Gateway is the only Orca service that talks directly to drones. Mission Control, dashboards, AI, analytics, and operator APIs talk to the gateway instead of opening their own drone connections.

Mission Control endpoints:

| Endpoint | Purpose |
| --- | --- |
| `GET /ready` | Reports mission topic state, gateway route, and mission count |
| `POST /missions/validate` | Validates route geometry, geofence criticality, and patrol policy |
| `POST /missions` | Creates a mission and uploads it to Drone Gateway when validation passes |
| `GET /missions` | Lists active and historical mission records |
| `POST /missions/{mission_id}/status` | Updates progress and lifecycle state for monitoring flows |

Implemented endpoints:

| Endpoint | Purpose |
| --- | --- |
| `GET /ready` | Reports Kafka topics, supported protocols, and Drone Registry state |
| `GET /metrics` | Exposes Prometheus-style counters for connected drones, telemetry, command acceptance, and capability sync |
| `POST /connect` | Selects an adapter, discovers capabilities, syncs the Drone Registry, and emits `drone.capabilities.discovered` |
| `POST /capabilities` | Upserts externally supplied capability records into the Drone Registry |
| `GET /drones/{drone_id}/capabilities` | Reads cached or PostgreSQL-backed capability records |
| `POST /telemetry` | Normalizes GPS, altitude, speed, heading, battery, link quality, flight mode, status, and health flags into `orca.drone.telemetry` |
| `POST /commands` | Sends commands through the selected drone adapter and emits `orca.drone.events` |
| `POST /drones/{drone_id}/commands` | Mission Control command route with path/body drone ID validation |
| `GET /drones` | Returns latest telemetry plus known registry capability records |

Supported adapter protocols are `simulated`, `mavlink`, `rest`, `websocket`, and `vendor-sdk`. The `mavlink` adapter now uses `pymavlink` for real heartbeat, command, position-target, and mission-upload transport, while the other protocols keep the stable gateway contract in place for future vendor-specific integrations.

The Drone Registry persists:

- `drone_id`
- `model`
- `firmware_version`
- `max_speed_mps`
- `max_altitude_m`
- `battery_capacity_mah`
- `camera_types`
- `sensors`
- `payload_supported`
- `status`
- `protocol`
- `last_seen_at`

## End-to-End Flow

1. Drones and sensors send telemetry, video metadata, readings, and alerts.
2. Drone Gateway and Sensor Gateway normalize payloads into Orca event envelopes.
3. Drone Camera Ingestion registers live streams and publishes frame metadata for AI analysis.
4. When a frame includes `image_b64`, Drone Camera Ingestion calls the shared AI service `/detect_objects` endpoint and stores summarized detections on the frame event and feed status.
5. Kafka carries drone, camera, sensor, location, and threat topics in real time.
6. Spark Streaming subscribes to the surveillance topic set, enriches events, stores batches in PostgreSQL/HDFS/HBase, and forwards alert-like payloads.
7. Threat Detection turns detections and correlated events into actionable alerts.
8. Mapping and Geospatial converts GPS positions into dashboard overlays, geofences, patrol routes, and heatmap intensity.
9. The React dashboard and Plotly Dash surfaces show drone positions, verified sensors, live camera links, threat zones, and timelines.
10. Operators send commands back to drones through the Drone Gateway API.

## Local Run

Start the supporting service stack:

```bash
docker compose -f docker-compose.services.yml up \
  drone-gateway sensor-gateway drone-camera-ingestion mission-control \
  threat-detection mapping-geospatial kafka
```

For the full dashboard, API, surveillance, and observability stack in one
command, use the root compose file:

```bash
docker compose up --build
```

The services default to Kafka publishing. For endpoint-only development without a broker, set:

```bash
export ORCA_KAFKA_ENABLED=0
export DRONE_REGISTRY_ENABLED=0
```

## API Examples

Send drone telemetry:

```bash
curl -X POST http://localhost:8020/telemetry \
  -H 'content-type: application/json' \
  -d '{
    "drone_id": "drone-001",
    "protocol": "mavlink",
    "position": {"latitude": -25.7479, "longitude": 28.2293, "altitude_m": 120},
    "speed_mps": 8.2,
    "heading_deg": 90,
    "battery_percent": 87,
    "status": "in_mission"
  }'
```

Discover drone capabilities and sync the Drone Registry:

```bash
curl -X POST http://localhost:8020/connect \
  -H 'content-type: application/json' \
  -d '{
    "drone_id": "drone-001",
    "protocol": "simulated",
    "endpoint": "sim://drone-001"
  }'
```

Send a drone command:

```bash
curl -X POST http://localhost:8020/drones/drone-001/commands \
  -H 'content-type: application/json' \
  -d '{
    "drone_id": "drone-001",
    "action": "move_to",
    "target": {"latitude": -25.7454, "longitude": 28.2438, "altitude_m": 95},
    "requested_by": "operator"
  }'
```

Control a drone camera:

```bash
curl -X POST http://localhost:8020/drones/drone-001/commands \
  -H 'content-type: application/json' \
  -d '{
    "drone_id": "drone-001",
    "action": "camera_zoom",
    "camera_id": "rgb-main",
    "zoom_level": 4,
    "requested_by": "mission-control"
  }'
```

Register a drone camera stream and publish frame metadata:

```bash
curl -X POST http://localhost:8022/streams/register \
  -H 'content-type: application/json' \
  -d '{"drone_id": "drone-001", "stream_url": "rtsp://drone-001/main", "protocol": "rtsp"}'

curl -X POST http://localhost:8022/frames \
  -H 'content-type: application/json' \
  -d '{"drone_id": "drone-001", "width": 1280, "height": 720}'
```

To request camera-side object detection during ingestion, include a base64-encoded image and optionally pin the backend:

```bash
curl -X POST http://localhost:8022/frames \
  -H 'content-type: application/json' \
  -d '{"drone_id": "drone-001", "width": 1280, "height": 720, "image_b64": "<base64-png>", "ai_backend": "auto", "ai_labels": ["vehicle"]}'
```

Publish a sensor alert:

```bash
curl -X POST http://localhost:8021/readings \
  -H 'content-type: application/json' \
  -d '{
    "device_id": "perimeter-sensor-003",
    "sensor_type": "motion",
    "position": {"latitude": -25.7448, "longitude": 28.2455},
    "value": 1,
    "unit": "boolean",
    "alert": true
  }'
```

Classify an AI detection:

```bash
curl -X POST http://localhost:8023/detections \
  -H 'content-type: application/json' \
  -d '{
    "source_id": "drone-001-camera",
    "source_type": "drone_camera",
    "label": "intrusion breach",
    "confidence": 0.88,
    "position": {"latitude": -25.7454, "longitude": 28.2438}
  }'
```

Fetch map overlays:

```bash
curl http://localhost:8024/overlays
```

## Kubernetes

Apply the Kubernetes layer after the shared namespaces, config maps, Kafka, storage, and API dependencies are available:

```bash
kubectl apply -f infra/kubernetes/platform-config.yaml
kubectl apply -f infra/kubernetes/surveillance-services.yaml
```

The manifests deploy:

- `drone-gateway` in the `backend` namespace
- `sensor-gateway` in the `backend` namespace
- `drone-camera-ingestion` in the `backend` namespace
- `mission-control` in the `backend` namespace
- `threat-detection` in the `ai` namespace, with a GPU-optional node selector
- `mapping-geospatial` in the `visualization` namespace

## Dashboard Integration

The existing control-plane dashboard now includes:

- Drone and sensor device categories
- Drone patrol and perimeter sensor demo overlays
- Drone patrol, threat zone, GPS path, camera, and heatmap layer toggles
- Surveillance service operator controls
- A surveillance data-flow stage showing MAVLink/RTSP/MQTT/Kafka movement into Spark and threat intelligence

## Validation

Run the focused tests:

```bash
ORCA_KAFKA_ENABLED=0 pytest tests/test_surveillance_layer.py -q
```

Run compile validation:

```bash
python3 -m compileall surveillance ingestion orcaapi/app
```

Validate local compose shape:

```bash
docker compose -f docker-compose.services.yml config
```
