# Contributing SmartCito Adapters

This document covers the SmartCito AI contribution path for LoRA and QLoRA improvements.

## Contribution Flow

1. Start from the dataset schema in [training/dataset_format.md](training/dataset_format.md).
2. Add or clean domain examples in your own dataset copy.
3. Prepare the dataset with `python training/prepare_dataset.py`.
4. Train with `python training/lora_training.py` or `python training/qlora_training.py`.
5. Evaluate the adapter with `python training/evaluate_adapters.py --adapter-path output/smartcito-lora`.
6. Verify that only adapter artifacts are present in `output/smartcito-lora/`.
7. Upload the adapter folder to Kaggle or attach it to your pull request workflow.
8. Open a pull request describing the dataset source, target task, and observed results.

If you prefer a single shell entry point over `make`, use [scripts/ai.sh](scripts/ai.sh) with `package`, `prepare`, `train-lora`, `train-qlora`, `evaluate`, or `full`.

To publish the generated Kaggle bundle, use [training/publish_kaggle_dataset.py](training/publish_kaggle_dataset.py) or `scripts/ai.sh publish-kaggle` after configuring your Kaggle API token.

The evaluator now writes both a JSON summary and a Markdown report suitable for pull requests. You can also score saved predictions without running inference by passing `--predictions-file`.

## Required Submission Notes

Each adapter submission should include:

- base model identifier
- whether LoRA or QLoRA was used
- dataset provenance and domain coverage
- number of records and high-level quality checks
- known limitations or regressions

## Review Rules

- No base model weights in commits or uploads tied to this repository.
- No secrets, API keys, private credentials, or personal data.
- No training data that violates applicable licensing or privacy restrictions.
- Keep adapter output reproducible with a documented command or notebook.

## Recommended Pull Request Summary

```text
Base model: meta-llama/Meta-Llama-3-8B-Instruct
Training mode: QLoRA
Dataset size: 12,400 records
Primary domains: drone telemetry, camera analytics, sensor fusion
Output artifact: output/smartcito-lora/
Evaluation summary: improved anomaly triage accuracy on internal validation prompts
```