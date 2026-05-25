"""
================================================================================
 File: ingestion/kafka_producer_service.py
 Purpose:
   Lightweight HTTP surface for the Kafka ingestion producer. Exposes
   liveness/readiness endpoints so the container can be health-checked when it
   runs as a long-lived service in Docker or OpenStack.
================================================================================
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from dotenv import load_dotenv

from ingestion.storage_config import storage_runtime_summary


load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

app = FastAPI(title="SmartCito Ingestion Kafka Producer")


def _broker_url() -> str:
    return (
        os.getenv("KAFKA_BROKER_URL")
        or os.getenv("MESSAGE_BUS_URL")
        or os.getenv("KAFKA_BOOTSTRAP_SERVERS")
        or "kafka:9092"
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ingestion-kafka-producer",
    }


@app.get("/ready")
async def readiness() -> dict[str, object]:
    return {
        "status": "ready",
        "bootstrap_servers": _broker_url(),
        "topic": os.getenv("KAFKA_SENSOR_TOPIC", "smartcito.sensors.raw"),
        "storage": storage_runtime_summary(),
    }