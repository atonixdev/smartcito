"""Training entrypoint for the drone vision model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ai.keras_stack.common.config import load_module_config
from ai.keras_stack.common.export import save_keras_artifact
from ai.keras_stack.common.schema import VisionClassificationExample
from ai.keras_stack.models.drone_vision.model import build_drone_vision_cnn


def _load_examples(dataset_path: str | Path) -> list[VisionClassificationExample]:
    payload = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Drone vision dataset must be a JSON array")
    return [VisionClassificationExample.from_mapping(item) for item in payload if isinstance(item, dict)]


def train_drone_vision_model(dataset_path: str | Path, *, output_dir: str | Path) -> dict[str, Any]:
    keras, _layers = __import__("ai.keras_stack.common.backend", fromlist=["require_keras"]).require_keras()
    module_dir = Path(__file__).resolve().parent
    config = load_module_config(module_dir)
    examples = _load_examples(dataset_path)
    if not examples:
        raise ValueError("No drone vision examples found")

    label_names = sorted({str(example.label) for example in examples})
    label_map = {label: index for index, label in enumerate(label_names)}
    image_size = tuple(int(value) for value in config["input_shape"][:2])

    from keras.utils import img_to_array, load_img  # type: ignore[import-not-found]
    import numpy as np

    images = []
    labels = []
    for example in examples:
        image = load_img(example.image_path, target_size=image_size)
        images.append(img_to_array(image))
        labels.append(label_map[str(example.label)])
    x_train = np.asarray(images, dtype="float32")
    y_train = np.asarray(labels, dtype="int32")

    model = build_drone_vision_cnn(
        num_classes=len(label_map),
        input_shape=tuple(int(value) for value in config["input_shape"]),
        backbone=str(config.get("backbone", "EfficientNetB0")),
        weights=config.get("weights"),
        trainable_backbone=bool(config.get("trainable_backbone", False)),
    )
    history = model.fit(
        x_train,
        y_train,
        epochs=int(config["training"]["epochs"]),
        batch_size=int(config["training"]["batch_size"]),
        validation_split=0.2,
        verbose=0,
    )
    manifest = save_keras_artifact(
        model,
        output_dir,
        config=config,
        metadata={"history": history.history, "dataset_path": str(dataset_path)},
        label_map=label_map,
        enable_onnx=bool(config["export"].get("onnx", False)),
    )
    return {"artifact_dir": str(output_dir), "manifest": manifest, "labels": label_map}


def main() -> int:
    parser = argparse.ArgumentParser(description="Train the Orca drone vision model")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    result = train_drone_vision_model(args.dataset, output_dir=args.output_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())