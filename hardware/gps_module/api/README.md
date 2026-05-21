# GPS Ingestion API

Reference contract for GPS and GNSS device ingestion.

## Protocols

- REST for registration and direct GPS event submission
- MQTT for streaming telemetry from constrained devices
- CoAP where low-power deployments need a compact transport

## Schemas

- [`../../api_connectors/schemas/gps_ingest.schema.json`](../../api_connectors/schemas/gps_ingest.schema.json)
- [`../../api_connectors/schemas/camera_registration.schema.json`](../../api_connectors/schemas/camera_registration.schema.json) for device registration

## Security

- TLS on every uplink
- device identity bound to token or certificate
- audit log for register, connect, disconnect, and anomalous location events
