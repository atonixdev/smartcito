<!--
================================================================================
 File: SECURITY.md
 Purpose:
   Coordinated vulnerability disclosure policy for Orca.
================================================================================
-->

# Security Policy

Orca powers critical urban infrastructure. We take security extremely
seriously and welcome responsible disclosure from researchers and users.

## Supported Versions

| Version  | Supported          |
|----------|--------------------|
| `main`   | ✅ (active development) |
| `0.x`    | ✅ security fixes only  |
| `< 0.1`  | ❌ no longer supported  |

## Reporting a Vulnerability

**Please do _not_ open a public GitHub issue for security problems.**

Instead, email: **security@orca.dev**

Include:

1. A description of the vulnerability and its impact.
2. Steps to reproduce (PoC, request/response, logs).
3. Affected commit / version.
4. Your name and affiliation (for credit, if you wish).

We will acknowledge your report within **3 business days** and provide an
initial assessment within **10 business days**. Critical issues are typically
patched and disclosed within **90 days**.

## Hardening Guidelines

- Always run Orca behind TLS (terminate at a reverse proxy or load balancer).
- Rotate JWT signing keys regularly; never commit them.
- Use least-privilege RBAC roles for city-department users.
- Enable audit logging in production (`AUDIT_LOG_ENABLED=true`).
- Keep dependencies up to date; we publish weekly Dependabot PRs.

## Frameworks We Align With

- ISO/IEC 27001
- NIST Cybersecurity Framework (CSF)
- OWASP Top 10 (2021)
- OWASP API Security Top 10 (2023)
- GDPR & POPIA data-protection principles
