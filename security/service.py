"""
================================================================================
 File: security/service.py
 Purpose:
   Minimal FastAPI security-domain service exposing encryption and posture info.
================================================================================
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from app.core.crypto import (
    build_integrity_record,
    build_secure_envelope,
    decrypt,
    decrypt_secure_envelope,
    encrypt,
    generate_certificate_authority,
    issue_device_certificate,
    verify_integrity_record,
)


load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

app = FastAPI(title="Orca Security Domain")


class EncryptRequest(BaseModel):
    """Request body for demo encryption."""

    plaintext: str = Field(..., min_length=1)
    purpose: str = Field(..., min_length=3)


class IntegrityRequest(BaseModel):
    payload: dict = Field(default_factory=dict)
    signer_id: str = Field(..., min_length=2)


class DeviceCertificateRequest(BaseModel):
    common_name: str = Field(..., min_length=3)
    ca_certificate_pem: str = Field(..., min_length=10)
    ca_private_key_pem: str = Field(..., min_length=10)


class CertificateAuthorityRequest(BaseModel):
    common_name: str = Field(default="orca-dev-ca", min_length=3)


class IntegrityVerifyRequest(BaseModel):
    payload: dict = Field(default_factory=dict)
    record: dict = Field(default_factory=dict)


class SecureEnvelopeRequest(BaseModel):
    payload: dict = Field(default_factory=dict)
    purpose: str = Field(..., min_length=3)
    signer_id: str = Field(..., min_length=2)
    associated: str | None = None


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "security-domain"}


@app.post("/encrypt")
async def encrypt_payload(request: EncryptRequest) -> dict[str, str]:
    blob = encrypt(request.plaintext.encode("utf-8"), purpose=request.purpose)
    recovered = decrypt(blob, purpose=request.purpose).decode("utf-8")
    return {
        "ciphertext_hex": blob.hex(),
        "round_trip": recovered,
    }


@app.post("/integrity/sign")
async def sign_integrity(request: IntegrityRequest) -> dict[str, object]:
    return build_integrity_record(request.payload, signer_id=request.signer_id)


@app.post("/integrity/verify")
async def verify_integrity(request: IntegrityVerifyRequest) -> dict[str, bool]:
    return {"valid": verify_integrity_record(request.payload, request.record)}


@app.post("/pki/ca")
async def create_certificate_authority(request: CertificateAuthorityRequest) -> dict[str, str]:
    return generate_certificate_authority(request.common_name)


@app.post("/pki/device-certificate")
async def create_device_certificate(request: DeviceCertificateRequest) -> dict[str, str]:
    return issue_device_certificate(
        request.common_name,
        ca_certificate_pem=request.ca_certificate_pem,
        ca_private_key_pem=request.ca_private_key_pem,
    )


@app.post("/packet/envelope")
async def create_secure_packet(request: SecureEnvelopeRequest) -> dict[str, object]:
    envelope = build_secure_envelope(
        request.payload,
        purpose=request.purpose,
        signer_id=request.signer_id,
        associated=request.associated,
    )
    return {
        "envelope": envelope,
        "round_trip": decrypt_secure_envelope(envelope, associated=request.associated),
    }
