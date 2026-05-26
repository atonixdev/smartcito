#!/usr/bin/env zsh

set -euo pipefail

ROOT_DIR=${0:A:h:h}
cd "$ROOT_DIR"

PYTHON_BIN=${PYTHON_BIN:-python3}
DATASET=${DATASET:-ai/datasets/sample_training_data.json}
EVAL_DATASET=${EVAL_DATASET:-ai/datasets/sample_evaluation_data.json}
BASE_MODEL=${BASE_MODEL:-}
ADAPTER_PATH=${ADAPTER_PATH:-ai/output/smartcito-lora}
KAGGLE_BUNDLE_DIR=${KAGGLE_BUNDLE_DIR:-dist/smartcito_ai_kaggle}
EVAL_OUTPUT=${EVAL_OUTPUT:-$ADAPTER_PATH/evaluation_summary.json}
EVAL_REPORT=${EVAL_REPORT:-$ADAPTER_PATH/evaluation_report.md}
PREDICTIONS_FILE=${PREDICTIONS_FILE:-}
KAGGLE_OWNER=${KAGGLE_OWNER:-jackiedeven}
KAGGLE_SLUG=${KAGGLE_SLUG:-smartcito-ai-kaggle-bundle}
KAGGLE_TITLE=${KAGGLE_TITLE:-SmartCito AI Kaggle Bundle}
KAGGLE_LICENSE=${KAGGLE_LICENSE:-Apache-2.0}
KAGGLE_PRIVATE=${KAGGLE_PRIVATE:-0}
KAGGLE_UPDATE=${KAGGLE_UPDATE:-0}
KAGGLE_DRY_RUN=${KAGGLE_DRY_RUN:-0}
KAGGLE_DIR_MODE=${KAGGLE_DIR_MODE:-zip}

print_help() {
	cat <<'EOF'
SmartCito AI workflow wrapper

Usage:
  scripts/ai.sh help
  scripts/ai.sh package
  scripts/ai.sh prepare
  scripts/ai.sh train-lora
  scripts/ai.sh train-qlora
  scripts/ai.sh evaluate
  scripts/ai.sh report
	scripts/ai.sh publish-kaggle
  scripts/ai.sh full

Environment overrides:
  PYTHON_BIN
  DATASET
  EVAL_DATASET
  BASE_MODEL
  ADAPTER_PATH
  KAGGLE_BUNDLE_DIR
  EVAL_OUTPUT
  EVAL_REPORT
  PREDICTIONS_FILE
	KAGGLE_OWNER
	KAGGLE_SLUG
	KAGGLE_TITLE
	KAGGLE_LICENSE
	KAGGLE_PRIVATE
	KAGGLE_UPDATE
	KAGGLE_DRY_RUN
	KAGGLE_DIR_MODE
EOF
}

run_package() {
	"$PYTHON_BIN" ai/training/package_kaggle_bundle.py --output-dir "$KAGGLE_BUNDLE_DIR"
}

run_prepare() {
	"$PYTHON_BIN" ai/training/prepare_dataset.py --input "$DATASET" --output ai/datasets/prepared_smartcito_training_data.jsonl
}

run_train_lora() {
	local -a args
	args=(ai/training/lora_training.py --dataset "$DATASET" --output-dir "$ADAPTER_PATH")
	if [[ -n "$BASE_MODEL" ]]; then
		args+=(--base-model "$BASE_MODEL")
	fi
	"$PYTHON_BIN" "${args[@]}"
}

run_train_qlora() {
	local -a args
	args=(ai/training/qlora_training.py --dataset "$DATASET" --output-dir "$ADAPTER_PATH")
	if [[ -n "$BASE_MODEL" ]]; then
		args+=(--base-model "$BASE_MODEL")
	fi
	"$PYTHON_BIN" "${args[@]}"
}

run_evaluate() {
	local -a args
	args=(
		ai/training/evaluate_adapters.py
		--dataset "$EVAL_DATASET"
		--adapter-path "$ADAPTER_PATH"
		--output "$EVAL_OUTPUT"
		--markdown-report "$EVAL_REPORT"
	)

	if [[ -n "$BASE_MODEL" ]]; then
		args+=(--base-model "$BASE_MODEL")
	fi

	if [[ -n "$PREDICTIONS_FILE" ]]; then
		args+=(--predictions-file "$PREDICTIONS_FILE")
	fi

	"$PYTHON_BIN" "${args[@]}"
}

run_publish_kaggle() {
	local -a args
	args=(
		ai/training/publish_kaggle_dataset.py
		--bundle-dir "$KAGGLE_BUNDLE_DIR"
		--owner "$KAGGLE_OWNER"
		--slug "$KAGGLE_SLUG"
		--title "$KAGGLE_TITLE"
		--license "$KAGGLE_LICENSE"
		--dir-mode "$KAGGLE_DIR_MODE"
	)

	if [[ "$KAGGLE_PRIVATE" == "1" ]]; then
		args+=(--private)
	fi

	if [[ "$KAGGLE_UPDATE" == "1" ]]; then
		args+=(--update)
	fi

	if [[ "$KAGGLE_DRY_RUN" == "1" ]]; then
		args+=(--dry-run)
	fi

	"$PYTHON_BIN" "${args[@]}"
}

command_name=${1:-help}

case "$command_name" in
	help|-h|--help)
		print_help
		;;
	package)
		run_package
		;;
	prepare)
		run_prepare
		;;
	train-lora)
		run_train_lora
		;;
	train-qlora)
		run_train_qlora
		;;
	evaluate|report)
		run_evaluate
		;;
	publish-kaggle)
		run_publish_kaggle
		;;
	full)
		run_package
		run_prepare
		run_evaluate
		;;
	*)
		print_help >&2
		exit 1
		;;
esac