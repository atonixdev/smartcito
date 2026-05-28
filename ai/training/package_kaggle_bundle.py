from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


AI_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = AI_ROOT.parent
DEFAULT_OUTPUT = REPO_ROOT / "dist" / "orca_ai_kaggle"
FOLDERS_TO_COPY = ("ai_models", "training", "datasets", "assets")
FILES_TO_COPY = ("LICENSE",)
DOCS_TO_COPY = ("MODEL_CARD.md", "OPERATIONAL_FLOW.md", "KAGGLE_USAGE.md")
EXAMPLE_FILES_TO_COPY = ("orca_training_demo.ipynb", "orca_inference_demo.ipynb")
PROHIBITED_WEIGHT_PATTERNS = (
    "*.bin",
    "*.ckpt",
    "*.gguf",
    "*.h5",
    "*.onnx",
    "*.pb",
    "*.pt",
    "*.pth",
    "*.safetensors",
    "pytorch_model*",
    "model.safetensors*",
    "snapshot*",
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Package Orca AI assets into one Kaggle-uploadable folder.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    return parser


def _copy_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", *PROHIBITED_WEIGHT_PATTERNS),
    )


def _copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _assert_no_prohibited_weights(destination: Path) -> None:
    for pattern in PROHIBITED_WEIGHT_PATTERNS:
        matches = [path for path in destination.rglob(pattern) if path.is_file()]
        if matches:
            first_match = matches[0]
            raise RuntimeError(
                f"Kaggle bundle contains a prohibited model-weight artifact: {first_match.relative_to(destination)}"
            )


def package_bundle(output_dir: str | Path) -> Path:
    destination = Path(output_dir)
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)

    for folder_name in FOLDERS_TO_COPY:
        _copy_tree(AI_ROOT / folder_name, destination / folder_name)

    examples_destination = destination / "examples"
    examples_destination.mkdir(parents=True, exist_ok=True)
    for file_name in EXAMPLE_FILES_TO_COPY:
        _copy_file(AI_ROOT / "examples" / file_name, examples_destination / file_name)

    docs_destination = destination / "docs"
    docs_destination.mkdir(parents=True, exist_ok=True)
    for doc_name in DOCS_TO_COPY:
        _copy_file(REPO_ROOT / "docs" / doc_name, docs_destination / doc_name)

    _copy_file(AI_ROOT / "README.md", destination / "README.md")

    for file_name in FILES_TO_COPY:
        _copy_file(REPO_ROOT / file_name, destination / file_name)

    _assert_no_prohibited_weights(destination)

    manifest = {
        "bundle_name": "orca_ai_kaggle",
        "upload_this_folder": str(destination),
        "folders": list(FOLDERS_TO_COPY) + ["docs", "examples"],
        "files": list(FILES_TO_COPY),
        "notes": [
            "Upload this folder to Kaggle as a Dataset or zip it for notebook input.",
            "This bundle does not include LLaMA-3 weights.",
            "It only ships Orca code, LoRA/QLoRA adapters, and synthetic or private datasets.",
            "Users must obtain any compatible base model from official provider sources.",
            "Generated adapters belong in ai/output/orca-lora after training."
        ]
    }
    (destination / "kaggle_bundle_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    bundle_readme = destination / "README_KAGGLE_UPLOAD.md"
    bundle_readme.write_text(
        "# Orca Model Kaggle Bundle\n\n"
        "Upload this folder to Kaggle. It contains Orca inference code, training scripts, synthetic datasets, notebooks, and contributor documentation.\n\n"
        "## What To Upload\n\n"
        f"Upload the entire folder at `{destination}`.\n\n"
        "## Weight Policy\n\n"
        "This bundle does not include LLaMA-3 weights. It only ships Orca code, LoRA/QLoRA adapters, and synthetic or private datasets. Users must obtain any compatible base model from official provider sources.\n\n"
        "## What Not To Upload\n\n"
        "- LLaMA-3 or other foundation-model weights\n"
        "- API keys or local secrets\n"
        "- Large local checkpoints outside LoRA adapter outputs\n",
        encoding="utf-8",
    )

    return destination


def main() -> int:
    args = build_arg_parser().parse_args()
    output_dir = package_bundle(args.output_dir)
    print(f"Packaged Orca AI Kaggle bundle at {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())