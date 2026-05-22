<!--
================================================================================
 File: docs/processes/04-testing-and-quality/PROCEDURE.md
 Purpose:
   Testing and quality workflow for SmartCito changes.
================================================================================
-->

# Testing And Quality Procedure

## Purpose

Ensure every change receives validation that matches its risk, ownership area,
and user impact.

## Scope

This procedure covers unit tests, integration tests, frontend builds, security
checks, manual review, and evidence capture.

## Procedure

1. Identify the changed modules and the contracts they affect.
2. Select the smallest test command that can catch likely failures.
3. Add or update tests for new behavior, regressions, and edge cases.
4. Run focused tests locally before broad validation.
5. Run broader validation for cross-module, release, security, or deployment
   changes.
6. Capture test output, screenshots, logs, or PNG diagrams needed for review.
7. Record known test gaps in the pull request.
8. Do not expand the scope to unrelated failures unless they block the change.

## Validation Checklist

- Focused tests pass for touched code.
- Broad tests are run when shared behavior changes.
- Manual checks are documented when automation does not cover the workflow.
- Known limitations are visible to reviewers.

## Related Documentation

- [../../../tests/README.md](../../../tests/README.md)
- [../03-feature-delivery/PROCEDURE.md](../03-feature-delivery/PROCEDURE.md)
