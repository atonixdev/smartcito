"""Inference helpers for the drone vision module."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from ai.keras_stack.common.export import load_artifact_metadata, load_saved_keras_model
from ai.keras_stack.models.drone_vision.model import build_vision_encoder


def classify_image(model_or_dir: Any, image: Any) -> dict[str, Any]:
    metadata = None
    model = model_or_dir
    if isinstance(model_or_dir, (str, Path)):
        metadata = load_artifact_metadata(model_or_dir)
        model = load_saved_keras_model(model_or_dir)

    from keras.utils import img_to_array, load_img  # type: ignore[import-not-found]
    from PIL import Image

    target_shape = tuple(int(value) for value in model.input_shape[1:4])
    if isinstance(image, (str, Path)):
        image_obj = load_img(image, target_size=target_shape[:2])
        image_array = img_to_array(image_obj)
    elif isinstance(image, Image.Image):
        image_obj = image.resize(target_shape[:2])
        image_array = img_to_array(image_obj)
    else:
        image_array = np.asarray(image, dtype=np.float32)
    if image_array.shape[:2] != target_shape[:2]:
        image_array = np.asarray(Image.fromarray(image_array.astype("uint8")).resize(target_shape[:2]), dtype=np.float32)

    probs = model.predict(image_array[None, ...], verbose=0)[0]
    predicted_index = int(np.argmax(probs))
    label_map = (metadata or {}).get("label_map") or {}
    inverse_label_map = {int(value): key for key, value in label_map.items()}
    encoder = build_vision_encoder(model)
    embedding = encoder.predict(image_array[None, ...], verbose=0)[0].tolist()
    return {
        "predicted_class": predicted_index,
        "predicted_label": inverse_label_map.get(predicted_index, str(predicted_index)),
        "probabilities": probs.tolist(),
        "embedding": embedding,
    }