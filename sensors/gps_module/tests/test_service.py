from fastapi.testclient import TestClient

from gps_module.service import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "gps-module"}


def test_parse_sentence() -> None:
    response = client.post(
        "/parse",
        json={"sentence": "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["quality"] == 1
    assert payload["satellites"] == 8