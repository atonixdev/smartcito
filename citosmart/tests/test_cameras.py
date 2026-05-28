"""
================================================================================
 File: citosmart/tests/test_cameras.py
 Purpose: Focused tests for camera registration and telemetry endpoints.
================================================================================
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.v1.endpoints.cameras import get_session
from app.db.base import Base
from app.core.security import create_access_token
from app.main import app


@pytest.fixture()
def client(tmp_path: Path) -> Generator[TestClient, None, None]:
    db_path = tmp_path / "camera-tests.db"
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
    token = create_access_token(subject=f"{role}@orca.dev", role=role)
    return {"Authorization": f"Bearer {token}"}


def test_camera_registration_and_listing(client: TestClient) -> None:
    registration = {
        "device_id": "body-001",
        "device_type": "body_camera",
        "firmware_version": "1.0.0",
        "capabilities": {
            "gps": True,
            "tamper_detection": True,
            "mount_detection": True,
            "stream_protocols": ["rtsp", "http2"],
            "local_encrypted_storage": True,
        },
        "network": {
            "transport": "5g",
            "signal_profile": "mobile",
        },
        "security": {
            "identity_mode": "secure_element",
            "tls_required": True,
            "storage_encryption": "aes-256",
        },
        "mounting": {
            "magnetic_base": True,
            "mount_sensor_type": "hall_effect",
        },
    }

    create_res = client.post(
        "/api/v1/cameras/register",
        json=registration,
        headers=_auth_headers("operator"),
    )
    assert create_res.status_code == 201
    assert create_res.json()["device_id"] == "body-001"

    list_res = client.get("/api/v1/cameras", headers=_auth_headers("viewer"))
    assert list_res.status_code == 200
    body = list_res.json()
    assert len(body) == 1
    assert body[0]["stream_status"] == "offline"


def test_camera_telemetry_updates_stream_and_location(client: TestClient) -> None:
    client.post(
        "/api/v1/cameras/register",
        json={
            "device_id": "micro-001",
            "device_type": "micro_camera",
            "firmware_version": "2.1.3",
            "capabilities": {
                "gps": True,
                "tamper_detection": True,
                "mount_detection": True,
                "stream_protocols": ["onvif", "rtsp"],
                "local_encrypted_storage": False,
            },
            "network": {
                "transport": "wifi6",
                "signal_profile": "hybrid",
            },
            "security": {
                "identity_mode": "certificate",
                "tls_required": True,
                "storage_encryption": "aes-256",
            },
            "mounting": {
                "magnetic_base": True,
                "mount_sensor_type": "reed_switch",
            },
        },
        headers=_auth_headers("operator"),
    )

    telemetry_res = client.post(
        "/api/v1/cameras/micro-001/telemetry",
        json={
            "stream_status": "live",
            "mounted": True,
            "tamper_detected": False,
            "battery_level": 78,
            "location": {
                "lat": -25.7479,
                "lon": 28.2293,
                "accuracy_m": 3.5,
            },
        },
        headers=_auth_headers("operator"),
    )
    assert telemetry_res.status_code == 200
    body = telemetry_res.json()
    assert body["stream_status"] == "live"
    assert body["location"]["lat"] == -25.7479
    assert body["mounted"] is True


def test_empty_registry_seeds_demo_devices_and_audit_events(client: TestClient) -> None:
    res = client.get("/api/v1/cameras", headers=_auth_headers("viewer"))
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 2
    assert {item["device_id"] for item in body} == {"demo-body-001", "demo-micro-007"}
