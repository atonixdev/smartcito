"""
================================================================================
 File: orcaapi/tests/test_gateway_flow.py
 Purpose:
   Gate-flow contract tests for health, auth, routing, and websocket readiness.
================================================================================
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.main import app
from app.schemas.gps import GPSPointOut
from app.services.gps_tracking import gps_tracking_service


client = TestClient(app)


def _install_gps_ingest_stub() -> None:
    async def _ingest_stub(_session, point):
        return GPSPointOut(
            id=1,
            device_id=point.device_id,
            lat=point.lat,
            lon=point.lon,
            speed=point.speed,
            heading=point.heading,
            ts=point.ts,
            received_at=point.ts,
        )

    setattr(gps_tracking_service, "ingest", _ingest_stub)


def test_gateway_health_chain() -> None:
    live = client.get("/api/v1/health/live")
    ready = client.get("/api/v1/health/ready")
    status = client.get("/api/v1/health/status")

    assert live.status_code == 200
    assert ready.status_code == 200
    assert status.status_code == 200


def test_auth_chain_token_and_role_enforcement() -> None:
    _install_gps_ingest_stub()
    viewer = create_access_token(subject="viewer@orca.dev", role="viewer")
    operator = create_access_token(subject="operator@orca.dev", role="operator")

    viewer_res = client.post(
        "/api/v1/ingest/gps",
        json={
            "device_id": "orca_unit_01",
            "lat": -26.2041,
            "lon": 28.0473,
            "speed": 12.3,
            "heading": 90,
        },
        headers={"Authorization": f"Bearer {viewer}"},
    )
    operator_res = client.post(
        "/api/v1/ingest/gps",
        json={
            "device_id": "orca_unit_01",
            "lat": -26.2041,
            "lon": 28.0473,
            "speed": 12.3,
            "heading": 90,
        },
        headers={"Authorization": f"Bearer {operator}"},
    )

    assert viewer_res.status_code == 403
    assert operator_res.status_code == 201


def test_websocket_flow_events_requires_auth() -> None:
    with client.websocket_connect("/api/v1/events/stream") as websocket:
        payload = websocket.receive_json()
        assert payload["type"] == "command-center.snapshot"


def test_gps_gateway_ingest_and_stream_channel() -> None:
    _install_gps_ingest_stub()
    operator = create_access_token(subject="operator@orca.dev", role="operator")

    ingest = client.post(
        "/api/v1/gps/gateway/ingest",
        json={
            "device_id": "orca_unit_22",
            "latitude": -26.2041,
            "longitude": 28.0473,
            "altitude": 120.5,
            "speed": 14.2,
            "heading": 87.0,
            "timestamp": 1716972000,
            "device_type": "drone",
        },
        headers={"Authorization": f"Bearer {operator}"},
    )

    assert ingest.status_code == 201

    with client.websocket_connect("/api/v1/gps/stream/drone") as websocket:
        frame = websocket.receive_json()
        assert frame["type"] in {"gps.snapshot", "gps.update"}
        assert frame["channel"] == "drone"
