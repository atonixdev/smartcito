"""
================================================================================
 File: ingestion/spark_service.py
 Purpose:
   Lightweight HTTP surface for the Spark-style ingestion worker. Exposes
   liveness/readiness endpoints and the current declarative pipeline shape.
================================================================================
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from dotenv import load_dotenv

from ingestion.spark_job import build_stream_description
from ingestion.storage_config import storage_runtime_summary


load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

app = FastAPI(title="SmartCito Ingestion Spark Worker")


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ingestion-spark",
    }


@app.get("/ready")
async def readiness() -> dict[str, object]:
    return {
        "status": "ready",
        "deployment_mode": "dedicated-image",
        "cache_backend": "memcached",
        "storage": storage_runtime_summary(),
        "pipeline": build_stream_description(),
    }


@app.get("/pipeline")
async def pipeline() -> dict[str, object]:
    return build_stream_description()