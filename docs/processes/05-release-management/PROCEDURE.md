<!--
================================================================================
 File: docs/processes/05-release-management/PROCEDURE.md
 Purpose:
   Release readiness and publishing procedure for SmartCito.
================================================================================
-->

# Release Management Procedure

## Purpose

Define how SmartCito changes are prepared, reviewed, packaged, and documented
for release.

## Scope

This procedure covers release readiness, release notes, version alignment,
validation evidence, and post-release checks.

## Procedure

1. Confirm the release scope, target branch, and planned release window.
2. Review merged changes since the previous release.
3. Confirm required migrations, configuration changes, and deployment notes.
4. Run release-level validation for backend, frontend, infrastructure, and
   security-sensitive changes.
5. Prepare release notes with user-visible changes, operational notes, and known
   risks.
6. Confirm rollback or recovery steps for production-facing deployments.
7. Publish the release through the approved repository workflow.
8. Perform post-release smoke checks and record the result.

## Validation Checklist

- Release scope is documented.
- Required tests and builds pass.
- Deployment and rollback notes are complete.
- Release notes are published with known risks.
- Post-release verification is complete.

## Related Documentation

- [../../GITFLOW.md](../../GITFLOW.md)
- [../../SMARTCITO_EDGE_V1_RELEASE.md](../../SMARTCITO_EDGE_V1_RELEASE.md)
- [../06-deployment-operations/PROCEDURE.md](../06-deployment-operations/PROCEDURE.md)
