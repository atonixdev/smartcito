# Security

Encryption, IAM, RBAC, and audit logging for Orca.

For the full design, see [`../docs/SECURITY_DEEP_DIVE.md`](../docs/SECURITY_DEEP_DIVE.md)
and [`../SECURITY.md`](../SECURITY.md).

Primary operating documents:
- [`SECURITY_POSTURE.md`](SECURITY_POSTURE.md)
- [`iam/oauth2.md`](iam/oauth2.md)
- [`rbac/policies.yaml`](rbac/policies.yaml)
- [`crypto/STANDARDS.md`](crypto/STANDARDS.md)
- [`audit/audit_log_schema.json`](audit/audit_log_schema.json)
- [`incident_response/playbook.md`](incident_response/playbook.md)
- [`hardening/secure_coding.md`](hardening/secure_coding.md)
- [`hardening/containers.md`](hardening/containers.md)

## Container Image

- Build file: `security/Dockerfile`
- What the image does: runs the FastAPI security-domain API on port `8013` with `uvicorn security.service:app`.
- What ships in the image: the `orcaapi/` runtime dependencies, the `security/` package, and this README at `/app/security/README.md`.

## Layout

```
security/
├── Dockerfile       # Container image for security-domain API
├── requirements.txt # Runtime dependencies
├── service.py       # FastAPI encryption/IAM helper service
├── iam/             # Identity providers, OIDC/SAML integrations
├── rbac/            # Role and permission definitions, policy engine
├── crypto/          # Key management, envelope encryption helpers
├── audit/           # Audit log sinks, tamper-evident storage
└── README.md
```

## Baseline Requirements

| Control                | Requirement                                       |
|------------------------|---------------------------------------------------|
| Transport encryption   | **TLS 1.2+** on every API and broker             |
| Data at rest           | **AES-256** for databases, object storage, backups|
| Authentication         | OIDC / JWT with short-lived tokens               |
| Authorization          | RBAC enforced at the API gateway and service     |
| Audit logging          | Append-only, signed, exported off-host            |
| Intrusion detection    | Anomaly detection on auth + API access patterns   |

## Checklist for New APIs

- [ ] TLS enforced, HSTS configured
- [ ] AuthN: OIDC / JWT validated
- [ ] AuthZ: RBAC policy added in `security/rbac/`
- [ ] Input validated and rate-limited
- [ ] Audit log emitted for every state-changing call
- [ ] Secrets loaded from env / secret manager, never committed
- [ ] Threat model reviewed in PR description

## Technologies Used

- Python 3.11
- FastAPI
- cryptography
- JWT / RBAC policy artifacts

## How To Run Its Container

```bash
docker build -f security/Dockerfile -t orca-security-domain .
docker run --rm -p 8013:8013 --env-file .env orca-security-domain
```

## Example Usage

```bash
curl -X POST http://localhost:8013/encrypt \
	-H 'Content-Type: application/json' \
	-d '{"plaintext":"hello","purpose":"demo"}'
```
