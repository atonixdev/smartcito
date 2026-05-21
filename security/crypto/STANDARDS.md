# Cryptography Standards

## Algorithms

| Use case                  | Algorithm                              |
|---------------------------|----------------------------------------|
| Symmetric encryption      | **AES-256-GCM** (preferred) / AES-256-CTR + HMAC-SHA256 |
| Asymmetric encryption     | RSA-OAEP-3072 or X25519 (ECIES)        |
| Digital signatures        | Ed25519 (preferred) or ECDSA P-256     |
| Password hashing          | bcrypt (cost ≥ 12) or Argon2id         |
| MAC / integrity           | HMAC-SHA-256                           |
| Random                    | OS CSPRNG (`os.urandom` / `secrets`)   |
| TLS                       | TLS 1.2+ (TLS 1.3 preferred), modern ciphers only |

**Forbidden:** MD5, SHA-1, DES/3DES, RC4, ECB mode, static IVs, custom
crypto, hand-rolled key derivation.

## Key Management

- All data-encryption keys are wrapped by a KMS-managed master key
  (envelope encryption).
- Rotate **DEKs** every 90 days; **KEKs** annually.
- Keys never appear in source, logs, error messages, or tickets.
- Access to key material is restricted to the `system:admin` permission
  and audited.

## End-to-End Encryption for Streams

### Camera feeds
- Producer (camera/edge) encrypts frames with AES-256-GCM using a
  session key established via X25519 + HKDF.
- Session keys rotate every 5 minutes or 1 GiB, whichever comes first.
- Manifests are signed with Ed25519; consumers verify before decode.

### GPS streams
- Every message carries an HMAC-SHA-256 tag over `(payload || timestamp
  || monotonic_seq)` keyed with a per-device key.
- Replay protection: consumers reject messages with a non-monotonic
  sequence or a timestamp skew > 30 s.

## Library Choices

| Language | Use                                                |
|----------|----------------------------------------------------|
| Python   | `cryptography`, `passlib[bcrypt]`, `PyJWT`         |
| TS/JS    | Web Crypto API; `jose` for JWT                     |
| C        | libsodium                                          |

Do **not** introduce a new crypto library without Governance Council
approval.
