# Services

Split-function container services for Orca.

## Purpose

This folder hosts deployable microservice containers used by Kubernetes and
local compose-based testing. The main backend application lives in
`../citosmart/`.

## Services

- `camera-service/`
- `gps-service/`
- `ai-service/`
- `security-service/`

## Local Run

```bash
docker compose -f docker-compose.services.yml up --build
```
