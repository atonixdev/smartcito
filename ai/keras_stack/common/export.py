"""Model export helpers for the Orca Keras stack."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai.keras_stack.common.backend import require_keras


def save_keras_artifact(
    model: Any,
    export_dir: str | Path,
    *,
    config: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    label_map: dict[str, int] | None = None,
    normalization: dict[str, Any] | None = None,
    enable_onnx: bool = False,
) -> dict[str, Any]:
    require_keras()
    export_dir = Path(export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)

    keras_path = export_dir / "model.keras"
    model.save(keras_path)

    saved_model_path = export_dir / "saved_model"
    try:
        if hasattr(model, "export"):
            model.export(saved_model_path)
        else:
            model.save(saved_model_path)
    except Exception:  # pragma: no cover - backend/runtime specific
        saved_model_path = None

    manifest = {
        "version": config.get("version", "v1"),
        "module": config.get("module"),
        "label_map": label_map or {},
        "normalization": normalization or {},
        "metadata": metadata or {},
        "formats": {
            "keras": str(keras_path),
            "saved_model": str(saved_model_path) if saved_model_path else None,
            "onnx": None,
        },
    }

    if enable_onnx:
        try:
            import tf2onnx  # type: ignore[import-not-found]

            onnx_path = export_dir / "model.onnx"
            tf2onnx.convert.from_keras(model, output_path=str(onnx_path))
            manifest["formats"]["onnx"] = str(onnx_path)
        except ModuleNotFoundError:
            manifest["formats"]["onnx"] = None

    (export_dir / "artifact_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (export_dir / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    return manifest


def load_artifact_metadata(export_dir: str | Path) -> dict[str, Any]:
    export_dir = Path(export_dir)
    return json.loads((export_dir / "artifact_manifest.json").read_text(encoding="utf-8"))


def load_saved_keras_model(export_dir: str | Path) -> Any:
    keras, _layers = require_keras()
    export_dir = Path(export_dir)
    return keras.models.load_model(export_dir / "model.keras")