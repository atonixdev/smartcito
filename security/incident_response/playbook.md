# Incident Response Playbook

> **Goal:** detect, contain, and recover from security incidents while
> preserving evidence and meeting POPIA/GDPR/ISO 27001 obligations.

## Roles

| Role                | Responsibility                                       |
|---------------------|------------------------------------------------------|
| **Incident Commander (IC)** | Owns the incident end-to-end; coordinates response. |
| **Communications Lead**     | External + internal comms, regulator notifications. |
| **Tech Lead**               | Technical containment, eradication, recovery.       |
| **Scribe**                  | Maintains the incident timeline.                    |
| **Legal / DPO**             | Compliance, breach notification decisions.          |

## Severity

| Sev | Definition                                                          | Page? |
|-----|---------------------------------------------------------------------|-------|
| S1  | Confirmed breach of personal data, key compromise, or prod outage   | Yes — immediate |
| S2  | Suspected breach, unauthorised access without confirmed exfiltration| Yes |
| S3  | Policy violation, single-user account compromise, contained         | Business hours |
| S4  | Near-miss, vulnerability disclosure pending fix                     | No   |

## Phases

### 1. Detect
Triggers:
- IDS / anomaly alert.
- Audit log anomaly.
- External report via [SECURITY.md](../../SECURITY.md) channel.
- Failed compliance check in CI on `main`.

### 2. Triage (≤ 15 min for S1/S2)
- Assign IC.
- Open private incident channel + tracking issue (`security-incident`
  label, restricted visibility).
- Set initial severity.

### 3. Contain
- Revoke compromised credentials / rotate keys
  ([`../crypto/STANDARDS.md`](../crypto/STANDARDS.md)).
- Disable affected accounts; force re-auth + MFA.
- Network: isolate affected workloads via NetworkPolicy.
- Snapshot disks / memory for forensics **before** termination.

### 4. Eradicate
- Patch the vulnerability; deploy via standard CI/CD (no `--no-verify`).
- Invalidate all sessions issued during the exposure window.
- Re-key any data that may have been exposed.

### 5. Recover
- Restore service from known-good state.
- Monitor for 72 h with elevated alerting.
- Close incident only after IC + Tech Lead sign-off.

### 6. Notify
- **N-1:** Internal Governance Council — within 1 h of S1/S2 confirmation.
- **N-2 (GDPR):** EU supervisory authority — **within 72 h** for personal
  data breaches. See [`../compliance/gdpr.md`](../compliance/gdpr.md).
- **N-3 (POPIA):** SA Information Regulator — as soon as reasonably
  possible. See [`../compliance/popia.md`](../compliance/popia.md).
- **N-4:** Data subjects — without undue delay if high risk.
- **N-5:** Public disclosure via the Security Advisories channel after
  fix is deployed.

### 7. Post-incident review (≤ 10 business days)
- Blameless post-mortem published to `docs/incidents/`.
- Action items tracked as issues with owners + due dates.
- Update this playbook with lessons learned.

## Evidence Handling

- Preserve audit logs covering at least the 30 days surrounding the
  incident. Audit storage is append-only and signed — see
  [`../audit/audit_log_schema.json`](../audit/audit_log_schema.json).
- Chain-of-custody log maintained by the Scribe.
- Never share evidence containing personal data outside the IR team
  without Legal/DPO approval.

## Tabletop Exercises

- Annual full-scale exercise covering an S1 scenario.
- Quarterly mini-exercises (key compromise, ransomware, insider misuse).
- Attendance is mandatory for anyone with `operator` or higher in prod.
