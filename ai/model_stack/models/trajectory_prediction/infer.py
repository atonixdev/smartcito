"""Inference helpers for the trajectory forecasting model."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from ai.model_stack.common.backend import require_keras
from ai.model_stack.common.export import load_artifact_metadata, load_saved_keras_model
from ai.model_stack.common.preprocessing import gps_points_to_feature_matrix, normalize_feature_matrix, pad_or_truncate


def _build_inference_models(model: Any) -> tuple[Any, Any]:
    keras, _layers = require_keras()
    encoder_inputs = model.input[0]
    encoder_lstm = model.get_layer("encoder_lstm")
    encoder_model = keras.Model(encoder_inputs, encoder_lstm.output[1:])

    decoder_dense = model.get_layer("decoder_output")
    decoder_lstm = model.get_layer("decoder_lstm")
    unit_count = int(decoder_lstm.units)
    output_dim = int(model.output_shape[-1])

    decoder_inputs = keras.Input(shape=(1, output_dim), name="decoder_step_input")
    state_input_h = keras.Input(shape=(unit_count,), name="decoder_state_h")
    state_input_c = keras.Input(shape=(unit_count,), name="decoder_state_c")
    decoder_outputs, state_h, state_c = decoder_lstm(decoder_inputs, initial_state=[state_input_h, state_input_c])
    decoder_outputs = decoder_dense(decoder_outputs)
    decoder_model = keras.Model([decoder_inputs, state_input_h, state_input_c], [decoder_outputs, state_h, state_c])
    return encoder_model, decoder_model


def predict_trajectory(model_or_dir: Any, past_seq: list[dict[str, Any]] | np.ndarray, future_len: int | None = None) -> dict[str, Any]:
    metadata = None
    model = model_or_dir
    if isinstance(model_or_dir, (str, Path)):
        metadata = load_artifact_metadata(model_or_dir)
        model = load_saved_keras_model(model_or_dir)

    matrix = gps_points_to_feature_matrix(past_seq) if not isinstance(past_seq, np.ndarray) else np.asarray(past_seq, dtype=np.float32)
    past_len = int(model.input_shape[0][1])
    matrix = pad_or_truncate(matrix, past_len)
    normalization = (metadata or {}).get("normalization") or {}
    if normalization:
        matrix, _stats = normalize_feature_matrix(matrix, normalization)

    encoder_model, decoder_model = _build_inference_models(model)
    state_h, state_c = encoder_model.predict(matrix[None, ...], verbose=0)
    predicted_steps = future_len or int(model.input_shape[1][1])
    decoder_input = np.zeros((1, 1, model.output_shape[-1]), dtype=np.float32)
    trajectories = []
    for _ in range(predicted_steps):
        output_tokens, state_h, state_c = decoder_model.predict([decoder_input, state_h, state_c], verbose=0)
        step = output_tokens[0, 0, :]
        trajectories.append(step.tolist())
        decoder_input = output_tokens[:, -1:, :]
    return {"predicted_trajectory": trajectories}