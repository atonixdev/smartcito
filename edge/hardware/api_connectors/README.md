# API Connectors

Contracts and reference flows for registering hardware cameras with Orca.

## Responsibilities

- device registration and provisioning
- token issuance / rotation
- camera heartbeat reporting
- stream endpoint announcements
- GPS, mount, and tamper event publication

## Suggested Flow

1. Device boots and attests identity using a per-device secret or certificate.
2. Device calls the registration endpoint with hardware profile and capabilities.
3. Backend returns a short-lived access token plus stream configuration.
4. Device starts secure streaming and periodic heartbeat/GPS updates.
5. Dashboard reflects online, mounted, and geolocated state in real time.

## API Shape

- REST for registration and heartbeat
- GraphQL optional for dashboard subscriptions and query aggregation
- JWT / OAuth2 tokens only; no static shared secrets

## Artifacts

- registration schema: [`schemas/camera_registration.schema.json`](schemas/camera_registration.schema.json)
- implementation targets: [`../../orcaapi/`](../../orcaapi/) and [`../../webapp/`](../../webapp/)
