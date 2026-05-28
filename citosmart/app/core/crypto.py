"""Shared backend crypto façade over the repository-wide crypto helpers."""

from orca_shared.crypto import (
    Ciphertext,
    build_integrity_record,
    build_secure_envelope,
    decrypt,
    decrypt_secure_envelope,
    derive_key,
    encrypt,
    generate_certificate_authority,
    issue_device_certificate,
    public_key_pem,
    sha256_hex,
    sha3_256_hex,
    sign_payload,
    verify_integrity_record,
    verify_payload_signature,
)

__all__ = [
    "Ciphertext",
    "build_integrity_record",
    "build_secure_envelope",
    "decrypt",
    "decrypt_secure_envelope",
    "derive_key",
    "encrypt",
    "generate_certificate_authority",
    "issue_device_certificate",
    "public_key_pem",
    "sha256_hex",
    "sha3_256_hex",
    "sign_payload",
    "verify_integrity_record",
    "verify_payload_signature",
]
