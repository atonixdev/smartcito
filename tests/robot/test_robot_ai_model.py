from __future__ import annotations

from robot.ai.hybrid import build_robot_ai_model
from robot.service import app


def test_robot_ai_model_contract() -> None:
    model = build_robot_ai_model()
    assert model["model_name"] == "SmartCito Robot AI"
    assert "physics" in model["inputs"]
    assert "ros2" in model["inputs"]
    assert "stabilize_robot" in model["outputs"]["primary_decisions"]


def test_robot_ai_model_route_exists() -> None:
    route_paths = {route.path for route in app.routes}
    assert "/robot/ai/model" in route_paths
