# Services

Split-function container services for SmartCito.

## Purpose

This folder hosts deployable microservice containers used by Kubernetes and
local compose-based testing.

## Services

- `api-gateway/`
- `camera-service/`
- `gps-service/`
- `ai-service/`
- `security-service/`

## Local Run

```bash
docker compose -f docker-compose.services.yml up --build
```
