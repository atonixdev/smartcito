# Orca Model Stack

This package adds a modular model stack to the existing Orca AI bundle.

The stack is organized around independent model modules that share a common schema,
config format, preprocessing layer, and export contract.

## Modules

- `models/gps_classification/` - multi-class classification over short GPS windows
- `models/trajectory_prediction/` - encoder-decoder LSTM route forecasting
- `models/anomaly_detection/` - sequence autoencoder plus combined anomaly scoring
- `models/drone_vision/` - transfer-learning image classifier for drone imagery
- `models/sensor_fusion/` - fused risk scoring over GPS, vision, and metadata embeddings

## Shared Components

- `common/schema.py` - shared input schema for GPS, sensors, frames, and fusion samples
- `common/preprocessing.py` - GPS feature engineering, normalization, sequence windows, teacher forcing
- `common/config.py` - YAML config loading and override support
- `common/export.py` - consistent model export and artifact manifest generation
- `pipeline.py` - unified inference wrapper over the modular model artifacts

## Export Contract

Each module saves a model artifact directory that can include:

- `model.keras` - native model format
- `saved_model/` - TensorFlow SavedModel export when supported by the runtime
- `artifact_manifest.json` - version, thresholds, labels, and preprocessing metadata
- `config.json` - resolved config used for training/export

ONNX export is kept optional and can be enabled later when `tf2onnx` or a similar
converter is available in the environment.