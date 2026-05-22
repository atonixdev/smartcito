<!--
================================================================================
 File: docs/SECURITY_DEEP_DIVE.md
 Purpose: Detailed security playbook beyond the SECURITY.md disclosure policy.
================================================================================
-->

# SmartCito Security Deep Dive

> Cities are critical infrastructure. SmartCito is built with that in mind.

## Threat Model (summary)

| Threat                                  | Mitigation                            |
|-----------------------------------------|---------------------------------------|
| Eavesdropping on device → server traffic | TLS 1.2+; mTLS for high-trust links  |
| Compromised IoT device                  | Per-device credentials; revocation list|
| Credential stuffing on API              | Rate limits; account lockout; MFA (planned) |
| Token theft                             | Short-lived JWTs; rotate signing keys |
| Insider data exfiltration               | RBAC; audit logs; immutable log store |
| Supply-chain attack                     | Pinned deps; Dependabot; SBOM         |
| DoS on ingestion                        | Kafka backpressure; quota per device  |

## Controls Map

### OWASP API Security Top 10 (2023)

| Risk | SmartCito Control                                |
|------|--------------------------------------------------|
| API1 — BOLA            | Resource-scoped RBAC, never trust client IDs |
| API2 — Broken AuthN    | OAuth2 + JWT, optional OIDC                  |
| API3 — Object property | Strict Pydantic schemas with `extra="forbid"`|
| API4 — Resource consumption | Rate limits + Kafka backpressure        |
| API5 — Function-level auth  | `require_role()` dependency on every write|
| API6 — Sensitive flows | Audit log of all mutations                   |
| API7 — SSRF            | Outbound HTTP requires allow-list (planned)  |
| API8 — Misconfiguration | Container runs as non-root, no shell        |
| API9 — Inventory       | OpenAPI is the inventory; versioned at /v1   |
| API10 — Unsafe consumption | All inbound JSON validated by Pydantic   |

## Cryptography

- TLS: terminate at a hardened reverse proxy (nginx, Envoy, or a managed LB).
- Token signing: HS256 in dev; switch to RS256 + KMS-managed keys in prod.
- At-rest: rely on disk encryption (LUKS, EBS, GCP CMEK) for databases.

## Compliance

- **GDPR**: right of access, right to erasure, data-processing register.
- **POPIA**: consent records, breach notification within 72h.
- **ISO/IEC 27001**: SmartCito does not certify, but maps controls to A.5–A.18.

## Operational Practices

- Weekly dependency updates via Dependabot.
- Signed container images (cosign) — planned.
- Immutable audit log shipped to a separate account / project.
- Quarterly tabletop exercises for breach response.
