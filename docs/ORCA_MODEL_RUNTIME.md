# Orca Model Runtime

## Purpose

The Orca runtime provides an end-to-end path for ingestion, training, deployment, and inference.

## Components

- `ai/orca_runtime/model.py` trains and loads versioned Orca model artifacts without external foundation-model weights.
- `ingestion/datastream.py` pulls new operational events from configurable data sources and writes training-ready JSON batches to `ai/orca_datasets/`.
- `ai/training/orca_model_pipeline.py` consumes those batches, trains `ai/models/orca_model_vN/`, writes run metadata, and deploys an active model pointer.
- `ai/ai_models/inference.py` exposes Orca decision endpoints for mission logic, navigation, camera analysis, sensor fusion, threat assessment, geographic reasoning, and infrastructure operations.
- `orca` is the project CLI for ingestion, training, deployment, and sanitized dataset export.

## CLI

```bash
./orca ingest --config ingestion/config/datastream_sources.json
./orca train --batch-dir ai/orca_datasets
./orca deploy --version orca_model_v2
./orca dataset export --batch-dir ai/orca_datasets --output-path exports/orca_external.json
```

## DataStream Contract

Input sources are configured in `ingestion/config/datastream_sources.json`.
Each source defines:

- `backend`: `sqlite`, `postgres`, or `mongodb`
- `source_type`: `drone`, `robot`, `camera`, `sensor`, `geographic`, `threat`, `operator`, or `orca`
- `connection`: database path, DSN, or Mongo URI
- `table_or_collection`: table name or `database.collection`
- `processed_field`: field used to prevent re-ingestion

Output batches are written as:

- `ai/orca_datasets/batch_YYYYMMDD_HHMMSS.json`

## Model Versioning

- New training runs create `ai/models/orca_model_vN/`
- Active deployment is tracked in `ai/models/active_model.json`
- Each model version contains `model.json`, `metrics.json`, `metadata.json`, and `training_run.json`

## Non-Negotiables

- No external model weights are bundled
- Only private or synthetic data should be ingested for training
- Sanitized export must be used for any external sharing workflow
