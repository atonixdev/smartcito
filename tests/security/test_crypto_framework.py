from __future__ import annotations

from smartcito_shared.crypto import (
    build_integrity_record,
    build_secure_envelope,
    decrypt_secure_envelope,
    generate_certificate_authority,
    issue_device_certificate,
    verify_integrity_record,
)


def test_integrity_record_round_trip_verifies() -> None:
    payload = {"mission_id": "mission-001", "waypoints": [1, 2, 3]}

    record = build_integrity_record(payload, signer_id="operator-001")

    assert record["hash"]["sha256"]
    assert verify_integrity_record(payload, record) is True


def test_secure_envelope_round_trip_decrypts() -> None:
    payload = {"telemetry": {"latitude": -25.7, "longitude": 28.2}, "zone": "cbd"}

    envelope = build_secure_envelope(payload, purpose="telemetry", signer_id="drone-001", associated="drone-001")

    assert envelope["algorithm"] == "AES-256-GCM"
    assert decrypt_secure_envelope(envelope, associated="drone-001") == payload


def test_device_certificate_is_issued_from_ca() -> None:
    ca = generate_certificate_authority("smartcito-test-ca")
    device = issue_device_certificate(
        "drone-001.smartcito",
        ca_certificate_pem=ca["certificate_pem"],
        ca_private_key_pem=ca["private_key_pem"],
    )

    assert "BEGIN CERTIFICATE" in ca["certificate_pem"]
    assert "BEGIN CERTIFICATE" in device["certificate_pem"]
    assert device["ca_fingerprint_sha256"] == ca["fingerprint_sha256"]