"""
================================================================================
 File: citosmart/tests/test_map_integration.py
 Purpose: Tests for SmartCito IoT -> GPS -> Map -> Camera endpoints.
================================================================================
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_session
from app.main import app


@pytest.fixture()
def client(tmp_path: Path) -> Generator[TestClient, None, None]:
    db_path = tmp_path / "map-tests.db"
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

    import asyncio

    asyncio.run(_setup())
    app.dependency_overrides[get_session] = _override_get_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    asyncio.run(_teardown())


def _auth_headers(role: str) -> dict[str, str]:
    token = create_access_token(subject=f"{role}@smartcito.dev", role=role)
    return {"Authorization": f"Bearer {token}"}


def test_map_overview_returns_verified_devices_only(client: TestClient) -> None:
    res = client.get("/api/v1/control-plane/map", headers=_auth_headers("viewer"))
    assert res.status_code == 200
    body = res.json()
    assert body["devices"]
    assert all(device["trust_score"] > 80 for device in body["devices"])
    assert "camera-overlays" in body["visible_layers"]


def test_raspberry_pi_registration_is_audited_and_visible_when_verified(client: TestClient) -> None:
    res = client.post(
        "/api/v1/control-plane/map/register",
        json={
            "device_id": "raspi-mobile-002",
            "device_type": "iot",
            "name": "Raspberry Pi Mobile Sensor",
            "latitude": -25.741,
            "longitude": 28.218,
            "trust_score": 91,
            "camera_feed_url": "rtsp://edge/raspi-mobile-002/camera",
            "sensor_type": "traffic-density",
            "sensor_value": 0.82,
            "mqtt_topic": "smartcito/pi/raspi-mobile-002/events",
        },
        headers=_auth_headers("operator"),
    )
    assert res.status_code == 201
    assert res.json()["trust_score"] == 91

    overview = client.get("/api/v1/control-plane/map", headers=_auth_headers("viewer")).json()
    assert "raspi-mobile-002" in {device["device_id"] for device in overview["devices"]}


def test_scene_overview_returns_3d_ready_devices_and_threats(client: TestClient) -> None:
    res = client.get("/api/v1/control-plane/scene", headers=_auth_headers("viewer"))
    assert res.status_code == 200
    body = res.json()
    assert body["devices"]
    assert body["threats"]
    assert "threat-waves" in body["layers"]
    first_device = body["devices"][0]
    assert {"x", "y", "z", "gps_path_3d", "status_color"} <= set(first_device)