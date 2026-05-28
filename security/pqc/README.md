# Post-Quantum Cryptography

Orca's post-quantum cryptography migration guidance.

## Strategy

- retain TLS and AES-256 now
- migrate asymmetric primitives toward NIST-standardized PQC algorithms as
  production libraries mature
- prefer hybrid classical + PQC exchange during transition periods
- keep cryptographic choices centralized so migration does not fork by service

## Current Expectations

- AES-256 remains the symmetric baseline
- JWT and service identity should move to PQ-safe signing only after mature,
  interoperable libraries are available
- certificate and TLS termination paths should be designed for hybrid support

## Governance

Changes to PQC choices require security review, compatibility testing, and
updated compliance mappings.
