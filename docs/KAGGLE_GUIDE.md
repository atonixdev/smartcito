# SmartCito Kaggle Guide

This repository is structured so contributors can upload it to Kaggle, fine-tune SmartCito adapters, and submit improvements back to the project.

## What To Upload

Build the single Kaggle bundle folder first:

```bash
python ai/training/package_kaggle_bundle.py
```

If you do not use `make`, you can run:

```bash
scripts/ai.sh package
```

Then write Kaggle dataset metadata and publish with:

```bash
KAGGLE_OWNER=jackiedeven ./scripts/ai.sh publish-kaggle
```

If this is the first upload and you only want to prepare metadata first, use:

```bash
KAGGLE_OWNER=jackiedeven KAGGLE_DRY_RUN=1 ./scripts/ai.sh publish-kaggle
```

Then upload the generated folder:

- `dist/smartcito_ai_kaggle/`

That folder already contains the SmartCito Model code, training scripts, sample datasets, notebooks, and contributor docs needed for Kaggle.

Primary public demo assets inside the bundle:

- `ai/examples/SmartCito_Training_Demo.ipynb`
- `ai/examples/inference_demo.py`

Do not upload Meta LLaMA-3 base weights.

## Kaggle Setup

1. Create a new Kaggle Notebook with GPU enabled.
2. Add `dist/smartcito_ai_kaggle/` as a Dataset or upload that folder as a zip.
3. Install dependencies from `ai/ai_models/requirements.txt`.
4. Provide a Hugging Face token through Kaggle Secrets if the base model requires gated access.
5. Install the Kaggle CLI locally if you are publishing from your machine: `python3 -m pip install --user kaggle`.
6. Download your Kaggle API token and place it at `~/.kaggle/kaggle.json`, then run `chmod 600 ~/.kaggle/kaggle.json`.

Example setup cell:

```python
!pip install -r /kaggle/input/smartcito/ai/ai_models/requirements.txt
```

## Training Steps

1. Open [ai/examples/SmartCito_Training_Demo.ipynb](ai/examples/SmartCito_Training_Demo.ipynb) locally or in Kaggle.
2. Prepare the dataset with `ai/training/prepare_dataset.py`.
3. Run `ai/training/lora_training.py` or `ai/training/qlora_training.py`.
4. Confirm the adapter output is written to `ai/output/smartcito-lora/`.
5. Optionally evaluate the adapter before sharing it:

```bash
python ai/training/evaluate_adapters.py --adapter-path ai/output/smartcito-lora
```

Shell-wrapper equivalents:

```bash
scripts/ai.sh train-lora
scripts/ai.sh train-qlora
scripts/ai.sh evaluate
```

This writes:

- `ai/output/smartcito-lora/evaluation_summary.json`
- `ai/output/smartcito-lora/evaluation_report.md`

For offline scoring of saved predictions, run:

```bash
python ai/training/evaluate_adapters.py \
	--dataset ai/datasets/sample_evaluation_data.json \
	--predictions-file ai/datasets/sample_predictions.json
```

## Inference Steps

1. Run [ai/examples/inference_demo.py](ai/examples/inference_demo.py) locally or from a Kaggle code environment.
2. Point `SMARTCITO_BASE_MODEL_ID` to the gated base model id.
3. Point `SMARTCITO_LORA_ADAPTER_PATH` to the generated adapter directory.
4. Use local or API-backed inference to test SmartCito tasks.

## Submission Back To SmartCito

1. Export only the adapter folder and training summary.
2. Publish the adapter as a Kaggle Dataset or attach it to your collaboration flow.
3. Open a SmartCito pull request referencing the dataset, notebook, and adapter artifact.