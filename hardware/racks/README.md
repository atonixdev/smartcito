# Rack Layout and Power

Reference rack placement for SmartCito installations.

## Placement Pattern

- **Top of rack**: core/distribution switches, firewalls, patch panels
- **Middle**: controller nodes and GPU compute nodes
- **Bottom**: storage arrays, UPS units, heavier gear

## Power

- dual power feeds per rack
- dual PSUs per server where supported
- separate A/B PDUs and monitored UPS capacity

## Cabling

- dual uplinks per node to separate switches where possible
- colour-coded management, data, and public-facing cabling
- labelled patching with rack-unit references and asset IDs

## Suggested Artifacts

Store diagrams, rack elevations, and power schedules in this folder as the
hardware footprint evolves.

## CI Coverage

- `test_power_distribution.py` validates rack telemetry, firmware baseline,
  power redundancy, UPS runtime, and thermal envelope.
- `ci_manifest.yaml` records the rack and power metrics required in CI.
