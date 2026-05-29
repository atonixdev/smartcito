"""Encoder-decoder trajectory forecasting model."""

from __future__ import annotations

from typing import Any

from ai.model_stack.common.backend import require_keras


def build_trajectory_lstm_model(past_len: int, feature_dim: int, future_len: int, output_dim: int = 2, encoder_units: int = 128) -> Any:
    keras, layers = require_keras()
    encoder_inputs = keras.Input(shape=(past_len, feature_dim), name="encoder_inputs")
    _encoder_outputs, state_h, state_c = layers.LSTM(encoder_units, return_state=True, name="encoder_lstm")(encoder_inputs)
    decoder_inputs = keras.Input(shape=(future_len, output_dim), name="decoder_inputs")
    decoder_lstm = layers.LSTM(encoder_units, return_sequences=True, return_state=True, name="decoder_lstm")
    decoder_outputs, _, _ = decoder_lstm(decoder_inputs, initial_state=[state_h, state_c])
    decoder_outputs = layers.TimeDistributed(layers.Dense(output_dim), name="decoder_output")(decoder_outputs)
    model = keras.Model([encoder_inputs, decoder_inputs], decoder_outputs, name="trajectory_prediction_model")
    model.compile(optimizer="adam", loss="mse")
    return model