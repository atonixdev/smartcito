# Camera API Connectors

Hardware-facing API conventions for camera registration and stream control.

## API Surface

- REST for registration, health, and heartbeat
- GraphQL optional for dashboard subscriptions and aggregated device queries
- JSON schemas for device registration and camera metadata contracts

## Schemas

- [`../../api_connectors/schemas/camera_registration.schema.json`](../../api_connectors/schemas/camera_registration.schema.json)
- [`../../api_connectors/schemas/camera_metadata.schema.json`](../../api_connectors/schemas/camera_metadata.schema.json)

## Auth

- JWT / OAuth2 tokens only
- mutual TLS preferred for managed fleet deployments
- every registration and state transition is auditable
