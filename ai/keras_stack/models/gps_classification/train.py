"""Training entrypoint for the GPS classification model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from ai.keras_stack.common.config import load_module_config, load_yaml_config
from ai.keras_stack.common.export import save_keras_artifact
from ai.keras_stack.common.preprocessing import gps_points_to_feature_matrix, normalize_feature_matrix, pad_or_truncate
from ai.keras_stack.common.schema import SequenceClassificationExample
from ai.keras_stack.models.gps_classification.model import build_gps_classification_model


def _load_examples(dataset_path: str | Path) -> list[SequenceClassificationExample]:
    payload = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("GPS classification dataset must be a JSON array")
    return [SequenceClassificationExample.from_mapping(item) for item in payload if isinstance(item, dict)]


def train_gps_classifier(dataset_path: str | Path, *, output_dir: str | Path, config_path: str | Path | None = None) -> dict[str, Any]:
    module_dir = Path(__file__).resolve().parent
    overrides = load_yaml_config(config_path) if config_path is not None else None
    config = load_module_config(module_dir, overrides)
    examples = _load_examples(dataset_path)
    if not examples:
        raise ValueError("No GPS classification examples found")

    label_names = config.get("labels") or sorted({str(example.label) for example in examples})
    label_map = {label: index for index, label in enumerate(label_names)}

    matrices = [pad_or_truncate(gps_points_to_feature_matrix(example.sequence), int(config["sequence_length"])) for example in examples]
    stacked = np.asarray(matrices, dtype=np.float32)
    flattened = stacked.reshape((-1, stacked.shape[-1]))
    _, normalization = normalize_feature_matrix(flattened)
    normalized = np.asarray([normalize_feature_matrix(matrix, normalization)[0] for matrix in stacked], dtype=np.float32)
    targets = np.asarray([label_map[str(example.label)] for example in examples], dtype=np.int32)

    model = build_gps_classification_model(
        seq_len=normalized.shape[1],
        feature_dim=normalized.shape[2],
        num_classes=len(label_map),
        lstm_units=tuple(config.get("lstm_units", [128, 64])),
        dropout=float(config.get("dropout", 0.3)),
    )
    history = model.fit(
        normalized,
        targets,
        epochs=int(config["training"]["epochs"]),
        batch_size=int(config["training"]["batch_size"]),
        validation_split=float(config["training"]["validation_split"]),
        verbose=0,
    )
    manifest = save_keras_artifact(
        model,
        output_dir,
        config=config,
        metadata={"history": history.history, "dataset_path": str(dataset_path)},
        label_map=label_map,
        normalization=normalization,
        enable_onnx=bool(config["export"].get("onnx", False)),
    )
    return {"artifact_dir": str(output_dir), "manifest": manifest, "labels": label_map}


def main() -> int:
    parser = argparse.ArgumentParser(description="Train the Orca GPS classification model")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    result = train_gps_classifier(args.dataset, output_dir=args.output_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())