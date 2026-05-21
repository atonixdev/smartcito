# GDPR Compliance Mapping

Mapping of **Regulation (EU) 2016/679 (GDPR)** principles and articles
to SmartCito controls.

## Article 5 Principles

| Principle                       | SmartCito Control                                    |
|---------------------------------|------------------------------------------------------|
| Lawfulness, fairness, transparency | Public privacy notice; consent records          |
| Purpose limitation              | Purpose tag per dataset; enforced via RBAC           |
| Data minimisation               | Metadata-only persistence for camera feeds           |
| Accuracy                        | Schema + integrity validation                        |
| Storage limitation              | Retention policy per dataset; automated TTL          |
| Integrity & confidentiality     | Encryption everywhere (`../crypto/STANDARDS.md`)     |
| Accountability                  | Audit log (`../audit/audit_log_schema.json`)         |

## Data Subject Rights (Articles 15–22)

| Right                | Endpoint / Mechanism                            |
|----------------------|-------------------------------------------------|
| Access (Art. 15)     | `GET  /api/v1/users/me/data`                    |
| Rectification (16)   | `PATCH /api/v1/users/me`                        |
| Erasure (17)         | `DELETE /api/v1/users/me/data`                  |
| Restriction (18)     | `POST /api/v1/users/me/processing/restrict`     |
| Portability (20)     | `GET  /api/v1/users/me/data?format=json`        |
| Object (21)          | `POST /api/v1/users/me/processing/object`       |
| Automated decisions (22) | AI models flagged; human review required    |

## Cross-Border Transfers (Chapter V)

Transfers outside the EEA use Standard Contractual Clauses (SCCs)
and Transfer Impact Assessments. Region routing is enforced at the
API gateway.

## Breach Notification (Articles 33–34)

- Notify the supervisory authority **within 72 hours**.
- Notify affected data subjects without undue delay if high risk.
- Playbook: [`../incident_response/playbook.md`](../incident_response/playbook.md)
  — step **N-2** triggers GDPR notification.

## DPIA

A Data Protection Impact Assessment is required before any new module
that processes biometrics, location at individual level, or large-scale
monitoring of public spaces.
