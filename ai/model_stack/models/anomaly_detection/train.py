"""Training entrypoint for anomaly detection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from ai.model_stack.common.config import load_module_config
from ai.model_stack.common.export import save_keras_artifact
from ai.model_stack.common.preprocessing import gps_points_to_feature_matrix, normalize_feature_matrix, pad_or_truncate, sequence_mse
from ai.model_stack.common.schema import SequenceClassificationExample
from ai.model_stack.models.anomaly_detection.autoencoder import build_sequence_autoencoder


def _load_examples(dataset_path: str | Path) -> list[SequenceClassificationExample]:
    payload = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Anomaly dataset must be a JSON array")
    return [SequenceClassificationExample.from_mapping(item) for item in payload if isinstance(item, dict)]


def train_anomaly_autoencoder(dataset_path: str | Path, *, output_dir: str | Path) -> dict[str, Any]:
    module_dir = Path(__file__).resolve().parent
    config = load_module_config(module_dir)
    examples = _load_examples(dataset_path)
    if not examples:
        raise ValueError("No anomaly examples found")

    seq_len = int(config["sequence_length"])
    matrices = np.asarray([pad_or_truncate(gps_points_to_feature_matrix(example.sequence), seq_len) for example in examples], dtype=np.float32)
    flattened = matrices.reshape((-1, matrices.shape[-1]))
    _, normalization = normalize_feature_matrix(flattened)
    normalized = np.asarray([normalize_feature_matrix(matrix, normalization)[0] for matrix in matrices], dtype=np.float32)

    model = build_sequence_autoencoder(seq_len=normalized.shape[1], feature_dim=normalized.shape[2], latent_dim=int(config["latent_dim"]))
    history = model.fit(
        normalized,
        normalized,
        epochs=int(config["training"]["epochs"]),
        batch_size=int(config["training"]["batch_size"]),
        validation_split=float(config["training"]["validation_split"]),
        verbose=0,
    )
    reconstructions = model.predict(normalized, verbose=0)
    errors = [sequence_mse(source, reconstruction) for source, reconstruction in zip(normalized, reconstructions, strict=False)]
    threshold = float(np.percentile(errors, float(config.get("threshold_percentile", 95))))
    manifest = save_keras_artifact(
        model,
        output_dir,
        config=config,
        metadata={"history": history.history, "dataset_path": str(dataset_path), "threshold": threshold},
        normalization=normalization,
        enable_onnx=bool(config["export"].get("onnx", False)),
    )
    return {"artifact_dir": str(output_dir), "threshold": threshold, "manifest": manifest}


def main() -> int:
    parser = argparse.ArgumentParser(description="Train the Orca anomaly autoencoder")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    result = train_anomaly_autoencoder(args.dataset, output_dir=args.output_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())