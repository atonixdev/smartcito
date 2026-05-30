from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "orcaapi"))
sys.path.insert(0, str(ROOT))

from security.service import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "security-domain"}


def test_encrypt_round_trip() -> None:
    response = client.post(
        "/encrypt",
        json={"plaintext": "incident payload", "purpose": "audit-log"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["round_trip"] == "incident payload"
    assert payload["ciphertext_hex"]