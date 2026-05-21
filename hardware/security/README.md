# Security Hardware

Physical and appliance-level controls that support the SmartCito software
security posture.

## Reference Components

- Hardware Security Modules (HSMs) for key storage and signing
- biometric access controls for server rooms and racks
- IDS/IPS appliances for north-south and east-west traffic monitoring
- UPS and backup generators for continuity
- tamper switches and secure elements for body and micro camera devices
- device allow-listing controls for registered camera hardware

## Control Mapping

- HSMs store or wrap keys used by the controls in
  [`../../security/crypto/STANDARDS.md`](../../security/crypto/STANDARDS.md).
- physical access events must be exported into the audit domain defined in
  [`../../security/audit/audit_log_schema.json`](../../security/audit/audit_log_schema.json).
- privileged hardware maintenance follows the incident and change controls in
  [`../../security/incident_response/playbook.md`](../../security/incident_response/playbook.md).
- body-camera and micro-camera casings should emit tamper events that map into
  the same audit domain and incident workflow.
