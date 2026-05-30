# POPIA Compliance Mapping

Mapping of the **Protection of Personal Information Act, 2013 (South Africa)**
conditions to Orca controls.

| POPIA Condition (s.8)       | Orca Control                                        |
|-----------------------------|----------------------------------------------------------|
| 1. Accountability           | Governance Council; ownership defined in `CODEOWNERS`    |
| 2. Processing limitation    | RBAC (`security/rbac/policies.yaml`); consent flags      |
| 3. Purpose specification    | Data Catalogue documents purpose per dataset             |
| 4. Further processing       | Purpose checks enforced in API + audit tags              |
| 5. Information quality      | Schema validation, integrity hashes on GPS streams       |
| 6. Openness                 | This repo + public Data Protection notice                |
| 7. Security safeguards      | Encryption everywhere (`security/crypto/STANDARDS.md`)   |
| 8. Data subject participation | `/api/v1/users/me/data` export + deletion endpoints    |

## Special Personal Information

Biometric data (faces, gait) is **special personal information** under
POPIA s.26. Processing requires:
- Documented lawful basis (s.27).
- Default-on redaction in `camera_module/`.
- Audit tag `compliance_tags: ["POPIA"]` on every event.

## Cross-Border Transfer (s.72)

Personal information may only leave South Africa to jurisdictions with
adequate protection or under contractual safeguards. Region routing is
enforced at the API gateway via the `subject.region_policy_satisfied`
RBAC rule.

## Breach Notification

Information Regulator notification required "as soon as reasonably
possible". See [`../incident_response/playbook.md`](../incident_response/playbook.md)
— playbook step **N-3** triggers POPIA notification.
