<!--
================================================================================
 File: docs/API.md
 Purpose: Human-readable summary of the SmartCito v1 HTTP API.
          The authoritative spec is auto-generated at /openapi.json.
================================================================================
-->

# SmartCito API (v1)

Base URL: `/api/v1`. All requests and responses are JSON.

Auth: OAuth2 password-flow → `Authorization: Bearer <jwt>`.

## Endpoints

### Health

| Method | Path                | Auth | Description           |
|--------|---------------------|------|-----------------------|
| GET    | `/health/live`      | none | Liveness probe        |
| GET    | `/health/ready`     | none | Readiness probe       |

### Auth

| Method | Path             | Auth   | Description                       |
|--------|------------------|--------|-----------------------------------|
| POST   | `/auth/token`    | none   | Exchange credentials for a JWT    |
| GET    | `/auth/me`       | bearer | Return the current caller's claims |

`POST /auth/token` accepts standard OAuth2 form fields:

```
username=<email>&password=<password>&grant_type=password
```

### Sensors

| Method | Path                | Role required | Description                  |
|--------|---------------------|---------------|------------------------------|
| POST   | `/sensors`          | operator      | Ingest one reading           |
| GET    | `/sensors/recent`   | viewer        | List the most recent readings|

Example request body:

```json
{
  "sensor_id": "traffic-001",
  "kind": "traffic",
  "value": 42.0,
  "unit": "vehicles/min",
  "latitude": -25.7479,
  "longitude": 28.2293
}
```

### Traffic

| Method | Path                  | Role required | Description                  |
|--------|-----------------------|---------------|------------------------------|
| GET    | `/traffic/summary`    | viewer        | Aggregated traffic snapshot  |

## Response Envelope

All SmartCito application APIs should return this traceable JSON envelope:

```json
{
  "status": "success",
  "timestamp": "2026-05-22T09:03:00Z",
  "request_id": "uuid",
  "data": {},
  "meta": {
    "version": "v1",
    "source": "smartcito-backend"
  }
}
```

## Platform Resources

| Method | Path | Role required | Description |
|---|---|---|---|
| GET | `/devices` | viewer | List registered devices |
| POST | `/devices` | operator | Register a device |
| GET | `/devices/{device_id}` | viewer | Fetch one device |
| PATCH | `/devices/{device_id}/status` | operator | Update device status |
| GET | `/cameras` | viewer | List cameras with stream/health state |
| GET | `/gps/live` | viewer | Current GPS coordinates |
| GET | `/gps/{device_id}/history` | viewer | GPS route history |
| GET | `/events` | viewer | Operational events and alerts |
| GET | `/map/layers` | viewer | GeoJSON and marker data |
| WS | `/ws/gps` | token | Live GPS updates |
| WS | `/ws/events` | token | Live event stream |

## Roles

| Role     | Can read | Can ingest | Can administer |
|----------|----------|------------|----------------|
| viewer   | ✅       | ❌         | ❌             |
| operator | ✅       | ✅         | ❌             |
| admin    | ✅       | ✅         | ✅             |

## Errors

All errors use the FastAPI default shape:

```json
{ "detail": "Human-readable error message" }
```

The webapp `api/client.ts` normalizes these into `{ status, message }`.
