"""
================================================================================
 File: orcaapi/tests/test_graphql.py
 Purpose: Focused tests for the Orca GraphQL integration endpoint.
================================================================================
"""

from __future__ import annotations

import asyncio
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_session
from app.main import app
from app.services.ingestion import ingestion_service


@pytest.fixture()
def client(tmp_path: Path) -> Generator[TestClient, None, None]:
    db_path = tmp_path / "graphql-tests.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

    async def _override_get_session():
        async with session_factory() as session:
            yield session

    async def _setup() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def _teardown() -> None:
        await engine.dispose()

    asyncio.run(_setup())
    app.dependency_overrides[get_session] = _override_get_session
    ingestion_service._buffer.clear()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    asyncio.run(_teardown())


def _auth_headers(role: str) -> dict[str, str]:
    token = create_access_token(subject=f"{role}@orca.dev", role=role)
    return {"Authorization": f"Bearer {token}"}


def test_graphql_exposes_recent_sensor_readings_and_control_plane(client: TestClient) -> None:
    ingest_response = client.post(
        "/api/v1/sensors",
        json={
            "sensor_id": "graphql-traffic-001",
            "kind": "traffic",
            "value": 19.4,
            "unit": "vehicles/min",
            "metadata": {"source": "graphql-test"},
        },
        headers=_auth_headers("operator"),
    )
    assert ingest_response.status_code == 201

    response = client.post(
        "/api/v1/graphql",
        json={
            "query": """
                query IntegrationHub($limit: Int!) {
                  viewerRole
                  recentSensorReadings(limit: $limit) {
                    sensorId
                    kind
                    value
                    unit
                    metadata
                  }
                  controlPlaneOverview {
                    security {
                      quantumSafeStatus
                    }
                    controls {
                      id
                      actionLabel
                    }
                  }
                }
            """,
            "variables": {"limit": 5},
        },
        headers=_auth_headers("viewer"),
    )

    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body
    assert body["data"]["viewerRole"] == "viewer"
    assert body["data"]["recentSensorReadings"][0]["sensorId"] == "graphql-traffic-001"
    assert body["data"]["recentSensorReadings"][0]["metadata"]["source"] == "graphql-test"
    assert (
        body["data"]["controlPlaneOverview"]["security"]["quantumSafeStatus"]
        == "ml-kem + qkd ingest ready"
    )
    assert {control["id"] for control in body["data"]["controlPlaneOverview"]["controls"]} >= {
        "camera-service",
        "usb-service",
    }


def test_graphql_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/api/v1/graphql",
        json={"query": "query { viewerRole }"},
    )

    assert response.status_code == 401
