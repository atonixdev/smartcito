<!--
================================================================================
 SmartCito — Urban Data Backbone for Smart Cities
================================================================================
 File: README.md
 Purpose:
   Top-level entry point for the SmartCito project. This document gives
   contributors, city stakeholders, and researchers a fast, complete overview
   of WHAT the project is, WHY it exists, HOW it is organized, and HOW to
   participate.

 Audience:
   - New developers evaluating the project on GitHub.
   - City IT / innovation teams considering a pilot.
   - Researchers studying smart-city data backbones.

 Conventions:
   - Every file in this repository starts with a documentation header similar
     to this one. Keep that pattern when contributing.
================================================================================
-->

# SmartCito — Urban Data Backbone

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Status: Alpha](https://img.shields.io/badge/status-alpha-orange.svg)](#project-status)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](CONTRIBUTING.md)

> **A secure, open, and scalable data backbone that unifies IoT, traffic, utilities,
> surveillance and citizen services into one real‑time, privacy‑respecting hub.**

SmartCito is the reference implementation of an **Urban Data Backbone** — the
"missing middleware" for smart cities. It collects, normalizes, secures, and
exposes urban data so that dashboards, AI models, and citizen apps can all
speak a common language.

---

## Table of Contents

1. [Why SmartCito?](#why-smartcito)
2. [Key Features](#key-features)
3. [High-Level Architecture](#high-level-architecture)
4. [Repository Layout](#repository-layout)
5. [Quick Start](#quick-start)
6. [Technology Stack](#technology-stack)
7. [Roadmap](#roadmap)
8. [Contributing](#contributing)
9. [Security & Compliance](#security--compliance)
10. [Project Status](#project-status)
11. [License](#license)

---

## Why SmartCito?

Modern cities run on data, but that data lives in **silos**:

- Traffic systems don't talk to utility grids.
- CCTV feeds are disconnected from emergency dispatch.
- IoT sensors generate terabytes of data with no central coordination.
- Privacy regulations (GDPR, POPIA) are hard to enforce across vendors.

The result: **slow response times, wasted resources, and avoidable security risks**.

SmartCito provides the missing **backbone** — a vendor‑neutral, open‑source
platform that any city, university, or contributor can deploy, audit, and extend.

---

## Key Features

| Capability | Description |
|---|---|
| 🛰️ **Unified Ingestion** | MQTT, Kafka, HTTP, and gRPC ingress for any IoT or legacy system. |
| 🧠 **Real‑time Analytics** | Streaming pipelines for traffic, air quality, and anomaly detection. |
| 📊 **Live Dashboards** | React + D3 visualizations; Grafana/Kibana compatible. |
| 🔐 **Security by Design** | TLS in transit, AES‑256 at rest, RBAC, audit logs. |
| 🧩 **Plug-in Connectors** | Add new sensor types or city systems via a documented connector SDK. |
| ⚖️ **Compliance Helpers** | Data residency, retention, and consent primitives for GDPR / POPIA. |
| 🌍 **Open Governance** | Apache 2.0 licensed, RFC-style proposals, public roadmap. |

---

## High-Level Architecture

```
            ┌────────────────────────────────────────────────────┐
            │                  Citizen & Ops Apps                │
            │   React Dashboard · Mobile · 3rd-party Services    │
            └───────────────────┬────────────────────────────────┘
                                │  REST / GraphQL / WebSocket
            ┌───────────────────▼────────────────────────────────┐
            │           SmartCito API Gateway (FastAPI)          │
            │     AuthN/Z · Rate-limit · Schema · Audit Logs     │
            └───────────────────┬────────────────────────────────┘
                                │
   ┌───────────────┬────────────┴───────────┬────────────────────┐
   │ Streaming     │ Storage                │ Analytics          │
   │ Kafka / MQTT  │ PostgreSQL · HBase     │ Spark · ML Models  │
   │ Spark Stream  │ Redis cache · HDFS     │ Anomaly detection  │
   └───────────────┴────────────────────────┴────────────────────┘
                                │
            ┌───────────────────▼────────────────────────────────┐
            │      IoT / City Systems · CCTV · Traffic · Grid    │
            └────────────────────────────────────────────────────┘
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full deep dive.

---

## Repository Layout

```
smartcito/
├── citosmart/              # FastAPI service: APIs, ingestion, security, analytics
│   └── app/
│       ├── api/v1/       # HTTP endpoints
│       ├── core/         # Config, logging, security, AES-GCM helpers
│       ├── db/           # SQLAlchemy async engine + ORM models
│       ├── services/     # MQTT, Kafka, analytics, frame parser
│       └── dash_app/     # Plotly Dash live analytics side-app
├── webapp/             # React + Vite + TypeScript dashboard
├── native/               # Optional C11 performance extensions (opt-in build)
├── docs/                 # Architecture, API, security and contributor docs
├── .github/              # CI workflows, issue and PR templates
├── docker-compose.yml    # One-command local stack
├── .env.example          # Environment variables template
├── CONTRIBUTING.md       # How to contribute
├── CODE_OF_CONDUCT.md    # Community standards
├── SECURITY.md           # Vulnerability disclosure policy
├── LICENSE               # Apache 2.0
└── README.md             # You are here
```

Every source file ships with a **documentation header** explaining its purpose,
inputs, outputs, and design decisions — making the codebase easy to learn.

---

## Quick Start

### Prerequisites

- **Docker** ≥ 24 and **Docker Compose** ≥ 2.20
- **Python** 3.11+ (for local citosmart dev)
- **Node.js** 20+ and **pnpm** or **npm** (for local webapp dev)

### One-Command Local Stack

```bash
git clone https://github.com/atonixdev/smartcito.git
cd smartcito
cp .env.example .env
docker compose up --build
```

This launches:

| Service     | URL                        | Purpose                       |
|-------------|----------------------------|-------------------------------|
| Webapp    | http://localhost:5173      | React dashboard               |
| Citosmart API | http://localhost:8000      | FastAPI (OpenAPI at `/docs`)  |
| PostgreSQL  | localhost:5432             | Relational store              |
| Redis       | localhost:6379             | Cache & pub/sub               |
| Kafka       | localhost:9092             | Event streaming               |

### Local Citosmart Development

```bash
cd citosmart
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Local Webapp Development

```bash
cd webapp
npm install
npm run dev
```

Detailed walkthroughs live in [`docs/`](docs/).

---

## Technology Stack

> **Python-first** for orchestration, APIs, analytics, and visualization.
> **C** only where raw performance matters (low-level drivers, hot-path parsing).

| Layer            | Tools                                                                              |
|------------------|------------------------------------------------------------------------------------|
| Citosmart API      | **Python 3.11**, **FastAPI**, Pydantic v2, SQLAlchemy 2 (asyncpg)                  |
| IoT Ingestion    | **paho-mqtt**, **kafka-python** / aiokafka, asyncio                                |
| Streaming / ML   | scikit-learn (default); **PySpark** or **Dask** for big-data scale; TensorFlow opt.|
| Storage          | PostgreSQL (SQLAlchemy), MongoDB (pymongo), HBase (happybase) optional             |
| Cache            | Redis (default), Memcached (optional)                                              |
| Webapp         | **React 18**, **TypeScript**, Vite, TanStack Query, D3.js                          |
| Analytics UI     | **Plotly Dash** side-app at `:8050`                                                |
| AuthN / AuthZ    | OAuth2 / OIDC, **PyJWT**, RBAC                                                     |
| Security         | **cryptography** (AES-256-GCM, HKDF), TLS, audit logs                              |
| Native ext.      | Optional **C11** module in `native/` for fast frame parsing                        |
| Observability    | Prometheus, Grafana, OpenTelemetry                                                 |
| Packaging        | Docker, Docker Compose, Helm (planned)                                             |

---

## Roadmap

- [x] Phase 0 — Public scaffolding and contributor docs
- [ ] Phase 1 — Pilot: traffic + CCTV + utilities ingestion
- [ ] Phase 2 — Real‑time dashboard with role-based views
- [ ] Phase 3 — Predictive analytics (traffic, air quality)
- [ ] Phase 4 — Compliance toolkit (GDPR / POPIA)
- [ ] Phase 5 — Multi-city federation & Helm charts

Track progress in [GitHub Projects](https://github.com/atonixdev/smartcito/projects).

---

## Contributing

We ❤️ contributors. SmartCito is an **open project** designed to grow with
the community.

- Read [`CONTRIBUTING.md`](CONTRIBUTING.md) for workflow, branch naming, and
  code style.
- See "good first issue" labels for easy entry points.
- Join discussions in GitHub Issues.

---

## Security & Compliance

If you find a vulnerability, please **do not open a public issue**. Follow the
disclosure process in [`SECURITY.md`](SECURITY.md).

SmartCito targets compatibility with:

- **GDPR** (EU)
- **POPIA** (South Africa)
- **ISO/IEC 27001** practices
- **NIST Cybersecurity Framework** controls

---

## Project Status

> 🟠 **Alpha.** APIs and schemas may change. Do not use in production yet.

---

## License

Released under the [Apache License 2.0](LICENSE). Contributions are accepted
under the same license via the standard "inbound = outbound" rule.
