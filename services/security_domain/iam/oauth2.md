# IAM — Identity & Access Management

Orca uses **OIDC / OAuth2** for human authentication and **JWT** for
service-to-service authentication.

## Standards

| Concern              | Choice                                              |
|----------------------|-----------------------------------------------------|
| Human auth           | OIDC (Authorization Code + PKCE)                    |
| Service auth         | OAuth2 client credentials → short-lived JWT         |
| Token signing        | RS256 in production; HS256 only in local/dev        |
| Access token TTL     | ≤ 15 minutes                                        |
| Refresh token TTL    | ≤ 24 hours, rotating, revocable                     |
| MFA                  | TOTP (RFC 6238) or WebAuthn for `operator`/`admin`  |
| Session binding      | Tokens bound to client fingerprint where supported  |

## Implementation Pointers

- Backend primitives: [../../orcaapi/app/core/security.py](../../orcaapi/app/core/security.py)
- Auth endpoints: [../../orcaapi/app/api/v1/endpoints/auth.py](../../orcaapi/app/api/v1/endpoints/auth.py)
- RBAC matrix: [../rbac/policies.yaml](../rbac/policies.yaml)

## Required Environment Variables

| Variable                          | Purpose                                |
|-----------------------------------|----------------------------------------|
| `SECRET_KEY`                      | JWT signing key (rotate ≥ every 90 d)  |
| `JWT_ALGORITHM`                   | `RS256` (prod) or `HS256` (dev only)   |
| `JWT_ACCESS_TOKEN_EXPIRES_MINUTES`| ≤ 15                                   |
| `OIDC_ISSUER_URL`                 | Identity provider issuer               |
| `OIDC_CLIENT_ID` / `_SECRET`      | Client credentials                     |
| `MFA_REQUIRED_ROLES`              | CSV list, e.g. `operator,admin`        |

Secrets are loaded from a secret manager (Vault, AWS Secrets Manager,
GCP Secret Manager). They must **never** be committed.

## MFA Enrollment Flow

1. User completes primary OIDC login.
2. On first access to an MFA-required role, the API returns
   `403 mfa_required`.
3. User enrolls via TOTP or WebAuthn (`/api/v1/auth/mfa/enroll`).
4. Subsequent logins issue tokens with the `amr: ["mfa"]` claim.
5. Sensitive endpoints require `amr` to include `mfa`.

## Token Validation Checklist

- [ ] Signature verified against the correct JWKS
- [ ] `iss` matches `OIDC_ISSUER_URL`
- [ ] `aud` matches the API audience
- [ ] `exp` not in the past, `nbf` not in the future
- [ ] `sub` resolves to an active, non-disabled user
- [ ] Role + `amr` satisfy the endpoint's policy
- [ ] Token not present in the revocation list
