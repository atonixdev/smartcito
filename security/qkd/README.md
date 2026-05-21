# Quantum Key Distribution

SmartCito policy guidance for integrating QKD-derived key material.

## Principle

QKD is optional and future-facing. SmartCito must remain secure and operable on
classical infrastructure while being able to accept QKD-derived keys through
well-defined interfaces.

## Integration Model

- QKD systems terminate at controlled gateways or key-management layers
- SmartCito services never consume raw QKD transport directly
- derived keys enter the existing KMS/HSM and audit pipeline

## Audit Requirements

Every QKD-derived key import, activation, rotation, and retirement event must be
logged in the same audit domain as classical key-management events.
