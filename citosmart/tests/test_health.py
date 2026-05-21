"""
================================================================================
 File: backend/tests/test_health.py
 Purpose: Smoke tests for the health endpoints. These tests double as the
          canary that proves the FastAPI app can boot in CI.
================================================================================
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_liveness_returns_200() -> None:
    res = client.get("/api/v1/health/live")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "alive"
    assert body["service"] == "smartcito-api"


def test_readiness_returns_200() -> None:
    res = client.get("/api/v1/health/ready")
    assert res.status_code == 200
    assert res.json()["status"] == "ready"


def test_openapi_schema_available() -> None:
    res = client.get("/openapi.json")
    assert res.status_code == 200
    assert res.json()["info"]["title"] == "SmartCito"
