from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
import sys

try:
    from ai.orca_runtime.model import OrcaTrainingRecord, next_model_version, set_active_model, train_model
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from ai.orca_runtime.model import OrcaTrainingRecord, next_model_version, set_active_model, train_model


DEFAULT_DATASET_DIR = Path("ai/datasets")
DEFAULT_MODELS_DIR = Path("ai/models")
SKIP_FILE_NAMES = {"sample_evaluation_data.json", "sample_predictions.json"}


def _load_dataset_records(dataset_dir: Path) -> tuple[list[OrcaTrainingRecord], list[Path]]:
    records: list[OrcaTrainingRecord] = []
    sources: list[Path] = []
    for path in sorted(dataset_dir.glob("*.json")):
        if path.name in SKIP_FILE_NAMES:
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            continue
        accepted = 0
        for item in payload:
            if not isinstance(item, dict):
                continue
            instruction = str(item.get("instruction") or "").strip()
            output = str(item.get("output") or "").strip()
            if not instruction or not output:
                continue
            records.append(
                OrcaTrainingRecord(
                    instruction=instruction,
                    input=str(item.get("input") or "").strip(),
                    output=output,
                    metadata=dict(item.get("metadata") or {"source": path.name}),
                )
            )
            accepted += 1
        if accepted:
            sources.append(path)
    return records, sources


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train the Orca runtime model from JSON datasets in ai/datasets.")
    parser.add_argument("--dataset-dir", default=str(DEFAULT_DATASET_DIR))
    parser.add_argument("--models-dir", default=str(DEFAULT_MODELS_DIR))
    parser.add_argument("--version", default=None)
    parser.add_argument("--no-activate", action="store_true")
    return parser


def train_from_dataset_dir(
    *,
    dataset_dir: str | Path = DEFAULT_DATASET_DIR,
    models_dir: str | Path = DEFAULT_MODELS_DIR,
    version: str | None = None,
    activate: bool = True,
) -> dict[str, object]:
    dataset_dir = Path(dataset_dir)
    models_dir = Path(models_dir)
    records, source_paths = _load_dataset_records(dataset_dir)
    if not records:
        raise ValueError(f"No training records found in {dataset_dir}")

    resolved_version = version or next_model_version(models_dir)
    model = train_model(records, version=resolved_version, created_from=",".join(path.name for path in source_paths))
    model_dir = models_dir / resolved_version
    model.save(model_dir)
    metrics = asdict(model.metrics)
    (model_dir / "training_run.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (model_dir / "metadata.json").write_text(
        json.dumps(
            {
                "version": resolved_version,
                "records": len(records),
                "sources": [str(path) for path in source_paths],
                "artifact_dir": str(model_dir),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    active_pointer = None
    if activate:
        active_pointer = set_active_model(model_dir, models_dir=models_dir)

    return {
        "version": resolved_version,
        "records": len(records),
        "model_dir": str(model_dir),
        "sources": [str(path) for path in source_paths],
        "active_pointer": str(active_pointer) if active_pointer else None,
    }


def main() -> int:
    args = build_arg_parser().parse_args()
    result = train_from_dataset_dir(
        dataset_dir=args.dataset_dir,
        models_dir=args.models_dir,
        version=args.version,
        activate=not args.no_activate,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())