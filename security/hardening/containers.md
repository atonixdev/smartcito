# Container Hardening

This standard applies to every Docker/Kubernetes workload used by
Orca.

## Image Build

- Use minimal bases (`python:slim`, distroless, or Alpine only when ABI
  impact is understood).
- Multi-stage builds only.
- Pin base images by digest in production.
- Sign images with cosign before deployment.
- Scan every image with Trivy; fail on High/Critical.

## Runtime

- Run as a non-root user (`USER 10001` or named unprivileged account).
- `readOnlyRootFilesystem: true` unless a documented exception exists.
- Drop all Linux capabilities and add back only the minimum required.
- `allowPrivilegeEscalation: false`.
- `seccompProfile: RuntimeDefault`, AppArmor/SELinux enforced.
- Resource requests/limits mandatory.
- Liveness, readiness, and startup probes required.

## Network

- Default-deny ingress and egress NetworkPolicies.
- mTLS between services.
- No public exposure of databases, Kafka, MQTT, or admin endpoints.

## Kubernetes

- Namespace per environment.
- Pod Security Standard: `restricted`.
- Secrets mounted from external secret manager, not ConfigMaps.
- Admission control blocks unsigned images and privileged pods.

## Docker Compose / Local Dev

Local development may relax some controls, but never:
- run with committed secrets,
- disable auth for shared environments,
- expose services on `0.0.0.0` without a clear reason.
