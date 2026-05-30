# Secure Coding Standards

These standards apply to **all** code in this repository. CI enforces a
subset of them; reviewers enforce the rest.

## Universal

- **Input validation at every trust boundary.** Validate type, length,
  range, format. Reject unknown fields.
- **Output encoding.** HTML/SQL/Shell/JSON context-aware encoding. Use
  parameterised queries — never string-concatenated SQL.
- **No secrets in code, logs, errors, or tests.** Use env vars + secret
  manager. Pre-commit hook + Gitleaks in CI.
- **Least privilege** for every credential, process, container, and IAM
  role.
- **Fail closed.** On error, deny access; never default-allow.
- **Crypto:** use library primitives in [`../crypto/STANDARDS.md`](../crypto/STANDARDS.md).
  No custom crypto.
- **Time:** UTC everywhere. Use monotonic clocks for intervals.
- **Random:** `secrets` (Python), Web Crypto (JS), libsodium (C). Never
  `random` for security purposes.
- **Dependencies:** pinned, scanned (`pip-audit`, `npm audit`, Trivy),
  reviewed for license + maintenance health before adding.

## Python (backend)

- PEP 8 + type hints required. `ruff`, `mypy --strict` clean.
- `bandit -r` clean (no `# nosec` without justification).
- Use Pydantic models at API boundaries.
- Never log request bodies that may contain PII; log structured fields
  and identifiers only.
- Use `subprocess.run([...], shell=False)`; never `shell=True` on
  untrusted input.

## TypeScript (frontend)

- `eslint . --max-warnings=0` clean, including `eslint-plugin-security`.
- No `dangerouslySetInnerHTML` without a documented sanitiser.
- All API calls go through `webapp/src/api/client.ts` (CSRF + auth
  headers centralised).
- CSP enabled; no inline scripts.

## C (native modules)

- `-Wall -Wextra -Werror -Wformat-security -fstack-protector-strong
  -D_FORTIFY_SOURCE=2`.
- AddressSanitizer + UBSan in CI test build.
- Bounds-checked APIs only (`snprintf`, `strncpy_s`, libsodium helpers).
- Free on every error path; verified with Valgrind or ASan leak check.

## API Design

- All state-changing endpoints require auth + RBAC + audit emission.
- Rate-limit every public endpoint.
- Use opaque IDs (UUIDs) in URLs, never sequential integers for
  user-facing resources.
- Return generic errors externally; log detail internally with a
  correlation ID.

## Forbidden Patterns

- `eval`, `exec` on user-controlled input.
- Disabling TLS verification.
- Wildcard CORS in production.
- Catching broad exceptions to swallow errors silently.
- Bypassing pre-commit / CI checks (`--no-verify`, `[skip ci]`).

## PR Review Checklist (Security)

- [ ] Threat model in PR description for new endpoints/data flows.
- [ ] Tests for both happy and unauthorised paths.
- [ ] Audit event emitted for state-changing actions.
- [ ] No secrets, no PII in logs.
- [ ] RBAC permission added/updated if needed.
- [ ] Compliance tags applied where personal data is touched.
