# Orca Operational Flow

Orca coordinates edge intelligence across drones, robots, cameras, IoT sensors, geographic services, and operator workflows.

## Flow Summary

1. Edge devices emit telemetry, alerts, imagery metadata, and mission context.
2. Orca normalizes those signals into operational records and event streams.
3. The training pipeline converts private or synthetic data into `instruction`, `input`, `output`, and `metadata` records.
4. LoRA or QLoRA fine-tuning produces adapter-only artifacts in `ai/output/orca-lora/`.
5. Evaluation checks domain coverage across drone missions, robot navigation, camera analytics, sensor fusion, threat reasoning, and geographic planning.
6. Inference runs through `ai/ai_models/inference.py` and `ai/ai_models/llama_stack.py`, using a user-supplied compatible base model plus Orca adapters.

## Bundle Boundary

This bundle does not include LLaMA-3 weights. It only ships Orca code, LoRA or QLoRA adapters, and synthetic or private datasets. Users must obtain any compatible base model from official provider sources.

## Primary Components

- `ai/ai_models/inference.py` exposes FastAPI inference endpoints.
- `ai/ai_models/llama_stack.py` wraps compatible OpenAI-style text-generation backends.
- `ai/training/prepare_dataset.py` normalizes raw logs into Orca training records.
- `ai/training/lora_training.py` and `ai/training/qlora_training.py` train adapter-only artifacts.
- `ai/datasets/sample_training_data.json` provides synthetic but realistic Orca examples.
- `ai/examples/Orca_Training_Demo.ipynb` and `ai/examples/orca_inference_demo.ipynb` show Kaggle-ready workflows.