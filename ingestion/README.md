# Ingestion

IoT + camera data pipelines for Orca.

## Purpose

This module hosts connectors and streaming pipelines that move raw data from
edge devices (IoT sensors, CCTV cameras, GPS modules, third-party APIs) into
the Orca core for processing, storage, and analytics.

## Container Images

- `ingestion/Dockerfile`: runs the default Python ingestion job container with `python -m ingestion.spark_job`.
- `ingestion/Dockerfile.spark`: runs the Structured Streaming container with `spark-submit` against `ingestion/streaming_job.py`.
- Both builds copy the `ingestion/` tree, so the image includes this README at `/app/ingestion/README.md` or `/opt/orca/ingestion/README.md`.

## Stack

- **Kafka** — durable event streaming backbone
- **MQTT** — lightweight transport for constrained IoT devices
- **Apache Spark** — batch + structured streaming transformations
- **Python 3.11+** — connector implementations

> The production-grade Python backend API lives under
> [`../citosmart/`](../citosmart/). This folder is for **new connectors**
> and ingestion adapters contributed by the community.

## Layout

```
ingestion/
├── Dockerfile       # Container image for Python ingestion APIs/helpers
├── Dockerfile.spark # Dedicated Spark job image
├── requirements.txt # Runtime dependencies
├── kafka_producer.py# Simple Kafka producer helper
├── spark_job.py     # Declarative pipeline metadata
├── streaming_job.py # Repo-owned Structured Streaming runtime
└── README.md
```

## Adding a New Connector

1. Create `ingestion/connectors/<your_source>/`.
2. Implement the connector following the interface used by
   the backend API service in `citosmart/app/services/`.
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
- Spark job templates and packaged streaming runtime

## How To Run Its Container

```bash
docker build -f ingestion/Dockerfile -t orca-ingestion .
docker run --rm orca-ingestion
```

```bash
docker build -f ingestion/Dockerfile.spark -t orca-ingestion-spark .
docker run --rm orca-ingestion-spark
```

## Example Usage

```bash
python -m ingestion.spark_job
```

```bash
/opt/bitnami/spark/bin/spark-submit --master local[*] ingestion/streaming_job.py
```
