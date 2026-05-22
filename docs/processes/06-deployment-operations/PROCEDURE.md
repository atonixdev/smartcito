<!--
================================================================================
 File: docs/processes/06-deployment-operations/PROCEDURE.md
 Purpose:
   Deployment operations procedure for SmartCito containers, services, and
   infrastructure.
================================================================================
-->

# Deployment Operations Procedure

## Purpose

Provide a controlled process for deploying SmartCito services to local,
staging, pilot, or production-like environments.

## Scope

This procedure covers Docker Compose, service containers, Kubernetes assets,
Terraform or Puppet changes, and deployment verification.

## Procedure

1. Confirm the target environment, deployment owner, and approved change window.
2. Review the release notes and required configuration changes.
3. Confirm secrets, environment variables, registry access, and infrastructure
   credentials are available through approved channels.
4. Build or pull the required images.
5. Apply database migrations or infrastructure changes in the approved order.
6. Deploy services with the target environment's deployment mechanism.
7. Run health checks for API, webapp, data stores, queues, and edge integrations.
8. Monitor logs, metrics, and service status during the stabilization window.
9. Record deployment evidence and any follow-up actions.

## Validation Checklist

- Target environment and change window are approved.
- Deployment inputs are versioned and traceable.
- Health checks pass after deployment.
- Monitoring shows no unresolved critical errors.
- Rollback path is known before deployment begins.

## Related Documentation

- [../../DOCKER_DEPLOYMENT.md](../../DOCKER_DEPLOYMENT.md)
- [../../../infra](../../../infra)
- [../../../services/README.md](../../../services/README.md)
