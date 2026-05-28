"""
================================================================================
 File: citosmart/tests/test_quantum.py
 Purpose: Focused tests for quantum-ready security endpoints and helpers.
================================================================================
"""

from __future__ import annotations

import base64

from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.main import app
from app.schemas.quantum import HybridEnvelopeIn, PqcKemAlgorithm, QkdKeyImportIn
from app.services.quantum_security import quantum_security_service

client = TestClient(app)


def _auth_headers(role: str) -> dict[str, str]:
    token = create_access_token(subject=f"{role}@orca.dev", role=role)
    return {"Authorization": f"Bearer {token}"}


def test_quantum_profile_endpoint_returns_supported_algorithms() -> None:
    quantum_security_service.clear()

    res = client.get("/api/v1/quantum/profile", headers=_auth_headers("viewer"))
    assert res.status_code == 200
    body = res.json()
    assert body["hybrid_mode"] is True
    assert "ml-kem-768" in body["supported_kems"]


def test_import_qkd_key_and_list_metadata() -> None:
    quantum_security_service.clear()

    key_material = base64.b64encode(b"q" * 32).decode("utf-8")
    create_res = client.post(
        "/api/v1/quantum/qkd-keys",
        json={
            "key_id": "qkd-link-001",
            "source": "fiber-qkd-gateway",
            "key_material_b64": key_material,
            "metadata": {"zone": "metro-core"},
        },
        headers=_auth_headers("admin"),
    )
    assert create_res.status_code == 201
    assert create_res.json()["key_id"] == "qkd-link-001"

    list_res = client.get("/api/v1/quantum/qkd-keys", headers=_auth_headers("viewer"))
    assert list_res.status_code == 200
    assert list_res.json()[0]["source"] == "fiber-qkd-gateway"


def test_hybrid_envelope_round_trip_uses_imported_qkd_material() -> None:
    quantum_security_service.clear()
    quantum_security_service.import_qkd_key(
        QkdKeyImportIn(
            key_id="sat-link-9",
            source="satellite-qkd-gateway",
            key_material_b64=base64.b64encode(b"k" * 48).decode("utf-8"),
            metadata={"hop": "leo-uplink"},
        )
    )

    envelope = quantum_security_service.create_hybrid_envelope(
        HybridEnvelopeIn(
            plaintext="classified telemetry",
            purpose="camera-feed-manifest",
            pqc_kem=PqcKemAlgorithm.ML_KEM_768,
            qkd_key_id="sat-link-9",
            associated_data="camera-7",
        )
    )

    plaintext = quantum_security_service.decrypt_hybrid_envelope(
        envelope.ciphertext_b64,
        purpose="camera-feed-manifest",
        pqc_kem=PqcKemAlgorithm.ML_KEM_768,
        qkd_key_id="sat-link-9",
        associated_data="camera-7",
    )
    assert plaintext == "classified telemetry"
