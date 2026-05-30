"""
================================================================================
 File: orcaapi/app/api/v1/endpoints/health.py
 Purpose:
   Liveness and readiness probes for orchestrators (Docker, Kubernetes).

   - /health/live  → Always returns 200 if the process is up.
   - /health/ready → Returns 200 only when downstream dependencies are usable.
================================================================================
"""

from __future__ import annotations

import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, status
from pydantic import BaseModel
from redis.asyncio import Redis

from app import __version__
from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.services.cache import cache_service

router = APIRouter()


class HealthResponse(BaseModel):
    """Standard health-check payload."""

    status: str
    service: str = "orca-api"
    version: str = __version__


class DependencyStatus(BaseModel):
    name: str
    ok: bool
    detail: str | None = None


class StatusResponse(BaseModel):
    status: str
    service: str = "orca-api"
    version: str = __version__
    dependencies: list[DependencyStatus]


async def _check_database(session: AsyncSession) -> DependencyStatus:
    try:
        await session.execute(text("SELECT 1"))
        return DependencyStatus(name="postgres", ok=True)
    except Exception as exc:  # noqa: BLE001
        return DependencyStatus(name="postgres", ok=False, detail=str(exc))


def _check_cache() -> DependencyStatus:
    return DependencyStatus(name="memcached", ok=cache_service.is_enabled())


async def _check_redis() -> DependencyStatus:
    settings = get_settings()
    try:
        client = Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
        await client.ping()
        await client.aclose()
        return DependencyStatus(name="redis", ok=True)
    except Exception as exc:  # noqa: BLE001
        return DependencyStatus(name="redis", ok=False, detail=str(exc))


async def _check_kafka_tcp() -> DependencyStatus:
    settings = get_settings()
    endpoint = settings.kafka_bootstrap_servers.split(",")[0].strip()
    host, _, port_str = endpoint.partition(":")
    port = int(port_str or "9092")

    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=1.5)
        writer.close()
        await writer.wait_closed()
        if reader is not None:
            return DependencyStatus(name="kafka", ok=True)
        return DependencyStatus(name="kafka", ok=False, detail="No stream returned")
    except Exception as exc:  # noqa: BLE001
        return DependencyStatus(name="kafka", ok=False, detail=str(exc))


def _check_realtime_configuration() -> DependencyStatus:
    settings = get_settings()
    return DependencyStatus(
        name="realtime-configured",
        ok=(
            bool(settings.drone_gateway_url.strip())
            and bool(settings.mission_control_url.strip())
            and bool(settings.mapping_geospatial_url.strip())
        ),
    )


def _check_configured_dependencies() -> list[DependencyStatus]:
    return [
        DependencyStatus(name="redis-configured", ok=bool(get_settings().redis_url.strip())),
        DependencyStatus(
            name="kafka-configured", ok=bool(get_settings().kafka_bootstrap_servers.strip())
        ),
        _check_realtime_configuration(),
    ]


async def _collect_dependency_status() -> list[DependencyStatus]:
    dependencies: list[DependencyStatus] = []
    async with AsyncSessionLocal() as session:
        dependencies.append(await _check_database(session))
    dependencies.append(await _check_redis())
    dependencies.append(await _check_kafka_tcp())
    dependencies.append(_check_cache())
    dependencies.extend(_check_configured_dependencies())
    return dependencies


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
    """Return readiness based on critical dependency checks."""
    dependencies = await _collect_dependency_status()
    critical = {"postgres", "redis", "kafka", "realtime-configured"}
    ready = all(item.ok for item in dependencies if item.name in critical)
    return HealthResponse(status="ready" if ready else "degraded")


@router.get(
    "/status",
    response_model=StatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Detailed service/dependency status",
)
async def service_status() -> StatusResponse:
    dependencies = await _collect_dependency_status()
    critical = {"postgres", "redis", "kafka", "realtime-configured"}
    ready = all(item.ok for item in dependencies if item.name in critical)
    return StatusResponse(status="ready" if ready else "degraded", dependencies=dependencies)
