# Quantum Key Distribution

Reference guidance for future QKD integration in SmartCito deployments.

## Scope

- satellite-based QKD links
- metro or campus fiber-based QKD links
- gateway appliances that expose QKD-derived keys to classical systems

## Design Principle

SmartCito should not depend on QKD to operate. Instead, APIs and key-management
interfaces should be ready to accept externally provisioned keys from QKD
systems when available.

## Practical Integration

- terminate QKD at dedicated gateway or key-management appliances
- inject derived keys into approved KMS/HSM workflows
- maintain audit trails for key provenance and rotation events

## SmartCito Mapping

See [`../../../security/qkd/README.md`](../../../security/qkd/README.md) for the
software and policy layer.
