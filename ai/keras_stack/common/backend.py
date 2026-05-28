"""Optional Keras/TensorFlow backend loader."""

from __future__ import annotations

from typing import Any

KERAS_IMPORT_ERROR: Exception | None = None

try:
    import keras  # type: ignore[import-not-found]
    from keras import layers  # type: ignore[import-not-found]
except ModuleNotFoundError as exc:  # pragma: no cover - dependency driven
    keras = None  # type: ignore[assignment]
    layers = None  # type: ignore[assignment]
    KERAS_IMPORT_ERROR = exc


def require_keras() -> tuple[Any, Any]:
    if keras is None or layers is None:
        raise RuntimeError(
            "Keras 3 with a TensorFlow backend is required for the Orca Keras stack. "
            "Install the AI requirements before using these modules."
        ) from KERAS_IMPORT_ERROR
    return keras, layers