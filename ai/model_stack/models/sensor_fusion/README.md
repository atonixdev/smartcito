# Sensor Fusion

This module combines GPS embeddings, vision embeddings, and numeric metadata into
a fused risk score.

## Inputs

- GPS embedding from the GPS classifier encoder
- Vision embedding from the drone vision encoder
- Numeric metadata vector derived from config keys

## Outputs

- Risk score in the range `[0, 1]`
- Binary risk label (`safe` or `risky`)