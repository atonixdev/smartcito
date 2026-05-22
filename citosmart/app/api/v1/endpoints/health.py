"""
================================================================================
 File: citosmart/app/api/v1/endpoints/health.py
 Purpose:
   Liveness and readiness probes for orchestrators (Docker, Kubernetes).

   - /health/live  → Always returns 200 if the process is up.
   - /health/ready → Returns 200 only when downstream dependencies are usable.
================================================================================
"""

from __future__ import annotations

from fastapi import APIRouter, Request, status
from pydantic import BaseModel

from app import __version__
from app.schemas.api_response import api_envelope

router = APIRouter()


class HealthResponse(BaseModel):
    """Standard health-check payload."""

    status: str
    service: str = "smartcito-api"
    version: str = __version__


@router.get(
    "/live",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
)
async def liveness() -> HealthResponse:
    """Return 200 if the process is running. Used by orchestrators."""
    return HealthResponse(status="alive")


@router.get(
    "/ready",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
)
async def readiness() -> HealthResponse:
    """Return 200 only when the service can serve traffic.

    TODO: Extend this to actually ping PostgreSQL, Redis, and Kafka and
    return 503 if any required dependency is down.
    """
    return HealthResponse(status="ready")


@router.get("/status/live", summary="Envelope liveness probe")
async def liveness_envelope(request: Request):
    return api_envelope(request, {"status": "alive", "service": "smartcito-api"})


@router.get("/status/ready", summary="Envelope readiness probe")
async def readiness_envelope(request: Request):
    return api_envelope(request, {"status": "ready", "service": "smartcito-api"})
