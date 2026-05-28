# Security Tests

Security validation scripts and fixtures for Orca.

## Scope

- Authentication and RBAC regression tests
- Audit logging contract tests
- Fuzzing inputs on parsers and public API boundaries
- Dependency, container, and secrets scanning hooks
- Lightweight penetration test scripts against staging

## Layout

```
tests/security/
├── test_rbac_policy.py
├── test_audit_schema.py
├── fixtures/
└── README.md
```

## Running

```bash
pytest tests/security -v
```

These tests complement backend tests in [`../citosmart/tests/`](../citosmart/tests/)
and frontend tests in [`../webapp/src/`](../webapp/src/).
