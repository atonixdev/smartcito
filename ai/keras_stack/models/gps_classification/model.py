"""Keras GPS sequence classification model."""

from __future__ import annotations

from typing import Any

from ai.keras_stack.common.backend import require_keras


def build_gps_classification_model(seq_len: int, feature_dim: int, num_classes: int, *, lstm_units: tuple[int, int] = (128, 64), dropout: float = 0.3) -> Any:
    keras, layers = require_keras()
    inputs = keras.Input(shape=(seq_len, feature_dim), name="gps_sequence")
    x = layers.Masking(mask_value=0.0, name="gps_masking")(inputs)
    x = layers.LSTM(lstm_units[0], return_sequences=True, name="gps_lstm_1")(x)
    x = layers.LSTM(lstm_units[1], name="gps_lstm_2")(x)
    x = layers.Dense(64, activation="relu", name="gps_dense_1")(x)
    x = layers.Dropout(dropout, name="gps_dropout")(x)
    embedding = layers.Dense(128, activation="relu", name="gps_embedding")(x)
    outputs = layers.Dense(num_classes, activation="softmax", name="gps_class_output")(embedding)

    model = keras.Model(inputs, outputs, name="gps_classification_model")
    model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    return model


def build_gps_encoder(model: Any) -> Any:
    keras, _layers = require_keras()
    return keras.Model(model.input, model.get_layer("gps_embedding").output, name="gps_sequence_encoder")