"""Fusion network over GPS, vision, and metadata embeddings."""

from __future__ import annotations

from typing import Any

from ai.keras_stack.common.backend import require_keras


def build_sensor_fusion_model(gps_embedding_dim: int = 128, vision_embedding_dim: int = 256, meta_dim: int = 16, output_dim: int = 1) -> Any:
    keras, layers = require_keras()
    gps_input = keras.Input(shape=(gps_embedding_dim,), name="gps_input")
    vision_input = keras.Input(shape=(vision_embedding_dim,), name="vision_input")
    meta_input = keras.Input(shape=(meta_dim,), name="meta_input")

    x = layers.Concatenate(name="fusion_concat")([gps_input, vision_input, meta_input])
    x = layers.Dense(256, activation="relu", name="fusion_dense_1")(x)
    x = layers.Dropout(0.3, name="fusion_dropout_1")(x)
    x = layers.Dense(128, activation="relu", name="fusion_dense_2")(x)
    x = layers.Dropout(0.3, name="fusion_dropout_2")(x)
    outputs = layers.Dense(output_dim, activation="sigmoid", name="risk_score")(x)
    model = keras.Model(inputs=[gps_input, vision_input, meta_input], outputs=outputs, name="sensor_fusion_model")
    model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    return model