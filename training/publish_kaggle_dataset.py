from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE_DIR = ROOT / "dist" / "smartcito_ai_kaggle"
DEFAULT_SLUG = "smartcito-ai-kaggle-bundle"
DEFAULT_TITLE = "SmartCito AI Kaggle Bundle"
DEFAULT_LICENSE = "Apache-2.0"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Publish the SmartCito AI Kaggle bundle as a Kaggle dataset.")
    parser.add_argument("--bundle-dir", default=str(DEFAULT_BUNDLE_DIR))
    parser.add_argument("--owner", required=True, help="Kaggle username or organization name.")
    parser.add_argument("--slug", default=DEFAULT_SLUG, help="Kaggle dataset slug.")
    parser.add_argument("--title", default=DEFAULT_TITLE, help="Kaggle dataset title.")
    parser.add_argument("--license", dest="license_name", default=DEFAULT_LICENSE, help="Kaggle dataset license name.")
    parser.add_argument("--private", action="store_true", help="Create or update the dataset as private.")
    parser.add_argument("--version-notes", default="SmartCito AI Kaggle bundle update", help="Version notes for Kaggle dataset updates.")
    parser.add_argument("--update", action="store_true", help="Use kaggle datasets version instead of create.")
    parser.add_argument("--dry-run", action="store_true", help="Write metadata but do not call the Kaggle CLI.")
    return parser


def build_metadata(args: argparse.Namespace) -> dict[str, object]:
    return {
        "title": args.title,
        "id": f"{args.owner}/{args.slug}",
        "licenses": [{"name": args.license_name}],
        "keywords": ["smart-city", "llama3", "lora", "qlora", "kaggle", "smartcito"],
        "subtitle": "Kaggle-ready SmartCito AI training and inference bundle",
        "description": (
            "SmartCito AI bundle for LoRA/QLoRA fine-tuning, offline evaluation, "
            "and Kaggle-based collaboration. Ships scripts, datasets, notebooks, and docs only; "
            "no Meta LLaMA base weights are included."
        ),
        "isPrivate": bool(args.private),
    }


def write_metadata(bundle_dir: Path, metadata: dict[str, object]) -> Path:
    metadata_path = bundle_dir / "dataset-metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata_path


def ensure_bundle(bundle_dir: Path) -> None:
    if bundle_dir.exists():
        return
    raise SystemExit(
        f"Bundle directory does not exist: {bundle_dir}. Run python training/package_kaggle_bundle.py first."
    )


def ensure_kaggle_cli() -> None:
    try:
        subprocess.run(
            [sys.executable, "-m", "kaggle.cli", "--version"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise SystemExit(
            "Kaggle CLI is not installed. Install it with `python3 -m pip install --user kaggle`."
        )


def ensure_kaggle_auth() -> None:
    kaggle_config = Path.home() / ".kaggle" / "kaggle.json"
    if not kaggle_config.exists():
        raise SystemExit(
            "Kaggle API credentials are missing. Download kaggle.json from your Kaggle account and place it at ~/.kaggle/kaggle.json with chmod 600."
        )

    try:
        subprocess.run(
            [sys.executable, "-m", "kaggle.cli", "auth", "print-access-token"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise SystemExit(
            "Kaggle API credentials are invalid or expired. Generate a new API token from your Kaggle account, replace ~/.kaggle/kaggle.json, and run chmod 600 ~/.kaggle/kaggle.json."
        )


def publish_dataset(bundle_dir: Path, args: argparse.Namespace) -> None:
    ensure_kaggle_cli()
    ensure_kaggle_auth()

    if args.update:
        command = [
            sys.executable,
            "-m",
            "kaggle.cli",
            "datasets",
            "version",
            "-p",
            str(bundle_dir),
            "-m",
            args.version_notes,
        ]
    else:
        command = [
            sys.executable,
            "-m",
            "kaggle.cli",
            "datasets",
            "create",
            "-p",
            str(bundle_dir),
        ]

    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    args = build_arg_parser().parse_args()
    bundle_dir = Path(args.bundle_dir)
    ensure_bundle(bundle_dir)
    metadata_path = write_metadata(bundle_dir, build_metadata(args))
    print(f"Wrote Kaggle metadata to {metadata_path}")

    if args.dry_run:
        print("Dry run enabled; skipping Kaggle CLI publish step.")
        return 0

    publish_dataset(bundle_dir, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())