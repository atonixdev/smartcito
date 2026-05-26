# SmartCito Model Runtime

## Purpose

The SmartCito runtime provides a sovereign end-to-end path for ingestion, training, deployment, and inference.

## Components

- `ai/smartcito_runtime/model.py` trains and loads versioned SmartCito model artifacts without external foundation-model weights.
- `ingestion/datastream.py` pulls new operational events from configurable data sources and writes training-ready JSON batches to `ai/smartcito_datasets/`.
- `ai/training/smartcito_model_pipeline.py` consumes those batches, trains `ai/models/smartcito_model_vN/`, writes run metadata, and deploys an active model pointer.
- `ai/ai_models/inference.py` exposes SmartCito decision endpoints for mission logic, navigation, camera analysis, sensor fusion, threat assessment, geographic reasoning, and infrastructure operations.
- `smartcito` is the project CLI for ingestion, training, deployment, and sanitized dataset export.

## CLI

```bash
./smartcito ingest --config ingestion/config/datastream_sources.json
./smartcito train --batch-dir ai/smartcito_datasets
./smartcito deploy --version smartcito_model_v2
./smartcito dataset export --batch-dir ai/smartcito_datasets --output-path exports/smartcito_external.json
```

## DataStream Contract

Input sources are configured in `ingestion/config/datastream_sources.json`.
Each source defines:

- `backend`: `sqlite`, `postgres`, or `mongodb`
- `source_type`: `drone`, `robot`, `camera`, `sensor`, `geographic`, `threat`, `operator`, or `smartcito`
- `connection`: database path, DSN, or Mongo URI
- `table_or_collection`: table name or `database.collection`
- `processed_field`: field used to prevent re-ingestion

Output batches are written as:

- `ai/smartcito_datasets/batch_YYYYMMDD_HHMMSS.json`

## Model Versioning

- New training runs create `ai/models/smartcito_model_vN/`
- Active deployment is tracked in `ai/models/active_model.json`
- Each model version contains `model.json`, `metrics.json`, `metadata.json`, and `training_run.json`

## Non-Negotiables

- No external model weights are bundled
- Only sovereign or synthetic data should be ingested for training
- Sanitized export must be used for any external sharing workflow
