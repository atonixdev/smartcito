# SmartCito Kaggle Usage

## What This Bundle Contains

- SmartCito training scripts
- SmartCito inference service code
- Synthetic or sovereign sample datasets
- Kaggle notebooks for training and inference
- Model and operational documentation

This bundle does not include LLaMA-3 weights. It only ships SmartCito code, LoRA or QLoRA adapters, and synthetic or sovereign datasets. Users must obtain LLaMA-3 or any other compatible base model from official provider sources.

## Recommended Bundle Layout

```text
ai/ai_models/
  inference.py
  llama_stack.py
  model.py

ai/training/
  lora_training.py
  prepare_dataset.py
  dataset_format.md

ai/datasets/
  sample_training_data.json

docs/
  MODEL_CARD.md
  OPERATIONAL_FLOW.md
  KAGGLE_USAGE.md

ai/examples/
  smartcito_training_demo.ipynb
  smartcito_inference_demo.ipynb
```

## Running Training

```bash
python ai/training/prepare_dataset.py \
  --input ai/datasets/sample_training_data.json \
  --output ai/datasets/prepared_smartcito_training_data.jsonl

python ai/training/lora_training.py \
  --dataset ai/datasets/sample_training_data.json \
  --base-model your-foundation-model-id \
  --output-dir ai/output/smartcito-lora
```

## Running Inference

- Use `ai/ai_models/inference.py` for the FastAPI service.
- Use `ai/examples/smartcito_inference_demo.ipynb` for a Kaggle-friendly inference walkthrough.

## Contribution Boundary

- Share only adapter artifacts from `ai/output/smartcito-lora/`
- Do not upload foundation-model weights
- Do not upload proprietary logs, secrets, or regulated data