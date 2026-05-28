# Quantum Compute

Quantum-ready compute guidance for Orca.

## Scope

This folder documents how Orca can consume:
- cloud-hosted quantum simulators
- managed quantum processing units (QPUs)
- post-quantum cryptography acceleration services
- future quantum anomaly-detection experiments

## Model

Orca remains a classical backbone first. Quantum services are attached via
modular APIs so they can be introduced incrementally without rewriting the
platform.

## Near-Term Uses

- PQC key management and signing workflows
- research prototypes for anomaly detection and optimization
- simulation environments for validating quantum-safe migration plans

## Integration Principle

Treat every quantum service as an external dependency behind an interface.
No core module should require a QPU to run.
