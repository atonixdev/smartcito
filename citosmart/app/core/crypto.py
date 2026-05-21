"""
================================================================================
 File: backend/app/core/crypto.py
 Purpose:
   Symmetric (AES-256-GCM) helpers built on the `cryptography` library.
   Used to encrypt sensitive fields at rest (e.g. device secrets, audit
   payloads) without depending on database-level encryption.

 Why AES-256-GCM?
   - Authenticated encryption: integrity AND confidentiality in one primitive.
   - Wide hardware acceleration (AES-NI on x86, ARMv8 crypto extensions).
   - NIST-approved (SP 800-38D).

 Key management:
   - Keys are 32 bytes (256 bit). Derive from `Settings.secret_key` via
     HKDF-SHA256 with a domain-separation `info` string so the same master
     key can yield distinct subkeys per purpose.
   - In production, replace `derive_key()` with a call to a KMS (AWS KMS,
     GCP KMS, HashiCorp Vault Transit).

 Example:
     from app.core.crypto import encrypt, decrypt
     ct = encrypt(b"super secret", purpose="audit-log")
     pt = decrypt(ct, purpose="audit-log")
================================================================================
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.core.config import get_settings

# AES-GCM recommended nonce length: 96 bits (12 bytes).
_NONCE_LEN = 12
_KEY_LEN = 32  # 256-bit


@dataclass(frozen=True)
class Ciphertext:
    """Container for an AES-GCM ciphertext + nonce.

    The wire format is `nonce || ciphertext_with_tag`. AES-GCM appends a
    16-byte authentication tag to the ciphertext automatically.
    """

    nonce: bytes
    ciphertext: bytes

    def to_bytes(self) -> bytes:
        """Serialize for storage as a single opaque blob."""
        return self.nonce + self.ciphertext

    @classmethod
    def from_bytes(cls, blob: bytes) -> "Ciphertext":
        if len(blob) <= _NONCE_LEN:
            raise ValueError("blob too short to contain nonce + ciphertext")
        return cls(nonce=blob[:_NONCE_LEN], ciphertext=blob[_NONCE_LEN:])


def derive_key(purpose: str) -> bytes:
    """Derive a 256-bit key from the configured master secret.

    Args:
        purpose: A short, stable string scoping the derived key
                 (e.g. "audit-log", "device-secret").

    Returns:
        32-byte key suitable for AES-256-GCM.
    """
    settings = get_settings()
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=_KEY_LEN,
        salt=None,  # Salt is optional; we rely on the high-entropy master.
        info=purpose.encode("utf-8"),
    )
    return hkdf.derive(settings.secret_key.encode("utf-8"))


def encrypt(plaintext: bytes, *, purpose: str, associated: bytes | None = None) -> bytes:
    """Encrypt with AES-256-GCM.

    Args:
        plaintext: Bytes to encrypt.
        purpose: Domain-separation tag (passed to `derive_key`).
        associated: Optional Additional Authenticated Data — bound to the
                    ciphertext but not encrypted (e.g. a record id).

    Returns:
        Opaque blob suitable for storage. Use `decrypt` with the same
        `purpose` and `associated` to recover the plaintext.
    """
    key = derive_key(purpose)
    nonce = os.urandom(_NONCE_LEN)
    aead = AESGCM(key)
    ct = aead.encrypt(nonce, plaintext, associated)
    return Ciphertext(nonce=nonce, ciphertext=ct).to_bytes()


def decrypt(blob: bytes, *, purpose: str, associated: bytes | None = None) -> bytes:
    """Inverse of :func:`encrypt`. Raises on tamper or wrong purpose."""
    key = derive_key(purpose)
    parsed = Ciphertext.from_bytes(blob)
    aead = AESGCM(key)
    return aead.decrypt(parsed.nonce, parsed.ciphertext, associated)
