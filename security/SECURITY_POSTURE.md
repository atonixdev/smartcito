# SmartCito Security Posture

> **Pillars:** Zero Trust • Encryption Everywhere • Strict IAM + RBAC •
> Audit, Compliance & Intrusion Detection • Hardening & Secure Coding.

This document is the authoritative description of SmartCito's security
posture. Every contributor is expected to read it before submitting code
that touches authentication, data, networking, or infrastructure.

Related material:
- [SECURITY.md](../SECURITY.md) — vulnerability disclosure policy
- [docs/SECURITY_DEEP_DIVE.md](../docs/SECURITY_DEEP_DIVE.md) — architecture
- [docs/security.md](../docs/security.md) — contributor checklist
- [security/rbac/policies.yaml](rbac/policies.yaml) — role/permission matrix
- [security/audit/audit_log_schema.json](audit/audit_log_schema.json)
- [security/pqc/](pqc/) — post-quantum migration guidance
- [security/qkd/](qkd/) — QKD integration guidance
- [security/compliance/](compliance/) — POPIA / GDPR / ISO 27001 mappings
- [security/incident_response/playbook.md](incident_response/playbook.md)

---

## 1. Zero Trust Architecture

- **No implicit trust.** Every request — internal or external — is
  authenticated and authorized at the service boundary.
- **Service identity.** Internal calls use mTLS or signed service tokens
  (SPIFFE/SPIRE-compatible). The network is **not** a trust boundary.
- **Short-lived credentials.** Access tokens expire in minutes; refresh
  tokens are rotated and revocable.
- **Default deny.** All RBAC policies start from `deny` and grant
  explicitly.

## 2. Encryption Everywhere

| Surface                       | Standard                                  |
|-------------------------------|-------------------------------------------|
| API traffic (public/internal) | **TLS 1.2+** (TLS 1.3 preferred), HSTS    |
| Kafka / MQTT                  | TLS + mutual auth                         |
| Database at rest              | **AES-256** (engine-native + disk-level)  |
| Object storage                | SSE-KMS with customer-managed keys        |
| Backups                       | AES-256, separate key, off-site           |
| Camera feeds                  | **End-to-end TLS**, signed manifests      |
| GPS streams                   | TLS + HMAC integrity tag per message      |
| Secrets                       | Vault / cloud secret manager — never repo |

Key management is centralised. Keys rotate at least every 90 days for
data-encryption keys and annually for master keys.

### Quantum-Ready Direction

- Begin migration planning with NIST-standardized post-quantum algorithms.
- Prefer hybrid classical + PQC key exchange during the transition period.
- Design key-management APIs so QKD-derived keys can enter the approved KMS/HSM
  pipeline without changing service contracts.

## 3. Identity & Access Management

- **RBAC** with the role matrix defined in
  [rbac/policies.yaml](rbac/policies.yaml). Roles today: `viewer`,
  `operator`, `admin`. Add a new role only via PR + Governance Council
  review.
- **MFA required** for `operator` and `admin` roles, and for every
  contributor with merge rights on `main`.
- **OIDC / OAuth2** for human auth; **JWT** (short TTL) for service auth.
  Configuration in [iam/oauth2.md](iam/oauth2.md).
- **Fine-grained permissions.** Permissions are verb-on-resource
  (e.g. `sensors:read`, `cameras:stream`, `audit:export`).
- **Just-in-time access** for `admin` actions on production via a
  break-glass workflow with full audit trail.

## 4. Audit & Compliance

- **Full logging** of every state-changing API call and every data export.
  Schema: [audit/audit_log_schema.json](audit/audit_log_schema.json).
- **Tamper-evident storage.** Audit logs are append-only and signed in
  batches (hash-chained); shipped off-host within 60 seconds.
- **Quantum-ready signing roadmap.** Audit chains should be prepared for PQC
  signatures as mature libraries become operationally viable.
- **Compliance mappings:**
  - [POPIA](compliance/popia.md)
  - [GDPR](compliance/gdpr.md)
  - [ISO 27001](compliance/iso27001.md)
- **Automated compliance checks** run in CI
  ([.github/workflows/security.yml](../.github/workflows/security.yml))
  and block merge on failure.

## 5. Intrusion Detection & Response

- **AI-powered anomaly detection** on auth events and API access patterns
  (see [`../ai_models/analytics/`](../ai_models/)).
- **Alerts** on impossible-travel sign-ins, brute-force, privilege
  escalation, and unusual data exfiltration volumes.
- **Incident response** follows
  [incident_response/playbook.md](incident_response/playbook.md). Every
  contributor and city operator with elevated access must complete the
  IR tabletop annually.

## 6. Hardening & Control

- **Secure coding standards** enforced in
  [hardening/secure_coding.md](hardening/secure_coding.md).
- **Static analysis + SCA** in CI: Bandit (Python), ESLint security
  plugin (TS), `pip-audit`, `npm audit`, Trivy (containers), Gitleaks
  (secrets), Semgrep (custom rules).
- **Penetration testing** quarterly against staging; results tracked in
  the Governance Council.
- **Container hardening** per
  [hardening/containers.md](hardening/containers.md): non-root users,
  read-only root FS, dropped capabilities, distroless images, signed
  with cosign, scanned with Trivy, deployed with PodSecurity `restricted`.

---

## Developer Folder Security Controls

| Folder                            | Responsibility                              |
|-----------------------------------|---------------------------------------------|
| [`security/`](.)                  | Encryption libs, IAM configs, RBAC policies |
| [`security/iam/`](iam/)           | OAuth2, OIDC, JWT, MFA configuration        |
| [`security/rbac/`](rbac/)         | Role + permission matrix                    |
| [`security/crypto/`](crypto/)     | Encryption standards + key management       |
| [`security/pqc/`](pqc/)           | Post-quantum cryptography migration         |
| [`security/qkd/`](qkd/)           | QKD integration policy                      |
| [`security/audit/`](audit/)       | Audit log schema + sinks                    |
| [`security/compliance/`](compliance/) | POPIA, GDPR, ISO 27001 mappings         |
| [`security/incident_response/`](incident_response/) | IR playbook        |
| [`security/hardening/`](hardening/) | Secure coding + container hardening       |
| [`tests/security/`](../tests/security/) | Pentest, fuzzing, security validation  |
| [`docs/security.md`](../docs/security.md) | Contributor checklist                |
| [`citosmart/app/core/security.py`](../citosmart/app/core/security.py) | JWT + RBAC primitives |
| [`camera_module/`](../camera_module/) | Secure video ingestion with TLS         |
| [`gps_module/`](../gps_module/)   | GPS integrity checks + encryption           |

## Operational Safeguards

- **Continuous monitoring** dashboards: system health, IDS, compliance.
- **Resilience.** Multi-AZ deployment; no single point of failure for
  ingestion, auth, or audit.
- **Contributor security training** is a prerequisite for merge rights.
- **Governance Council** approves changes to this posture, RBAC roles,
  cryptographic standards, and incident classifications.

## Change Control

Changes to anything in `security/` require:
1. PR approval from a Governance Council member listed in
   [`../.github/CODEOWNERS`](../.github/CODEOWNERS).
2. Passing security CI workflow.
3. Updated compliance mapping if the change affects a control.
