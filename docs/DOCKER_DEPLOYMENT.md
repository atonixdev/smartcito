# Docker Deployment Guide

Orca ships with two Compose entry points:

- [`../docker-compose.yml`](../docker-compose.yml): local development stack
- [`../docker-compose.hardware.yml`](../docker-compose.hardware.yml): hardware-aware overlay for pilot or on-prem environments

## Local Development

```bash
cp .env.example .env
docker compose up --build
```

This is intended for a single developer machine and uses simplified defaults.

## Hardware / Pilot Deployment

```bash
cp .env.example .env
docker compose \
  -f docker-compose.yml \
  -f docker-compose.hardware.yml \
  up -d --build
```

The overlay adds:
- dedicated internal and monitoring networks
- container hardening controls where Compose supports them
- monitoring services (Prometheus + Grafana)
- volume separation for stateful services
- resource reservations and placement hints for GPU and storage-heavy nodes

## Host Expectations

- Docker Engine 24+
- Compose v2.20+
- NVIDIA container runtime on GPU hosts if AI inference runs in containers
- SSD-backed volumes for PostgreSQL and Kafka
- TLS termination at a trusted reverse proxy or service mesh layer

## Operational Split

- keep the base file small and developer-friendly
- keep hardware and pilot concerns in the overlay
- promote to Kubernetes or OpenStack orchestration when you need HA, rolling
  upgrades, or multi-host scheduling
