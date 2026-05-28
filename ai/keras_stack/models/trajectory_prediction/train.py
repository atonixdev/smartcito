"""Training entrypoint for the trajectory forecasting model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from ai.keras_stack.common.config import load_module_config
from ai.keras_stack.common.export import save_keras_artifact
from ai.keras_stack.common.preprocessing import create_teacher_forcing_inputs, gps_points_to_feature_matrix, normalize_feature_matrix, pad_or_truncate
from ai.keras_stack.common.schema import TrajectoryExample
from ai.keras_stack.models.trajectory_prediction.model import build_trajectory_lstm_model


def _load_examples(dataset_path: str | Path) -> list[TrajectoryExample]:
    payload = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Trajectory dataset must be a JSON array")
    return [TrajectoryExample.from_mapping(item) for item in payload if isinstance(item, dict)]


def train_trajectory_model(dataset_path: str | Path, *, output_dir: str | Path) -> dict[str, Any]:
    module_dir = Path(__file__).resolve().parent
    config = load_module_config(module_dir)
    examples = _load_examples(dataset_path)
    if not examples:
        raise ValueError("No trajectory examples found")

    past_len = int(config["past_length"])
    future_len = int(config["future_length"])
    encoder_windows = []
    future_targets = []
    for example in examples:
        past_matrix = pad_or_truncate(gps_points_to_feature_matrix(example.past_sequence), past_len)
        future_matrix = pad_or_truncate(gps_points_to_feature_matrix(example.future_sequence), future_len)
        encoder_windows.append(past_matrix)
        future_targets.append(future_matrix[:, :2])
    encoder_x = np.asarray(encoder_windows, dtype=np.float32)
    future_y = np.asarray(future_targets, dtype=np.float32)
    flattened = encoder_x.reshape((-1, encoder_x.shape[-1]))
    _, normalization = normalize_feature_matrix(flattened)
    encoder_x = np.asarray([normalize_feature_matrix(item, normalization)[0] for item in encoder_x], dtype=np.float32)
    decoder_x = create_teacher_forcing_inputs(future_y)

    model = build_trajectory_lstm_model(
        past_len=past_len,
        feature_dim=encoder_x.shape[2],
        future_len=future_len,
        output_dim=future_y.shape[2],
        encoder_units=int(config.get("encoder_units", 128)),
    )
    history = model.fit(
        [encoder_x, decoder_x],
        future_y,
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
        normalization=normalization,
        enable_onnx=bool(config["export"].get("onnx", False)),
    )
    return {"artifact_dir": str(output_dir), "manifest": manifest}


def main() -> int:
    parser = argparse.ArgumentParser(description="Train the Orca trajectory forecasting model")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    result = train_trajectory_model(args.dataset, output_dir=args.output_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())