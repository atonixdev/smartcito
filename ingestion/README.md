# Ingestion

IoT + camera data pipelines for SmartCito.

## Purpose

This module hosts connectors and streaming pipelines that move raw data from
edge devices (IoT sensors, CCTV cameras, GPS modules, third-party APIs) into
the SmartCito core for processing, storage, and analytics.

## Stack

- **Kafka** — durable event streaming backbone
- **MQTT** — lightweight transport for constrained IoT devices
- **Apache Spark** — batch + structured streaming transformations
- **Python 3.11+** — connector implementations

> The production-grade Python backend (FastAPI + Kafka + MQTT consumers) lives
> under [`citosmart/`](../citosmart/). This folder is for **new connectors**
> and ingestion adapters contributed by the community.

## Layout

```
ingestion/
├── Dockerfile       # Container image for ingestion jobs
├── requirements.txt # Runtime dependencies
├── kafka_producer.py# Simple Kafka producer helper
├── spark_job.py     # Structured streaming job template
└── README.md
```

## Adding a New Connector

1. Create `ingestion/connectors/<your_source>/`.
2. Implement the connector following the interface used by
   `citosmart/app/services/ingestion.py`.
3. Document configuration (env vars, topics, schemas) in a local `README.md`.
4. Add unit + integration tests under [`../tests/`](../tests/).
5. Submit a PR per the [contribution workflow](../CONTRIBUTING.md).

## Security

- All brokers must be reached over **TLS**.
- Credentials are loaded from environment variables — never commit secrets.
- Apply the project's RBAC policies to any new ingestion endpoint.

## Technologies Used

- Python 3.11
- kafka-python
- Spark job templates

## How To Run Its Container

```bash
docker build -f ingestion/Dockerfile -t smartcito-ingestion .
docker run --rm smartcito-ingestion
```

## Example Usage

```bash
python -m ingestion.spark_job
```
