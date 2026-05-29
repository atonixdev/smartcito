from __future__ import annotations

import jax.numpy as jnp

from robot.ai.hybrid import predict_robot_energy_use, predict_robot_stability
from robot.cloud.contracts import build_robot_cloud_contract
from robot.navigation.control import obstacle_avoidance_command, smooth_return_to_base
from robot.navigation.localization import build_robot_localization_contract, ekf_localize
from robot.navigation.planning import build_navigation_contract, hybrid_a_star_score, plan_path_grid, rrt_star_step
from robot.perception.detection import build_robot_perception_contract, detect_obstacle_risk, terrain_classification_score
from robot.sensors.fusion import build_robot_sensor_contract, normalize_robot_sensors
from robot.service import app


def test_robot_planning_helpers() -> None:
    score = float(hybrid_a_star_score(1.0, 2.0, 0.5))
    node = rrt_star_step(jnp.array([0.0, 0.0]), jnp.array([1.0, 1.0]), 0.25)
    grid = jnp.array([[0.0, 1.0], [1.0, 0.0]])
    distances = plan_path_grid(grid, 0)
    assert score == 3.5
    assert node.shape == (2,)
    assert distances.shape == (2,)


def test_robot_navigation_and_localization_contracts() -> None:
    cmd = obstacle_avoidance_command(0.8, 1.2, 1.8)
    return_cmd = smooth_return_to_base(jnp.array([2.0, 1.0]), jnp.array([0.0, 0.0]), 1.0)
    state, covariance = ekf_localize(
        state=jnp.zeros(9),
        covariance=jnp.eye(9),
        imu_accel=jnp.zeros(3),
        imu_gyro=jnp.zeros(3),
        gps_position=jnp.array([1.0, 2.0, 0.0]),
        gps_velocity=jnp.array([0.2, 0.0, 0.0]),
        dt=0.1,
    )
    assert cmd.shape == (2,)
    assert return_cmd.shape == (2,)
    assert state.shape == (9,)
    assert covariance.shape == (9, 9)

    assert build_navigation_contract()["planning"]
    assert build_robot_localization_contract()["filters"]


def test_robot_perception_and_sensor_contracts() -> None:
    obstacle_risk = float(detect_obstacle_risk(0.5, 1.5, 2.0))
    terrain = terrain_classification_score(0.4, 0.6, 0.3)
    sensors = normalize_robot_sensors(
        jnp.array([1.0, 2.0, 3.0]),
        jnp.array([0.1, 0.2, 0.3]),
        jnp.array([4.0, 5.0, 6.0]),
        jnp.array([7.0, 8.0, 9.0]),
    )
    assert 0.0 <= obstacle_risk <= 1.0
    assert terrain.shape == (3,)
    assert sensors.shape == (4,)
    assert build_robot_perception_contract()["targets"]
    assert build_robot_sensor_contract()["primary"]


def test_robot_cloud_and_ai_contracts() -> None:
    cloud = build_robot_cloud_contract()
    stability = predict_robot_stability()
    energy = predict_robot_energy_use()
    assert cloud["cloud"]["services"]
    assert stability["safe"] is True
    assert energy["runtime_seconds"] > 0.0


def test_robot_fastapi_app_exists() -> None:
    assert app.title == "SmartCito Robot Stack"
