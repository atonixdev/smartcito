"""
================================================================================
 File: citosmart/app/schemas/quantum.py
 Purpose:
   Pydantic schemas for Orca's quantum-ready security surface.

   These models describe supported PQC algorithms, imported QKD key metadata,
   and the hybrid envelope API used to protect sensitive payloads.
================================================================================
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class PqcKemAlgorithm(str, Enum):
    """NIST-standardized or migration-target KEM identifiers."""

    ML_KEM_512 = "ml-kem-512"
    ML_KEM_768 = "ml-kem-768"
    ML_KEM_1024 = "ml-kem-1024"


class PqcSignatureAlgorithm(str, Enum):
    """PQC signature families Orca tracks for future adoption."""

    ML_DSA_65 = "ml-dsa-65"
    SLH_DSA_SHA2_128S = "slh-dsa-sha2-128s"


class QuantumSecurityProfile(BaseModel):
    """Advertised quantum-ready posture for the running service."""

    hybrid_mode: bool
    symmetric_baseline: str
    supported_kems: list[PqcKemAlgorithm]
    supported_signatures: list[PqcSignatureAlgorithm]
    qkd_ingest_enabled: bool


class QkdKeyImportIn(BaseModel):
    """Request body for importing externally derived QKD key material."""

    model_config = ConfigDict(extra="forbid")

    key_id: str = Field(..., min_length=3, max_length=128)
    source: str = Field(..., min_length=3, max_length=128, examples=["satellite-qkd-gateway"])
    key_material_b64: str = Field(..., min_length=16)
    expires_at: datetime | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class QkdKeyMetadata(BaseModel):
    """Non-secret metadata returned for imported QKD keys."""

    key_id: str
    source: str
    fingerprint: str
    imported_at: datetime
    expires_at: datetime | None
    metadata: dict[str, str]


class HybridEnvelopeIn(BaseModel):
    """Payload to encrypt using Orca's hybrid quantum-ready envelope."""

    model_config = ConfigDict(extra="forbid")

    plaintext: str = Field(..., min_length=1)
    purpose: str = Field(..., min_length=3, max_length=128)
    pqc_kem: PqcKemAlgorithm = PqcKemAlgorithm.ML_KEM_768
    qkd_key_id: str | None = None
    associated_data: str | None = None


class HybridEnvelopeOut(BaseModel):
    """Encrypted payload plus metadata describing the hybrid protections used."""

    ciphertext_b64: str
    pqc_kem: PqcKemAlgorithm
    symmetric_cipher: str = "aes-256-gcm"
    qkd_key_id: str | None
    fingerprint: str
