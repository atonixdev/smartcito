"""
================================================================================
 File: security/service.py
 Purpose:
   Minimal FastAPI security-domain service exposing encryption and posture info.
================================================================================
"""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.core.crypto import decrypt, encrypt

app = FastAPI(title="SmartCito Security Domain")


class EncryptRequest(BaseModel):
    """Request body for demo encryption."""

    plaintext: str = Field(..., min_length=1)
    purpose: str = Field(..., min_length=3)


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
