PYTHON ?= python3
ENV_FILE ?= .env
DATASET ?= ai/datasets/sample_training_data.json
EVAL_DATASET ?= ai/datasets/sample_evaluation_data.json
BASE_MODEL ?=
ADAPTER_PATH ?= ai/output/orca-lora
KAGGLE_BUNDLE_DIR ?= dist/orca_ai_kaggle
EVAL_OUTPUT ?= $(ADAPTER_PATH)/evaluation_summary.json
EVAL_REPORT ?= $(ADAPTER_PATH)/evaluation_report.md
KAGGLE_OWNER ?= jackiedeven
KAGGLE_SLUG ?= orca-ai-kaggle-bundle
KAGGLE_TITLE ?= Orca Kaggle Bundle
KAGGLE_LICENSE ?= Apache-2.0
KAGGLE_PRIVATE ?= 0
KAGGLE_UPDATE ?= 0
KAGGLE_DRY_RUN ?= 0
KAGGLE_DIR_MODE ?= zip

KAGGLE_PRIVATE_FLAG := $(if $(filter 1,$(KAGGLE_PRIVATE)),--private,)
KAGGLE_UPDATE_FLAG := $(if $(filter 1,$(KAGGLE_UPDATE)),--update,)
KAGGLE_DRY_RUN_FLAG := $(if $(filter 1,$(KAGGLE_DRY_RUN)),--dry-run,)

.PHONY: ai-help ai-prepare ai-package ai-train-lora ai-train-qlora ai-evaluate ai-report ai-publish-kaggle ai-full openstack-env k8s-backend-secret repo-check repo-help

ai-help:
	@printf '%s\n' 'Orca AI workflow targets:'
	@printf '%s\n' '  make ai-package                      Build the Kaggle upload bundle'
	@printf '%s\n' '  make ai-prepare                      Prepare the default training dataset'
	@printf '%s\n' '  make ai-train-lora                   Run LoRA fine-tuning'
	@printf '%s\n' '  make ai-train-qlora                  Run QLoRA fine-tuning'
	@printf '%s\n' '  make ai-evaluate                     Score an adapter and write JSON + Markdown reports'
	@printf '%s\n' '  make ai-report                       Alias for ai-evaluate'
	@printf '%s\n' '  make ai-publish-kaggle               Write Kaggle metadata and publish the bundle'
	@printf '%s\n' '                                        Set KAGGLE_PRIVATE=1, KAGGLE_UPDATE=1, KAGGLE_DRY_RUN=1, or KAGGLE_DIR_MODE=zip|tar|skip as needed'
	@printf '%s\n' '  make ai-full                         Package, prepare, and evaluate in sequence'

ai-package:
	$(PYTHON) ai/training/package_kaggle_bundle.py --output-dir $(KAGGLE_BUNDLE_DIR)

ai-prepare:
	$(PYTHON) ai/training/prepare_dataset.py --input $(DATASET) --output ai/datasets/prepared_orca_training_data.jsonl

ai-train-lora:
	$(PYTHON) ai/training/lora_training.py --dataset $(DATASET) $(if $(BASE_MODEL),--base-model $(BASE_MODEL),) --output-dir $(ADAPTER_PATH)

ai-train-qlora:
	$(PYTHON) ai/training/qlora_training.py --dataset $(DATASET) $(if $(BASE_MODEL),--base-model $(BASE_MODEL),) --output-dir $(ADAPTER_PATH)

ai-evaluate:
	$(PYTHON) ai/training/evaluate_adapters.py --dataset $(EVAL_DATASET) $(if $(BASE_MODEL),--base-model $(BASE_MODEL),) --adapter-path $(ADAPTER_PATH) --output $(EVAL_OUTPUT) --markdown-report $(EVAL_REPORT)

ai-report: ai-evaluate

ai-publish-kaggle:
	$(PYTHON) ai/training/publish_kaggle_dataset.py --bundle-dir $(KAGGLE_BUNDLE_DIR) --owner $(KAGGLE_OWNER) --slug $(KAGGLE_SLUG) --title "$(KAGGLE_TITLE)" --license $(KAGGLE_LICENSE) --dir-mode $(KAGGLE_DIR_MODE) $(KAGGLE_PRIVATE_FLAG) $(KAGGLE_UPDATE_FLAG) $(KAGGLE_DRY_RUN_FLAG)

ai-full: ai-package ai-prepare ai-evaluate

repo-help:
	@printf '%s\n' 'Repository organization targets:'
	@printf '%s\n' '  make repo-check                     Validate required directory structure and guardrails'

repo-check:
	bash scripts/repo_check.sh

openstack-env:
	bash infra/openstack/export-openstack-env.sh $(ENV_FILE)

k8s-backend-secret:
	bash infra/kubernetes/apply-backend-secret.sh $(ENV_FILE)