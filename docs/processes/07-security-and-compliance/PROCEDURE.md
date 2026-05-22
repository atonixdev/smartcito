<!--
================================================================================
 File: docs/processes/07-security-and-compliance/PROCEDURE.md
 Purpose:
   Security review and compliance evidence procedure for SmartCito.
================================================================================
-->

# Security And Compliance Procedure

## Purpose

Ensure security-sensitive work is reviewed, validated, and documented with clear
evidence.

## Scope

This procedure applies to authentication, authorization, encryption, secrets,
networking, audit logs, compliance records, incident controls, and third-party
dependency changes.

## Procedure

1. Identify whether the change affects identity, permissions, data protection,
   auditability, infrastructure exposure, or dependency risk.
2. Review the applicable security documentation and existing control patterns.
3. Confirm least-privilege access for new credentials, roles, services, or
   operators.
4. Keep secrets out of source control and local screenshots.
5. Add tests or manual evidence for security-sensitive behavior.
6. Run dependency, configuration, or code checks required by the change type.
7. Document residual risk and required monitoring.
8. Request security review before merging high-risk changes.

## Validation Checklist

- Security impact is documented.
- Secrets are not committed.
- Auth, RBAC, encryption, and audit behavior are tested when touched.
- Required compliance evidence is attached to the work item or pull request.
- Security owner has reviewed high-risk changes.

## Related Documentation

- [../../SECURITY_DEEP_DIVE.md](../../SECURITY_DEEP_DIVE.md)
- [../../security.md](../../security.md)
- [../../../SECURITY.md](../../../SECURITY.md)
- [../../../security/README.md](../../../security/README.md)
