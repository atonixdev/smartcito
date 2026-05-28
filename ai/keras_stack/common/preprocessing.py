"""Common preprocessing utilities for Orca Keras models."""

from __future__ import annotations

import math
from typing import Any, Iterable

import numpy as np

from ai.keras_stack.common.schema import GPSPoint


def pad_or_truncate(matrix: np.ndarray, target_len: int) -> np.ndarray:
    if len(matrix) == target_len:
        return matrix.astype(np.float32)
    feature_dim = matrix.shape[1]
    if len(matrix) > target_len:
        return matrix[-target_len:].astype(np.float32)
    padded = np.zeros((target_len, feature_dim), dtype=np.float32)
    padded[: len(matrix)] = matrix.astype(np.float32)
    return padded


def normalize_feature_matrix(matrix: np.ndarray, stats: dict[str, list[float]] | None = None) -> tuple[np.ndarray, dict[str, list[float]]]:
    matrix = np.asarray(matrix, dtype=np.float32)
    if stats is None:
        means = matrix.mean(axis=0)
        stds = matrix.std(axis=0)
        stds = np.where(stds < 1e-6, 1.0, stds)
        stats = {"mean": means.tolist(), "std": stds.tolist()}
    mean = np.asarray(stats["mean"], dtype=np.float32)
    std = np.asarray(stats["std"], dtype=np.float32)
    std = np.where(std < 1e-6, 1.0, std)
    normalized = (matrix - mean) / std
    return normalized.astype(np.float32), stats


def build_sliding_windows(matrix: np.ndarray, window_size: int, stride: int = 1) -> np.ndarray:
    matrix = np.asarray(matrix, dtype=np.float32)
    if len(matrix) < window_size:
        return np.asarray([pad_or_truncate(matrix, window_size)], dtype=np.float32)
    windows = [matrix[index : index + window_size] for index in range(0, len(matrix) - window_size + 1, stride)]
    return np.asarray(windows, dtype=np.float32)


def build_future_targets(matrix: np.ndarray, past_len: int, future_len: int, position_indices: tuple[int, int] = (0, 1)) -> tuple[np.ndarray, np.ndarray]:
    matrix = np.asarray(matrix, dtype=np.float32)
    encoder_windows: list[np.ndarray] = []
    decoder_targets: list[np.ndarray] = []
    total_len = past_len + future_len
    if len(matrix) < total_len:
        return np.empty((0, past_len, matrix.shape[1]), dtype=np.float32), np.empty((0, future_len, len(position_indices)), dtype=np.float32)
    for index in range(0, len(matrix) - total_len + 1):
        window = matrix[index : index + total_len]
        encoder_windows.append(window[:past_len])
        decoder_targets.append(window[past_len:, list(position_indices)])
    return np.asarray(encoder_windows, dtype=np.float32), np.asarray(decoder_targets, dtype=np.float32)


def create_teacher_forcing_inputs(targets: np.ndarray) -> np.ndarray:
    targets = np.asarray(targets, dtype=np.float32)
    decoder_inputs = np.zeros_like(targets)
    decoder_inputs[:, 1:, :] = targets[:, :-1, :]
    return decoder_inputs


def compute_turn_angles(headings: np.ndarray) -> np.ndarray:
    headings = np.asarray(headings, dtype=np.float32)
    turns = np.zeros_like(headings)
    turns[1:] = np.diff(headings)
    return turns


def compute_stop_durations(speeds: np.ndarray, stop_threshold: float = 0.5) -> np.ndarray:
    speeds = np.asarray(speeds, dtype=np.float32)
    durations = np.zeros_like(speeds)
    running = 0.0
    for index, speed in enumerate(speeds):
        if speed <= stop_threshold:
            running += 1.0
        else:
            running = 0.0
        durations[index] = running
    return durations


def gps_points_to_feature_matrix(points: Iterable[GPSPoint | dict[str, Any]]) -> np.ndarray:
    resolved: list[GPSPoint] = []
    for item in points:
        resolved.append(item if isinstance(item, GPSPoint) else GPSPoint.from_mapping(item))
    if not resolved:
        return np.empty((0, 10), dtype=np.float32)

    origin_lat = resolved[0].latitude
    origin_lon = resolved[0].longitude
    headings = np.asarray([point.heading for point in resolved], dtype=np.float32)
    speeds = np.asarray([point.speed for point in resolved], dtype=np.float32)
    turn_angles = compute_turn_angles(headings)
    stop_durations = compute_stop_durations(speeds)

    rows: list[list[float]] = []
    previous_ts = resolved[0].timestamp
    for index, point in enumerate(resolved):
        time_delta = point.timestamp - previous_ts if index else 0.0
        previous_ts = point.timestamp
        rows.append(
            [
                point.latitude - origin_lat,
                point.longitude - origin_lon,
                point.altitude,
                point.speed,
                math.sin(math.radians(point.heading)),
                math.cos(math.radians(point.heading)),
                point.acceleration,
                time_delta,
                float(turn_angles[index]),
                float(stop_durations[index]),
            ]
        )
    return np.asarray(rows, dtype=np.float32)


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6_371_000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return radius * c


def sequence_mse(actual: np.ndarray, predicted: np.ndarray) -> float:
    actual = np.asarray(actual, dtype=np.float32)
    predicted = np.asarray(predicted, dtype=np.float32)
    return float(np.mean(np.square(actual - predicted)))


def aggregate_anomaly_score(
    reconstruction_error: float,
    prediction_error: float = 0.0,
    reconstruction_weight: float = 0.6,
    prediction_weight: float = 0.4,
) -> float:
    score = (reconstruction_error * reconstruction_weight) + (prediction_error * prediction_weight)
    return float(max(0.0, min(score, 1.0)))


def prepare_metadata_vector(metadata: dict[str, Any], keys: list[str]) -> np.ndarray:
    values = [float(metadata.get(key, 0.0) or 0.0) for key in keys]
    return np.asarray(values, dtype=np.float32)