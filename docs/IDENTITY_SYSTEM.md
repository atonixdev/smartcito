# ORCA Identity System

ORCA now has a shared identity foundation for UPI generation, LDAP entry modeling, RBAC policy enforcement, and audit-event creation.

## What is implemented

- Shared identity primitives live in `orca_shared.identity`
- Mandatory UPI format: `orca:<component-type>:<uuidv4>`
- LDAP DN generation uses the base tree `dc=orca,dc=internal`
- Required RBAC roles and permissions are modeled centrally
- ORCA API local-system access now boots with a real ORCA UPI instead of the legacy `local-device` placeholder
- Process bootstrap emits an identity audit event on API startup

## Package requirements

Install the identity dependencies where ORCA components need LDAP-backed identity:

```bash
pip install ldap3
pip install py-fortress
```

## Shared module usage

Generate a UPI:

```python
from orca_shared.identity import generate_upi

upi = generate_upi("service")
```

Bootstrap a local process identity:

```python
from orca_shared.identity import bootstrap_process_identity

identity = bootstrap_process_identity(
    component_type="service",
    role="orca.service",
    description="ORCA gateway service",
)
```

Build the LDAP entry that should be stored:

```python
from orca_shared.identity import build_ldap_entry

entry = build_ldap_entry(
    identity.upi,
    description=identity.description,
    role=identity.role,
)
```

Check permissions:

```python
from orca_shared.identity import role_has_permission

allowed = role_has_permission("orca.operator", "service.start")
```

Verify a live LDAP role assignment:

```python
from orca_shared.identity import LDAPIdentityDirectory

directory = LDAPIdentityDirectory(
    server_uri="ldap://localhost:389",
    bind_dn="cn=admin,dc=orca,dc=internal",
    bind_password="change-me",
)

verified = directory.verify_role_assignment(
    "orca:service:550e8400-e29b-41d4-a716-446655440000",
    expected_role="orca.service",
    permission="service.health",
)
```

Update a live LDAP role assignment:

```python
updated_identity = directory.update_role_assignment(
    "orca:service:550e8400-e29b-41d4-a716-446655440000",
    "orca.admin",
)
```

## Environment variables

The ORCA API reads these identity settings:

- `ORCA_UPI`
- `ORCA_COMPONENT_TYPE`
- `ORCA_IDENTITY_ROLE`
- `ORCA_IDENTITY_DESCRIPTION`
- `ORCA_LDAP_BASE_DN`
- `ORCA_LDAP_SERVER`
- `ORCA_LDAP_BIND_DN`
- `ORCA_LDAP_BIND_PASSWORD`

If `ORCA_UPI` is not supplied, the API generates a valid UPI during startup and registers it in the in-process identity directory.

## Current integration scope

The shared identity model is implemented and wired into the ORCA API startup and local-auth path.

Additional rollout surfaces now included:

- ORCA CLI can query the API identity posture with `orca api health identity`
- The hardware-domain agent service boots with its own `orca:agent:<uuidv4>` identity
- The Kafka event consumer worker boots with its own pod/process UPI for Kubernetes-facing deployments
- The API exposes `GET /api/v1/health/identity` for current process UPI and RBAC posture
- LDAP base tree bootstrap script: `python3 scripts/bootstrap_ldap_identity.py`
- LDAP bootstrap now also seeds the required ORCA roles and their permission mappings under `ou=roles`
- Live LDAP helpers can now search identities, verify role assignments, read seeded permissions, and update roles
- CLI can now register identities, bootstrap LDAP roles, inspect live permissions, and verify assignments
- API identity admin endpoints expose LDAP-backed identity operations for desktop operator tooling

The remaining rollout work is service-by-service and should use the same shared module for:

- CLI entrypoints
- TUI sessions
- device agents
- drone and robot runtimes
- firmware build pipelines
- Kubernetes pod bootstrap
- OpenStack worker processes
- ORCA OS processes

## Rollout rule

New ORCA runtime surfaces should not invent their own identity format or role map. Reuse `orca_shared.identity` and register the component UPI before the component begins serving work.

## Operational commands

Query the ORCA API identity posture:

```bash
orca api health identity
```

Inspect a live LDAP-backed ORCA identity from the CLI:

```bash
orca admin identity \
    --server ldap://localhost:389 \
    --bind-dn cn=admin,dc=orca,dc=internal \
    --bind-password change-me \
    inspect orca:service:550e8400-e29b-41d4-a716-446655440000
```

Update a live LDAP-backed ORCA role assignment from the CLI:

```bash
orca admin identity \
    --server ldap://localhost:389 \
    --bind-dn cn=admin,dc=orca,dc=internal \
    --bind-password change-me \
    update-role orca:service:550e8400-e29b-41d4-a716-446655440000 orca.admin
```

Verify a live LDAP-backed ORCA identity from the CLI:

```bash
orca admin identity \
    --server ldap://localhost:389 \
    --bind-dn cn=admin,dc=orca,dc=internal \
    --bind-password change-me \
    verify orca:service:550e8400-e29b-41d4-a716-446655440000 \
    --expected-role orca.admin \
    --permission telemetry.write
```

List the live LDAP permissions assigned to an ORCA role:

```bash
orca admin identity \
    --server ldap://localhost:389 \
    --bind-dn cn=admin,dc=orca,dc=internal \
    --bind-password change-me \
    list-role-permissions orca.admin
```

Create a new ORCA UPI and LDAP entry from the CLI:

```bash
orca admin identity \
    --server ldap://localhost:389 \
    --bind-dn cn=admin,dc=orca,dc=internal \
    --bind-password change-me \
    register \
    --component-type service \
    --role orca.service \
    --description "ORCA gateway service"
```

Seed LDAP role entries directly from the CLI:

```bash
orca admin identity \
    --server ldap://localhost:389 \
    --bind-dn cn=admin,dc=orca,dc=internal \
    --bind-password change-me \
    bootstrap-roles
```

Desktop/UI-facing API endpoints:

- `GET /api/v1/identity/admin/{upi}`
- `GET /api/v1/identity/admin/roles/{role}`
- `POST /api/v1/identity/admin/register`
- `POST /api/v1/identity/admin/{upi}/verify`
- `POST /api/v1/identity/admin/{upi}/role`
- `POST /api/v1/identity/admin/bootstrap-roles`

Render the LDAP bootstrap LDIF:

```bash
python3 scripts/bootstrap_ldap_identity.py --ldif-output /tmp/orca-identity.ldif
```

Apply the LDAP bootstrap tree directly:

```bash
python3 scripts/bootstrap_ldap_identity.py \
    --server ldap://localhost:389 \
    --bind-dn cn=admin,dc=orca,dc=internal \
    --bind-password change-me \
    --apply
```

Skip the initial ORCA role seed if you only want the LDAP base tree:

```bash
python3 scripts/bootstrap_ldap_identity.py --skip-role-seed
```