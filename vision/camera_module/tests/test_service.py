from fastapi.testclient import TestClient

from camera_module.service import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "camera-module"}


def test_probe_builds_rtsp_stream() -> None:
    response = client.post(
        "/probe",
        json={"device_id": "cam-1", "host": "camera.local", "path": "/stream/main"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["device_id"] == "cam-1"
    assert payload["protocol"] == "rtsp"
    assert payload["stream_uri"].startswith("rtsp://camera.local")