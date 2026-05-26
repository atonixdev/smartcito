from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "dist" / "smartcito_ai_kaggle"
FOLDERS_TO_COPY = ("ai_models", "training", "datasets", "examples")
FILES_TO_COPY = ("README.md", "LICENSE")
DOCS_TO_COPY = ("MODEL_CARD.md", "CONTRIBUTING.md", "KAGGLE_GUIDE.md")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Package SmartCito AI assets into one Kaggle-uploadable folder.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    return parser


def _copy_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))


def package_bundle(output_dir: str | Path) -> Path:
    destination = Path(output_dir)
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)

    for folder_name in FOLDERS_TO_COPY:
        _copy_tree(ROOT / folder_name, destination / folder_name)

    docs_destination = destination / "docs"
    docs_destination.mkdir(parents=True, exist_ok=True)
    for doc_name in DOCS_TO_COPY:
        shutil.copy2(ROOT / "docs" / doc_name, docs_destination / doc_name)

    for file_name in FILES_TO_COPY:
        shutil.copy2(ROOT / file_name, destination / file_name)

    manifest = {
        "bundle_name": "smartcito_ai_kaggle",
        "upload_this_folder": str(destination),
        "folders": list(FOLDERS_TO_COPY) + ["docs"],
        "files": list(FILES_TO_COPY),
        "notes": [
            "Upload this folder to Kaggle as a Dataset or zip it for notebook input.",
            "Do not add Meta LLaMA base weights to the bundle.",
            "Generated adapters belong in output/smartcito-lora after training."
        ]
    }
    (destination / "kaggle_bundle_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    bundle_readme = destination / "README_KAGGLE_UPLOAD.md"
    bundle_readme.write_text(
        "# SmartCito AI Kaggle Bundle\n\n"
        "Upload this folder to Kaggle. It contains the SmartCito AI inference code, training scripts, sample datasets, notebooks, and contributor documentation.\n\n"
        "## What To Upload\n\n"
        f"Upload the entire folder at `{destination}`.\n\n"
        "## What Not To Upload\n\n"
        "- Meta LLaMA base weights\n"
        "- API keys or local secrets\n"
        "- Large local checkpoints outside LoRA adapter outputs\n",
        encoding="utf-8",
    )

    return destination


def main() -> int:
    args = build_arg_parser().parse_args()
    output_dir = package_bundle(args.output_dir)
    print(f"Packaged SmartCito AI Kaggle bundle at {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())