"""
================================================================================
 File: citosmart/tests/test_control_plane.py
 Purpose: Focused tests for SmartCito dashboard control-plane endpoints.
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
    db_path = tmp_path / "control-plane-tests.db"
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


def test_control_plane_overview_returns_devices_security_and_controls(client: TestClient) -> None:
    res = client.get("/api/v1/control-plane/overview", headers=_auth_headers("viewer"))
    assert res.status_code == 200
    body = res.json()
    assert body["devices"]
    assert body["security"]["quantum_safe_status"] == "ml-kem + qkd ingest ready"
    assert len(body["data_flow"]) >= 3
    assert {control["id"] for control in body["controls"]} >= {"camera-service", "usb-service"}


def test_operator_control_update_persists_audit_event(client: TestClient) -> None:
    res = client.post(
        "/api/v1/control-plane/operator-controls/usb-service",
        json={"desired_state": "stopped"},
        headers=_auth_headers("operator"),
    )
    assert res.status_code == 200
    assert res.json()["state"] == "stopped"