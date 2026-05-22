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

# SmartCito

**Sovereign edge-intelligence platform for cities and infrastructure.**

SmartCito unifies IoT, GPS, cameras, 2D/3D maps, AI, cryptography, and secure edge compute into a single auditable operations dashboard.

---

## Operational Overview

![SmartCito Operational Flow](docs/diagrams/smartcito-architecture.svg)

End-to-end flow:
**Edge Devices → Edge Compute → Location Fusion + ATP Ledger → Operator Dashboard**

---

## Edge Data Flow

![SmartCito Edge Data Flow](docs/diagrams/edge-data-flow.svg)

Every hop is authenticated, encrypted, and logged to the ATP ledger.

---

## Location Intelligence (Map Module)

The **Map module** (`/map`) powers SmartCito's sovereign location intelligence: country selection, region/area-code mapping, IP geolocation, GPS validation, and multi-source fusion with confidence scoring.

![Location Fusion Engine](docs/diagrams/location-fusion.svg)

| Source | Weight | Notes |
| ------ | ------ | ----- |
| GPS | 1.0 | Highest accuracy when available |
| IP Geolocation | 0.6 | ASN + ISP + city |
| Area Code | 0.4 | Country → region → city → coords |
| User Selection | 0.3 | Country / region fallback |


See [`map/README.md`](map/README.md) for full API and usage.

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

For a single wiki-style project entry point, start with [`docs/WIKI.md`](docs/WIKI.md).

For pilot or hardware-backed deployments, see [`docs/DOCKER_DEPLOYMENT.md`](docs/DOCKER_DEPLOYMENT.md)
and [`hardware/`](hardware/).


---

## Dashboard — 2D / 3D Map View

![SmartCito Dashboard Map View](docs/diagrams/dashboard-map-view.svg)

The dashboard renders:

- Authenticated device pins (IoT, cameras, GPS, edge Pis)
- Live camera popups linked to GPS coordinates
- Confidence-scored unified location
- 3D operational scene (`dashboard/src/components/Scene3DOperations.jsx`)

---

## Module Layout

| Folder | Purpose |
| ------ | ------- |
| `ai/` | AI threat detection and inference |
| `iot/` | IoT device registration and ingestion |
| `gps/` | GPS readers and validators |
| `camera/` | Camera streaming and frame processing |
| `map/` | **Location intelligence: country/region/area-code/IP/GPS fusion + 2D/3D rendering** |
| `security/` | Authentication and ATP trust scoring |
| `crypto/` | Cryptography primitives and validation |
| `containers/` | Debian-based container builds |
| `openstack/` | OpenStack deployment assets |
| `debian/` | Debian build rules |
| `k8s/` | Kubernetes manifests |
| `tests/` | Cross-module integration tests |
| `docs/` | Architecture, diagrams, release notes |

---

## Releases


- [SmartCito Edge v1.0](docs/SMARTCITO_EDGE_V1_RELEASE.md) — IoT, GPS, Map & Camera Integration

If you find a vulnerability, please **do not open a public issue**. Follow the
disclosure process in [`SECURITY.md`](SECURITY.md).

SmartCito targets compatibility with:

- **GDPR**
- **POPIA**
- **ISO/IEC 27001** practices
- **NIST Cybersecurity Framework** controls


---

## CI/CD

SmartCito uses a multi-stage GitLab pipeline: **prepare → build → test → scan → package → deploy → audit**.

See [`.gitlab-ci.yml`](.gitlab-ci.yml).

---

## Security

- All device communication is encrypted and token-authenticated
- All location events are HMAC-signed into the ATP ledger
- Only authenticated, validated devices appear on the map
- Containers are Debian-based for OpenStack and Kubernetes compatibility
