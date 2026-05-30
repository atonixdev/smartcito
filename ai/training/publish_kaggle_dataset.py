from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


AI_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = AI_ROOT.parent
DEFAULT_BUNDLE_DIR = REPO_ROOT / "dist" / "orca_ai_kaggle"
DEFAULT_SLUG = "orca-ai-kaggle-bundle"
DEFAULT_TITLE = "Orca Kaggle Bundle"
DEFAULT_LICENSE = "Apache-2.0"
DEFAULT_DIR_MODE = "zip"


def resolve_kaggle_command() -> list[str]:
    kaggle_executable = shutil.which("kaggle")
    if kaggle_executable:
        return [kaggle_executable]
    return [sys.executable, "-m", "kaggle.cli"]


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Publish the Orca Kaggle bundle as a Kaggle dataset.")
    parser.add_argument("--bundle-dir", default=str(DEFAULT_BUNDLE_DIR))
    parser.add_argument("--owner", required=True, help="Kaggle username or organization name.")
    parser.add_argument("--slug", default=DEFAULT_SLUG, help="Kaggle dataset slug.")
    parser.add_argument("--title", default=DEFAULT_TITLE, help="Kaggle dataset title.")
    parser.add_argument("--license", dest="license_name", default=DEFAULT_LICENSE, help="Kaggle dataset license name.")
    parser.add_argument("--private", action="store_true", help="Create or update the dataset as private.")
    parser.add_argument("--version-notes", default="Orca Kaggle bundle update", help="Version notes for Kaggle dataset updates.")
    parser.add_argument(
        "--dir-mode",
        choices=("skip", "zip", "tar"),
        default=DEFAULT_DIR_MODE,
        help="How Kaggle CLI should upload subdirectories inside the bundle.",
    )
    parser.add_argument("--update", action="store_true", help="Use kaggle datasets version instead of create.")
    parser.add_argument("--dry-run", action="store_true", help="Write metadata but do not call the Kaggle CLI.")
    return parser


def build_metadata(args: argparse.Namespace) -> dict[str, object]:
    return {
        "title": args.title,
        "id": f"{args.owner}/{args.slug}",
        "licenses": [{"name": args.license_name}],
        "keywords": [
            "artificial intelligence",
            "computer vision",
            "deep learning",
            "geospatial analysis",
        ],
        "subtitle": "Orca training, inference, and synthetic data bundle",
        "description": (
            "Orca Model is the AI workspace for Orca operational intelligence. "
            "This Kaggle bundle packages model structure, ingestion pipelines, datasets, training logic, notebooks, and documentation "
            "for navigation, mapping, alerts, sensor fusion, weather analysis, and satellite-driven operational reasoning. "
            "Orca is designed to build on a compatible LLaMA-3 foundation model, but foundation-model weights are not included in this bundle."
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
        f"Bundle directory does not exist: {bundle_dir}. Run python ai/training/package_kaggle_bundle.py first."
    )


def ensure_kaggle_cli() -> None:
    kaggle_command = resolve_kaggle_command()
    try:
        subprocess.run(
            [*kaggle_command, "--version"],
            cwd=REPO_ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise SystemExit(
            "Kaggle CLI is not available. Install it in a virtual environment or expose the `kaggle` executable on PATH."
        )


def ensure_kaggle_auth() -> None:
    kaggle_command = resolve_kaggle_command()
    kaggle_config = Path.home() / ".kaggle" / "kaggle.json"
    kaggle_access_token = Path.home() / ".kaggle" / "access_token"
    if not kaggle_config.exists() and not kaggle_access_token.exists():
        raise SystemExit(
            "Kaggle credentials are missing. Either download kaggle.json from your Kaggle account into ~/.kaggle/kaggle.json or authenticate with `python3 -m kaggle.cli auth login`."
        )

    try:
        subprocess.run(
            [*kaggle_command, "competitions", "list"],
            cwd=REPO_ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise SystemExit(
            "Kaggle credentials are invalid or expired. Refresh ~/.kaggle/kaggle.json or run `python3 -m kaggle.cli auth login --force` to re-authenticate."
        )


def publish_dataset(bundle_dir: Path, args: argparse.Namespace) -> None:
    ensure_kaggle_cli()
    ensure_kaggle_auth()
    kaggle_command = resolve_kaggle_command()

    if args.update:
        command = [
            *kaggle_command,
            "datasets",
            "version",
            "-p",
            str(bundle_dir),
            "-m",
            args.version_notes,
            "-r",
            args.dir_mode,
        ]
    else:
        command = [
            *kaggle_command,
            "datasets",
            "create",
            "-p",
            str(bundle_dir),
            "-r",
            args.dir_mode,
        ]
        if not args.private:
            command.append("-u")

    subprocess.run(command, cwd=REPO_ROOT, check=True)


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