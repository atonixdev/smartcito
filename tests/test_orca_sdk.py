from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from urllib.error import HTTPError

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sdk" / "python"))

from orca_sdk import OrcaApiError, OrcaClient


class _FakeResponse:
    def __init__(self, payload: object) -> None:
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


def test_sdk_adds_auth_header_and_decodes_json(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request, timeout: float):
        captured["url"] = request.full_url
        captured["auth"] = request.get_header("Authorization")
        captured["timeout"] = timeout
        return _FakeResponse({"status": "alive"})

    monkeypatch.setattr("orca_sdk.client.urllib_request.urlopen", fake_urlopen)
    client = OrcaClient("http://orca.local/", token="demo-token", timeout=4.5)

    response = client.health_live()

    assert response == {"status": "alive"}
    assert captured == {
        "url": "http://orca.local/api/v1/health/live",
        "auth": "Bearer demo-token",
        "timeout": 4.5,
    }


def test_sdk_encodes_track_query_parameters(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request, timeout: float):
        captured["url"] = request.full_url
        return _FakeResponse([])

    monkeypatch.setattr("orca_sdk.client.urllib_request.urlopen", fake_urlopen)
    client = OrcaClient("https://orca.example")

    client.get_device_track(
        "drone alpha",
        from_ts="2026-05-30T10:00:00Z",
        to_ts="2026-05-30T10:05:00Z",
        limit=25,
    )

    assert captured["url"] == (
        "https://orca.example/api/v1/devices/drone%20alpha/track"
        "?limit=25&from=2026-05-30T10%3A00%3A00Z&to=2026-05-30T10%3A05%3A00Z"
    )


def test_sdk_raises_structured_error_for_http_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(request, timeout: float):
        raise HTTPError(
            request.full_url,
            404,
            "Not Found",
            hdrs=None,
            fp=io.BytesIO(b'{"detail":"Unknown operator control \'missing\'"}'),
        )

    monkeypatch.setattr("orca_sdk.client.urllib_request.urlopen", fake_urlopen)
    client = OrcaClient("https://orca.example")

    with pytest.raises(OrcaApiError) as exc_info:
        client.update_operator_control("missing", "running")

    assert exc_info.value.status_code == 404
    assert str(exc_info.value) == "Unknown operator control 'missing'"
    assert exc_info.value.payload == {"detail": "Unknown operator control 'missing'"}


def test_sdk_posts_camera_registration_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request, timeout: float):
        captured["url"] = request.full_url
        captured["body"] = request.data.decode("utf-8")
        captured["content_type"] = request.get_header("Content-type")
        return _FakeResponse({"device_id": "cam-001"})

    monkeypatch.setattr("orca_sdk.client.urllib_request.urlopen", fake_urlopen)
    client = OrcaClient("https://orca.example")

    response = client.register_camera({"device_id": "cam-001"})

    assert response == {"device_id": "cam-001"}
    assert captured == {
        "url": "https://orca.example/api/v1/cameras/register",
        "body": '{"device_id": "cam-001"}',
        "content_type": "application/json",
    }