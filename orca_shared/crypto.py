from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.x509.oid import NameOID

_NONCE_LEN = 12
_KEY_LEN = 32
_EPHEMERAL_SIGNING_KEY = ec.generate_private_key(ec.SECP521R1())


@dataclass(frozen=True)
class Ciphertext:
    nonce: bytes
    ciphertext: bytes

    def to_bytes(self) -> bytes:
        return self.nonce + self.ciphertext

    @classmethod
    def from_bytes(cls, blob: bytes) -> "Ciphertext":
        if len(blob) <= _NONCE_LEN:
            raise ValueError("blob too short to contain nonce + ciphertext")
        return cls(nonce=blob[:_NONCE_LEN], ciphertext=blob[_NONCE_LEN:])


def _master_secret() -> str:
    return (
        os.getenv("ORCA_MASTER_KEY")
        or os.getenv("AUTH_JWT_SECRET")
        or os.getenv("SECRET_KEY")
        or "dev-only-change-me"
    )


def _load_signing_key(private_key_pem: str | None = None) -> ec.EllipticCurvePrivateKey:
    pem = private_key_pem or os.getenv("ORCA_SIGNING_PRIVATE_KEY_PEM")
    if pem:
        return serialization.load_pem_private_key(pem.encode("utf-8"), password=None)
    return _EPHEMERAL_SIGNING_KEY


def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def sha256_hex(payload: Any) -> str:
    digest = hashes.Hash(hashes.SHA256())
    digest.update(canonical_json_bytes(payload))
    return digest.finalize().hex()


def sha3_256_hex(payload: Any) -> str:
    digest = hashes.Hash(hashes.SHA3_256())
    digest.update(canonical_json_bytes(payload))
    return digest.finalize().hex()


def derive_key(purpose: str, *, master_secret: str | None = None) -> bytes:
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=_KEY_LEN,
        salt=None,
        info=purpose.encode("utf-8"),
    )
    return hkdf.derive((master_secret or _master_secret()).encode("utf-8"))


def encrypt(plaintext: bytes, *, purpose: str, associated: bytes | None = None) -> bytes:
    nonce = os.urandom(_NONCE_LEN)
    ciphertext = AESGCM(derive_key(purpose)).encrypt(nonce, plaintext, associated)
    return Ciphertext(nonce=nonce, ciphertext=ciphertext).to_bytes()


def decrypt(blob: bytes, *, purpose: str, associated: bytes | None = None) -> bytes:
    parsed = Ciphertext.from_bytes(blob)
    return AESGCM(derive_key(purpose)).decrypt(parsed.nonce, parsed.ciphertext, associated)


def public_key_pem(private_key_pem: str | None = None) -> str:
    key = _load_signing_key(private_key_pem)
    return key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")


def sign_payload(payload: Any, *, private_key_pem: str | None = None) -> str:
    signature = _load_signing_key(private_key_pem).sign(
        canonical_json_bytes(payload),
        ec.ECDSA(hashes.SHA256()),
    )
    return base64.b64encode(signature).decode("ascii")


def verify_payload_signature(payload: Any, signature_b64: str, public_key_pem_text: str) -> bool:
    public_key = serialization.load_pem_public_key(public_key_pem_text.encode("utf-8"))
    try:
        public_key.verify(
            base64.b64decode(signature_b64.encode("ascii")),
            canonical_json_bytes(payload),
            ec.ECDSA(hashes.SHA256()),
        )
    except Exception:
        return False
    return True


def build_integrity_record(payload: Any, *, signer_id: str, private_key_pem: str | None = None) -> dict[str, Any]:
    public_pem = public_key_pem(private_key_pem)
    signature = sign_payload(payload, private_key_pem=private_key_pem)
    return {
        "signer_id": signer_id,
        "signed_at": datetime.now(UTC).isoformat(),
        "hash": {
            "sha256": sha256_hex(payload),
            "sha3_256": sha3_256_hex(payload),
        },
        "signature": {
            "algorithm": "ECDSA-P521-SHA256",
            "value": signature,
            "public_key_pem": public_pem,
        },
    }


def verify_integrity_record(payload: Any, record: dict[str, Any]) -> bool:
    hash_record = record.get("hash", {})
    signature_record = record.get("signature", {})
    if hash_record.get("sha256") != sha256_hex(payload):
        return False
    public_pem = signature_record.get("public_key_pem")
    signature = signature_record.get("value")
    if not isinstance(public_pem, str) or not isinstance(signature, str):
        return False
    return verify_payload_signature(payload, signature, public_pem)


def build_secure_envelope(
    payload: Any,
    *,
    purpose: str,
    signer_id: str,
    associated: str | None = None,
    private_key_pem: str | None = None,
) -> dict[str, Any]:
    plaintext = canonical_json_bytes(payload)
    associated_bytes = associated.encode("utf-8") if associated else None
    blob = encrypt(plaintext, purpose=purpose, associated=associated_bytes)
    parsed = Ciphertext.from_bytes(blob)
    return {
        "algorithm": "AES-256-GCM",
        "purpose": purpose,
        "nonce_b64": base64.b64encode(parsed.nonce).decode("ascii"),
        "ciphertext_b64": base64.b64encode(parsed.ciphertext).decode("ascii"),
        "integrity": build_integrity_record(payload, signer_id=signer_id, private_key_pem=private_key_pem),
    }


def decrypt_secure_envelope(
    envelope: dict[str, Any],
    *,
    associated: str | None = None,
) -> Any:
    blob = base64.b64decode(envelope["nonce_b64"]) + base64.b64decode(envelope["ciphertext_b64"])
    plaintext = decrypt(blob, purpose=str(envelope["purpose"]), associated=associated.encode("utf-8") if associated else None)
    return json.loads(plaintext.decode("utf-8"))


def generate_certificate_authority(common_name: str, *, validity_days: int = 3650) -> dict[str, str]:
    private_key = ec.generate_private_key(ec.SECP521R1())
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    now = datetime.now(UTC)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=validity_days))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(private_key, hashes.SHA256())
    )
    return {
        "private_key_pem": private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8"),
        "certificate_pem": certificate.public_bytes(serialization.Encoding.PEM).decode("utf-8"),
        "fingerprint_sha256": certificate.fingerprint(hashes.SHA256()).hex(),
    }


def issue_device_certificate(
    common_name: str,
    *,
    ca_certificate_pem: str,
    ca_private_key_pem: str,
    validity_days: int = 365,
) -> dict[str, str]:
    ca_cert = x509.load_pem_x509_certificate(ca_certificate_pem.encode("utf-8"))
    ca_private_key = serialization.load_pem_private_key(ca_private_key_pem.encode("utf-8"), password=None)
    device_private_key = ec.generate_private_key(ec.SECP521R1())
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    now = datetime.now(UTC)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(device_private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=validity_days))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .sign(ca_private_key, hashes.SHA256())
    )
    return {
        "private_key_pem": device_private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8"),
        "certificate_pem": certificate.public_bytes(serialization.Encoding.PEM).decode("utf-8"),
        "ca_fingerprint_sha256": ca_cert.fingerprint(hashes.SHA256()).hex(),
        "fingerprint_sha256": certificate.fingerprint(hashes.SHA256()).hex(),
    }