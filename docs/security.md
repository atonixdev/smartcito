# Secure Coding Checklist for Contributors

This is the day-to-day checklist contributors must follow before opening
or merging a pull request.

Related references:
- [../security/SECURITY_POSTURE.md](../security/SECURITY_POSTURE.md)
- [../security/hardening/secure_coding.md](../security/hardening/secure_coding.md)
- [../security/rbac/policies.yaml](../security/rbac/policies.yaml)
- [../security/incident_response/playbook.md](../security/incident_response/playbook.md)

## Baseline

- [ ] I read [../security/SECURITY_POSTURE.md](../security/SECURITY_POSTURE.md).
- [ ] My change follows Zero Trust: no internal endpoint or service call is trusted by default.
- [ ] I did not commit secrets, credentials, tokens, private keys, or sample real data.
- [ ] I used approved crypto only from [../security/crypto/STANDARDS.md](../security/crypto/STANDARDS.md).

## If I Added or Changed an API

- [ ] Endpoint requires authentication unless explicitly public and documented.
- [ ] RBAC permission is defined or reused in [../security/rbac/policies.yaml](../security/rbac/policies.yaml).
- [ ] State-changing calls emit an audit event using the schema in [../security/audit/audit_log_schema.json](../security/audit/audit_log_schema.json).
- [ ] Inputs are validated and the endpoint is rate-limited.
- [ ] I added tests for authorised and unauthorised paths.

## If I Touched Personal Data, Camera Feeds, or GPS

- [ ] I minimised stored data and avoided retaining raw video unless explicitly approved.
- [ ] Data in transit uses TLS; sensitive data at rest uses AES-256.
- [ ] I updated compliance mapping if POPIA, GDPR, or ISO 27001 controls changed.
- [ ] I considered subject rights, retention, and cross-border transfer requirements.

## CI and Review

- [ ] `citosmart`: lint/tests pass locally where applicable.
- [ ] `webapp`: lint/tests/build pass locally where applicable.
- [ ] Security workflow passes in CI.
- [ ] PR description includes threat model notes for new data flows or privileged operations.

## Escalation

If you find a vulnerability, do **not** open a public issue. Follow
[../SECURITY.md](../SECURITY.md).
