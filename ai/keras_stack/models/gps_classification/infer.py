"""Inference helpers for the GPS classification module."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from ai.keras_stack.common.export import load_artifact_metadata, load_saved_keras_model
from ai.keras_stack.common.preprocessing import gps_points_to_feature_matrix, normalize_feature_matrix, pad_or_truncate
from ai.keras_stack.models.gps_classification.model import build_gps_encoder


def classify_gps_sequence(model_or_dir: Any, gps_window: list[dict[str, Any]] | np.ndarray) -> dict[str, Any]:
    metadata = None
    model = model_or_dir
    if isinstance(model_or_dir, (str, Path)):
        metadata = load_artifact_metadata(model_or_dir)
        model = load_saved_keras_model(model_or_dir)

    matrix = gps_points_to_feature_matrix(gps_window) if not isinstance(gps_window, np.ndarray) else np.asarray(gps_window, dtype=np.float32)
    input_shape = model.input_shape
    seq_len = int(input_shape[1])
    matrix = pad_or_truncate(matrix, seq_len)

    normalization = (metadata or {}).get("normalization") or {}
    if normalization:
        matrix, _stats = normalize_feature_matrix(matrix, normalization)

    probs = model.predict(matrix[None, ...], verbose=0)[0]
    predicted_index = int(np.argmax(probs))
    label_map = (metadata or {}).get("label_map") or {}
    inverse_label_map = {int(value): key for key, value in label_map.items()}
    encoder = build_gps_encoder(model)
    embedding = encoder.predict(matrix[None, ...], verbose=0)[0].tolist()
    return {
        "predicted_class": predicted_index,
        "predicted_label": inverse_label_map.get(predicted_index, str(predicted_index)),
        "probabilities": probs.tolist(),
        "embedding": embedding,
    }