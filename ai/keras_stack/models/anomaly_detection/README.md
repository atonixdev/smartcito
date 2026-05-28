# Anomaly Detection

This module flags unusual sequence behavior with a sequence autoencoder and can
combine that score with a trajectory forecast error.

## Inputs

- GPS or sensor sequence using the shared Orca schema
- Optional actual future positions for combined scoring

## Outputs

- Reconstruction error
- Optional trajectory prediction error
- Combined anomaly score and threshold flag