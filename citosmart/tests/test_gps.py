"""
================================================================================
 File: citosmart/tests/test_gps.py
 Purpose: Focused tests for GPS ingestion and retrieval endpoints.
================================================================================
"""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.v1.endpoints.gps import get_session
from app.core.security import create_access_token
from app.db.base import Base
from app.main import app


def _auth_headers(role: str) -> dict[str, str]:
    token = create_access_token(subject=f"{role}@orca.dev", role=role)
    return {"Authorization": f"Bearer {token}"}


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _post_point(client: TestClient, payload: dict[str, object]) -> None:
    response = client.post(
        "/api/v1/ingest/gps",
        json=payload,
        headers=_auth_headers("operator"),
    )
    assert response.status_code == 201, response.text


@pytest.fixture()
def client(tmp_path: Path) -> Generator[TestClient, None, None]:
    db_path = tmp_path / "gps-tests.db"
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


def test_gps_ingest_and_last_position(client: TestClient) -> None:
    payload = {
        "device_id": "drone-001",
        "lat": -26.2041,
        "lon": 28.0473,
        "speed": 12.5,
        "heading": 90,
        "ts": "2026-05-26T15:30:12Z",
    }

    ingest_res = client.post(
        "/api/v1/ingest/gps",
        json=payload,
        headers=_auth_headers("operator"),
    )
    assert ingest_res.status_code == 201
    assert ingest_res.json()["device_id"] == "drone-001"

    last_res = client.get(
        "/api/v1/devices/drone-001/last-position",
        headers=_auth_headers("viewer"),
    )
    assert last_res.status_code == 200
    body = last_res.json()
    assert body["lat"] == -26.2041
    assert body["heading"] == 90.0


def test_gps_track_and_live_fleet(client: TestClient) -> None:
    now = datetime.now(timezone.utc)
    _post_point(client, {
        "device_id": "drone-001",
        "lat": -26.2041,
        "lon": 28.0473,
        "ts": _iso(now - timedelta(minutes=4)),
    })
    _post_point(client, {
        "device_id": "drone-001",
        "lat": -26.2045,
        "lon": 28.0480,
        "speed": 13.0,
        "ts": _iso(now - timedelta(minutes=2)),
    })
    _post_point(client, {
        "device_id": "drone-002",
        "lat": -25.7479,
        "lon": 28.2293,
        "ts": _iso(now - timedelta(minutes=90)),
    })

    track_res = client.get(
        f"/api/v1/devices/drone-001/track?from={_iso(now - timedelta(minutes=5))}&to={_iso(now)}",
        headers=_auth_headers("viewer"),
    )
    assert track_res.status_code == 200
    track = track_res.json()
    assert len(track) == 2
    assert track[0]["ts"] < track[1]["ts"]

    live_res = client.get(
        "/api/v1/fleet/live?active_within_minutes=10",
        headers=_auth_headers("viewer"),
    )
    assert live_res.status_code == 200
    body = live_res.json()
    assert body["active_within_minutes"] == 10
    assert [item["device_id"] for item in body["devices"]] == ["drone-001"]


def test_gps_validation_rejects_invalid_coordinates(client: TestClient) -> None:
    response = client.post(
        "/api/v1/ingest/gps",
        json={
            "device_id": "drone-001",
            "lat": -126.2041,
            "lon": 28.0473,
            "ts": "2026-05-26T15:30:12Z",
        },
        headers=_auth_headers("operator"),
    )
    assert response.status_code == 422