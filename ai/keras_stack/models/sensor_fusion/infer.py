"""Inference helpers for the sensor fusion module."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from ai.keras_stack.common.export import load_artifact_metadata, load_saved_keras_model
from ai.keras_stack.common.preprocessing import prepare_metadata_vector


def score_sensor_fusion(model_or_dir: Any, *, gps_embedding: list[float] | np.ndarray, vision_embedding: list[float] | np.ndarray, metadata: dict[str, Any]) -> dict[str, Any]:
    metadata_manifest = None
    model = model_or_dir
    if isinstance(model_or_dir, (str, Path)):
        metadata_manifest = load_artifact_metadata(model_or_dir)
        model = load_saved_keras_model(model_or_dir)

    meta_keys = ((metadata_manifest or {}).get("metadata") or {}).get("meta_keys") or []
    gps_vector = np.asarray(gps_embedding, dtype=np.float32)[None, ...]
    vision_vector = np.asarray(vision_embedding, dtype=np.float32)[None, ...]
    meta_vector = prepare_metadata_vector(metadata, meta_keys)[None, ...]
    prediction = model.predict([gps_vector, vision_vector, meta_vector], verbose=0)[0]
    score = float(prediction[0]) if prediction.ndim else float(prediction)
    return {"risk_score": score, "label": "risky" if score >= 0.5 else "safe"}