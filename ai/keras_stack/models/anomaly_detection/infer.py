"""Inference helpers for anomaly detection."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from ai.keras_stack.common.export import load_artifact_metadata, load_saved_keras_model
from ai.keras_stack.common.preprocessing import aggregate_anomaly_score, gps_points_to_feature_matrix, normalize_feature_matrix, pad_or_truncate, sequence_mse
from ai.keras_stack.models.trajectory_prediction.infer import predict_trajectory


def score_sequence_anomaly(
    model_or_dir: Any,
    sequence: list[dict[str, Any]] | np.ndarray,
    *,
    trajectory_model_dir: str | Path | None = None,
    actual_future: np.ndarray | None = None,
) -> dict[str, Any]:
    metadata = None
    model = model_or_dir
    if isinstance(model_or_dir, (str, Path)):
        metadata = load_artifact_metadata(model_or_dir)
        model = load_saved_keras_model(model_or_dir)

    matrix = gps_points_to_feature_matrix(sequence) if not isinstance(sequence, np.ndarray) else np.asarray(sequence, dtype=np.float32)
    seq_len = int(model.input_shape[1])
    matrix = pad_or_truncate(matrix, seq_len)
    normalization = (metadata or {}).get("normalization") or {}
    if normalization:
        matrix, _stats = normalize_feature_matrix(matrix, normalization)

    reconstruction = model.predict(matrix[None, ...], verbose=0)[0]
    reconstruction_error = sequence_mse(matrix, reconstruction)
    threshold = float(((metadata or {}).get("metadata") or {}).get("threshold", 0.5))
    prediction_error = 0.0
    if trajectory_model_dir is not None and actual_future is not None:
        forecast = predict_trajectory(trajectory_model_dir, sequence)
        predicted_future = np.asarray(forecast["predicted_trajectory"], dtype=np.float32)
        prediction_error = sequence_mse(np.asarray(actual_future, dtype=np.float32), predicted_future[: len(actual_future)])
    combined = aggregate_anomaly_score(reconstruction_error, prediction_error)
    return {
        "reconstruction_error": reconstruction_error,
        "prediction_error": prediction_error,
        "combined_score": combined,
        "threshold": threshold,
        "is_anomaly": combined >= threshold,
    }