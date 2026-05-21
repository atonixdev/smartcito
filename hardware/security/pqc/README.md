# Post-Quantum Cryptography Hardware Controls

Reference material for integrating NIST-standardized post-quantum cryptography
into SmartCito deployments.

## Priority Algorithms

- lattice-based KEMs and signatures where standardized and supported
- hash-based signatures for long-lived integrity artifacts
- hybrid classical + PQC key exchange during migration periods

## Deployment Guidance

- start with hybrid TLS and hybrid key establishment where libraries support it
- keep AES-256 for symmetric encryption while upgrading asymmetric primitives
- store PQC private material in HSM-backed or equivalent hardened key stores

## SmartCito Mapping

See [`../../../security/pqc/README.md`](../../../security/pqc/README.md) for the
software control layer.
