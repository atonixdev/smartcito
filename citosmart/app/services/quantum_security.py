"""
================================================================================
 File: citosmart/app/services/quantum_security.py
 Purpose:
   Quantum-ready security helpers for SmartCito.

   This service does three concrete things today:
     - Advertises a PQC migration profile.
     - Accepts externally provisioned QKD key material through a stable API.
     - Produces hybrid envelopes using AES-256-GCM plus PQC/QKD metadata.

   It does NOT claim to implement production PQC KEMs itself. Instead, it
   creates the abstraction boundary SmartCito will need when mature PQC/QKD
   libraries and hardware are plugged in later.
================================================================================
"""

from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import dataclass
from datetime import datetime, timezone

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.core.config import get_settings
from app.core.crypto import decrypt, encrypt
from app.schemas.quantum import (
    HybridEnvelopeIn,
    HybridEnvelopeOut,
    PqcKemAlgorithm,
    PqcSignatureAlgorithm,
    QkdKeyImportIn,
    QkdKeyMetadata,
    QuantumSecurityProfile,
)

_NONCE_LEN = 12
_KEY_LEN = 32


@dataclass(slots=True)
class _StoredQkdKey:
    """Internal encrypted representation of imported QKD material."""

    encrypted_material: bytes
    metadata: QkdKeyMetadata


class QuantumSecurityService:
    """In-process quantum-ready control plane for security integrations."""

    def __init__(self) -> None:
        self._qkd_keys: dict[str, _StoredQkdKey] = {}

    def profile(self) -> QuantumSecurityProfile:
        """Return the currently supported quantum-ready posture."""
        return QuantumSecurityProfile(
            hybrid_mode=True,
            symmetric_baseline="aes-256-gcm",
            supported_kems=[
                PqcKemAlgorithm.ML_KEM_512,
                PqcKemAlgorithm.ML_KEM_768,
                PqcKemAlgorithm.ML_KEM_1024,
            ],
            supported_signatures=[
                PqcSignatureAlgorithm.ML_DSA_65,
                PqcSignatureAlgorithm.SLH_DSA_SHA2_128S,
            ],
            qkd_ingest_enabled=True,
        )

    def import_qkd_key(self, request: QkdKeyImportIn) -> QkdKeyMetadata:
        """Import externally derived key material and store it encrypted at rest."""
        raw_key = base64.b64decode(request.key_material_b64, validate=True)
        if len(raw_key) < 32:
            raise ValueError("QKD key material must be at least 32 bytes")

        metadata = QkdKeyMetadata(
            key_id=request.key_id,
            source=request.source,
            fingerprint=hashlib.sha256(raw_key).hexdigest(),
            imported_at=datetime.now(tz=timezone.utc),
            expires_at=request.expires_at,
            metadata=request.metadata,
        )
        encrypted_material = encrypt(
            raw_key,
            purpose="qkd-key-store",
            associated=request.key_id.encode("utf-8"),
        )
        self._qkd_keys[request.key_id] = _StoredQkdKey(
            encrypted_material=encrypted_material,
            metadata=metadata,
        )
        return metadata

    def list_qkd_keys(self) -> list[QkdKeyMetadata]:
        """Return non-secret metadata for every imported key."""
        return sorted(
            (entry.metadata for entry in self._qkd_keys.values()),
            key=lambda item: item.imported_at,
            reverse=True,
        )

    def create_hybrid_envelope(self, request: HybridEnvelopeIn) -> HybridEnvelopeOut:
        """Encrypt a payload using a hybrid classical/QKD-derived AES key."""
        qkd_key = self._load_qkd_key(request.qkd_key_id) if request.qkd_key_id else b""
        aead_key = self._derive_hybrid_key(
            purpose=request.purpose,
            pqc_kem=request.pqc_kem,
            qkd_material=qkd_key,
        )
        nonce = os.urandom(_NONCE_LEN)
        aad = request.associated_data.encode("utf-8") if request.associated_data else None
        ciphertext = AESGCM(aead_key).encrypt(nonce, request.plaintext.encode("utf-8"), aad)
        blob = nonce + ciphertext
        return HybridEnvelopeOut(
            ciphertext_b64=base64.b64encode(blob).decode("utf-8"),
            pqc_kem=request.pqc_kem,
            qkd_key_id=request.qkd_key_id,
            fingerprint=hashlib.sha256(blob).hexdigest(),
        )

    def decrypt_hybrid_envelope(
        self,
        ciphertext_b64: str,
        *,
        purpose: str,
        pqc_kem: PqcKemAlgorithm,
        qkd_key_id: str | None = None,
        associated_data: str | None = None,
    ) -> str:
        """Inverse helper used by focused tests to verify round-trips."""
        qkd_key = self._load_qkd_key(qkd_key_id) if qkd_key_id else b""
        aead_key = self._derive_hybrid_key(
            purpose=purpose,
            pqc_kem=pqc_kem,
            qkd_material=qkd_key,
        )
        blob = base64.b64decode(ciphertext_b64)
        nonce = blob[:_NONCE_LEN]
        ciphertext = blob[_NONCE_LEN:]
        aad = associated_data.encode("utf-8") if associated_data else None
        plaintext = AESGCM(aead_key).decrypt(nonce, ciphertext, aad)
        return plaintext.decode("utf-8")

    def clear(self) -> None:
        """Reset imported keys for tests."""
        self._qkd_keys.clear()

    def _load_qkd_key(self, key_id: str | None) -> bytes:
        """Load and decrypt one stored QKD key."""
        if key_id is None:
            return b""
        record = self._qkd_keys.get(key_id)
        if record is None:
            raise KeyError(f"Unknown QKD key '{key_id}'")
        return decrypt(
            record.encrypted_material,
            purpose="qkd-key-store",
            associated=key_id.encode("utf-8"),
        )

    def _derive_hybrid_key(
        self,
        *,
        purpose: str,
        pqc_kem: PqcKemAlgorithm,
        qkd_material: bytes,
    ) -> bytes:
        """Derive an AES-256 key from the master secret plus optional QKD entropy."""
        settings = get_settings()
        ikm = settings.secret_key.encode("utf-8") + qkd_material
        hkdf = HKDF(
            algorithm=hashes.SHA384(),
            length=_KEY_LEN,
            salt=None,
            info=f"smartcito-hybrid:{purpose}:{pqc_kem.value}".encode("utf-8"),
        )
        return hkdf.derive(ikm)


quantum_security_service = QuantumSecurityService()
