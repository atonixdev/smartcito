"""Sequence autoencoder for anomaly detection."""

from __future__ import annotations

from typing import Any

from ai.keras_stack.common.backend import require_keras


def build_sequence_autoencoder(seq_len: int, feature_dim: int, latent_dim: int = 64) -> Any:
    keras, layers = require_keras()
    inputs = keras.Input(shape=(seq_len, feature_dim), name="anomaly_inputs")
    x = layers.LSTM(128, return_sequences=True, name="anomaly_encoder_lstm_1")(inputs)
    x = layers.LSTM(latent_dim, name="anomaly_encoder_lstm_2")(x)
    latent = layers.Dense(latent_dim, activation="relu", name="anomaly_embedding")(x)
    x = layers.RepeatVector(seq_len, name="anomaly_repeat")(latent)
    x = layers.LSTM(128, return_sequences=True, name="anomaly_decoder_lstm_1")(x)
    outputs = layers.TimeDistributed(layers.Dense(feature_dim), name="anomaly_reconstruction")(x)
    model = keras.Model(inputs, outputs, name="sequence_autoencoder")
    model.compile(optimizer="adam", loss="mse")
    return model