"""
================================================================================
 File: citosmart/tests/test_events_stream.py
 Purpose: Focused tests for the dashboard realtime event stream.
================================================================================
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.services.realtime_bus import realtime_bus_service
from app.main import app


def test_events_stream_emits_command_center_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _snapshot() -> dict[str, object]:
        return {
            "type": "command-center.snapshot",
            "events": [],
            "alerts": [],
            "control_plane": {"controls": []},
            "map": {"devices": []},
            "surveillance": {},
        }

    monkeypatch.setattr(realtime_bus_service, "snapshot", _snapshot)

    token = create_access_token(subject="viewer@orca.dev", role="viewer")

    with TestClient(app) as client:
        with client.websocket_connect(f"/api/v1/events/stream?token={token}") as websocket:
            payload = websocket.receive_json()

    assert payload["type"] == "command-center.snapshot"
    assert {"events", "alerts", "control_plane", "map", "surveillance"} <= set(payload)
    assert "devices" in payload["map"]
    assert "controls" in payload["control_plane"]