"""Training entrypoint for the sensor fusion model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from ai.keras_stack.common.config import load_module_config
from ai.keras_stack.common.export import load_saved_keras_model, save_keras_artifact
from ai.keras_stack.common.preprocessing import gps_points_to_feature_matrix, normalize_feature_matrix, pad_or_truncate, prepare_metadata_vector
from ai.keras_stack.common.schema import SensorFusionExample
from ai.keras_stack.models.drone_vision.model import build_vision_encoder
from ai.keras_stack.models.gps_classification.model import build_gps_encoder
from ai.keras_stack.models.sensor_fusion.model import build_sensor_fusion_model


def _load_examples(dataset_path: str | Path) -> list[SensorFusionExample]:
    payload = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Sensor fusion dataset must be a JSON array")
    return [SensorFusionExample.from_mapping(item) for item in payload if isinstance(item, dict)]


def _gps_embedding_for_example(example: SensorFusionExample, *, gps_encoder: Any | None, seq_len: int | None = None, normalization: dict[str, Any] | None = None) -> np.ndarray:
    if example.gps_embedding is not None:
        return np.asarray(example.gps_embedding, dtype=np.float32)
    if gps_encoder is None or seq_len is None:
        raise ValueError("Sensor fusion training needs gps embeddings or a GPS encoder artifact")
    matrix = pad_or_truncate(gps_points_to_feature_matrix(example.gps_sequence), seq_len)
    if normalization:
        matrix, _stats = normalize_feature_matrix(matrix, normalization)
    return np.asarray(gps_encoder.predict(matrix[None, ...], verbose=0)[0], dtype=np.float32)


def _vision_embedding_for_example(example: SensorFusionExample, *, vision_encoder: Any | None) -> np.ndarray:
    if example.vision_embedding is not None:
        return np.asarray(example.vision_embedding, dtype=np.float32)
    if vision_encoder is None or not example.image_path:
        raise ValueError("Sensor fusion training needs vision embeddings or a drone vision encoder artifact")
    from keras.utils import img_to_array, load_img  # type: ignore[import-not-found]

    target_shape = tuple(int(value) for value in vision_encoder.input_shape[1:3])
    image = load_img(example.image_path, target_size=target_shape)
    image_array = img_to_array(image)
    return np.asarray(vision_encoder.predict(image_array[None, ...], verbose=0)[0], dtype=np.float32)


def train_sensor_fusion_model(
    dataset_path: str | Path,
    *,
    output_dir: str | Path,
    gps_model_dir: str | Path | None = None,
    vision_model_dir: str | Path | None = None,
) -> dict[str, Any]:
    module_dir = Path(__file__).resolve().parent
    config = load_module_config(module_dir)
    examples = _load_examples(dataset_path)
    if not examples:
        raise ValueError("No sensor fusion examples found")

    gps_encoder = None
    gps_seq_len = None
    gps_normalization = None
    if gps_model_dir is not None:
        gps_model = load_saved_keras_model(gps_model_dir)
        gps_encoder = build_gps_encoder(gps_model)
        gps_seq_len = int(gps_model.input_shape[1])
        gps_normalization = (json.loads((Path(gps_model_dir) / "artifact_manifest.json").read_text(encoding="utf-8")).get("normalization") or {})

    vision_encoder = None
    if vision_model_dir is not None:
        vision_model = load_saved_keras_model(vision_model_dir)
        vision_encoder = build_vision_encoder(vision_model)

    meta_keys = list(config.get("meta_keys", []))
    gps_embeddings = np.asarray([
        _gps_embedding_for_example(example, gps_encoder=gps_encoder, seq_len=gps_seq_len, normalization=gps_normalization)
        for example in examples
    ], dtype=np.float32)
    vision_embeddings = np.asarray([
        _vision_embedding_for_example(example, vision_encoder=vision_encoder)
        for example in examples
    ], dtype=np.float32)
    meta_vectors = np.asarray([prepare_metadata_vector(example.metadata, meta_keys) for example in examples], dtype=np.float32)
    labels = np.asarray([float(example.label) for example in examples], dtype=np.float32)

    model = build_sensor_fusion_model(
        gps_embedding_dim=gps_embeddings.shape[1],
        vision_embedding_dim=vision_embeddings.shape[1],
        meta_dim=meta_vectors.shape[1],
        output_dim=int(config.get("output_dim", 1)),
    )
    history = model.fit(
        [gps_embeddings, vision_embeddings, meta_vectors],
        labels,
        epochs=int(config["training"]["epochs"]),
        batch_size=int(config["training"]["batch_size"]),
        validation_split=float(config["training"]["validation_split"]),
        verbose=0,
    )
    manifest = save_keras_artifact(
        model,
        output_dir,
        config=config,
        metadata={"history": history.history, "dataset_path": str(dataset_path), "meta_keys": meta_keys},
        enable_onnx=bool(config["export"].get("onnx", False)),
    )
    return {"artifact_dir": str(output_dir), "manifest": manifest}


def main() -> int:
    parser = argparse.ArgumentParser(description="Train the Orca sensor fusion model")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--gps-model-dir", default=None)
    parser.add_argument("--vision-model-dir", default=None)
    args = parser.parse_args()
    result = train_sensor_fusion_model(
        args.dataset,
        output_dir=args.output_dir,
        gps_model_dir=args.gps_model_dir,
        vision_model_dir=args.vision_model_dir,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())