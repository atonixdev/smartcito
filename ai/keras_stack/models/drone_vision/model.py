"""Transfer-learning drone vision classifier."""

from __future__ import annotations

from typing import Any

from ai.keras_stack.common.backend import require_keras


def build_drone_vision_cnn(num_classes: int, *, input_shape: tuple[int, int, int] = (224, 224, 3), backbone: str = "EfficientNetB0", weights: str | None = "imagenet", trainable_backbone: bool = False) -> Any:
    keras, layers = require_keras()
    if backbone != "EfficientNetB0":
        raise ValueError("Only EfficientNetB0 is configured in the initial Orca drone vision module")
    from keras.applications import EfficientNetB0  # type: ignore[import-not-found]
    from keras.applications.efficientnet import preprocess_input  # type: ignore[import-not-found]

    base_model = EfficientNetB0(include_top=False, weights=weights, input_shape=input_shape)
    base_model.trainable = trainable_backbone

    inputs = keras.Input(shape=input_shape, name="drone_image")
    x = preprocess_input(inputs)
    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D(name="vision_pool")(x)
    embedding = layers.Dense(256, activation="relu", name="vision_embedding")(x)
    x = layers.Dropout(0.3, name="vision_dropout")(embedding)
    outputs = layers.Dense(num_classes, activation="softmax", name="vision_class_output")(x)
    model = keras.Model(inputs, outputs, name="drone_vision_cnn")
    model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    return model


def build_vision_encoder(model: Any) -> Any:
    keras, _layers = require_keras()
    return keras.Model(model.input, model.get_layer("vision_embedding").output, name="vision_encoder")