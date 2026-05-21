# Camera Hardware Integration Guide

This guide maps body cameras and micro cameras into the SmartCito platform.

## Ingestion Path

1. Device registers through the contract in
   [`../api_connectors/schemas/camera_registration.schema.json`](../api_connectors/schemas/camera_registration.schema.json).
2. SmartCito issues a short-lived token and stream destination.
3. Device publishes video into [`../../camera_module/`](../../camera_module/).
4. Device publishes GNSS samples into [`../../gps_module/`](../../gps_module/).
5. Mount, tamper, battery, and heartbeat events are logged and surfaced in the dashboard.

## Open Standards

- ONVIF is the preferred interoperability layer for IP camera discovery and control.
- RTSP and HTTP/2 are the standard transport choices for streaming and metadata.
- REST and GraphQL provide the universal integration layer for developers and dashboards.
- Camera metadata contracts are defined in
   [`../api_connectors/schemas/camera_metadata.schema.json`](../api_connectors/schemas/camera_metadata.schema.json).
- GPS ingestion contracts are defined in
   [`../api_connectors/schemas/gps_ingest.schema.json`](../api_connectors/schemas/gps_ingest.schema.json).

## Magnetic Detection

For magnetic mounts, the device should emit state transitions immediately:
- mounted
- removed
- unstable mount

These transitions should update dashboards and trigger audit events.

## OpenStack Alignment

- controller services manage device registration and policy
- compute nodes handle video decode, enrichment, and AI inference
- storage nodes persist approved metadata and controlled archives
- Neutron security groups and VPN gateways protect device ingress

## Modular Driver Model

- hardware-side contributor guidance lives in [`../camera_module/`](../camera_module/)
- software-side driver implementations live in [`../../camera_module/drivers/`](../../camera_module/drivers/)
- GPS standardization lives in [`../gps_module/`](../gps_module/)
- protocol baseline lives in [`../networking/protocols/`](../networking/protocols/)

## Security Minimums

- TLS for all uplinks
- AES-256 for local device storage
- tamper alert event on enclosure open or secure element fault
- registered-device allow-list enforced by backend auth
- full audit trail for registration, connect, disconnect, and stream actions
