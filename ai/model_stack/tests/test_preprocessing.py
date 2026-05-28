from __future__ import annotations

from ai.model_stack.common.preprocessing import aggregate_anomaly_score, build_sliding_windows, gps_points_to_feature_matrix, haversine_distance_meters


def test_gps_points_to_feature_matrix_engineers_expected_columns() -> None:
    matrix = gps_points_to_feature_matrix(
        [
            {"latitude": -26.2, "longitude": 28.0, "speed": 0.0, "heading": 10.0, "timestamp": 1.0},
            {"latitude": -26.21, "longitude": 28.01, "speed": 4.0, "heading": 15.0, "timestamp": 2.0},
        ]
    )
    assert matrix.shape == (2, 10)


def test_build_sliding_windows_pads_short_sequences() -> None:
    matrix = gps_points_to_feature_matrix([{"latitude": -26.2, "longitude": 28.0}])
    windows = build_sliding_windows(matrix, window_size=4)
    assert windows.shape == (1, 4, 10)


def test_anomaly_score_is_bounded() -> None:
    score = aggregate_anomaly_score(0.8, 0.9)
    assert 0.0 <= score <= 1.0


def test_haversine_distance_zero_for_same_point() -> None:
    assert haversine_distance_meters(-26.2, 28.0, -26.2, 28.0) == 0.0