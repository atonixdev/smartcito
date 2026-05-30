"""FastAPI service for Orca robot contracts and physics summaries."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from dotenv import load_dotenv

from robot.ai.hybrid import build_robot_ai_model, predict_robot_energy_use, predict_robot_stability
from robot.cloud.contracts import build_robot_cloud_contract
from robot.navigation.localization import build_robot_localization_contract
from robot.navigation.planning import build_navigation_contract
from robot.physics.dynamics import build_robot_physics_contract
from robot.perception.detection import build_robot_perception_contract
from robot.sensors.fusion import build_robot_sensor_contract
from robot.ros2_ws.contract import build_ros2_robot_contract

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

app = FastAPI(title="Orca Robot Stack")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "robot-stack"}


@app.get("/robot/physics")
async def robot_physics() -> dict[str, object]:
    return build_robot_physics_contract()


@app.get("/robot/sensors")
async def robot_sensors() -> dict[str, object]:
    return build_robot_sensor_contract()


@app.get("/robot/perception")
async def robot_perception() -> dict[str, object]:
    return build_robot_perception_contract()


@app.get("/robot/navigation")
async def robot_navigation() -> dict[str, object]:
    return build_navigation_contract()


@app.get("/robot/localization")
async def robot_localization() -> dict[str, object]:
    return build_robot_localization_contract()


@app.get("/robot/cloud")
async def robot_cloud() -> dict[str, object]:
    return build_robot_cloud_contract()


@app.get("/robot/ros2")
async def robot_ros2() -> dict[str, object]:
    return build_ros2_robot_contract()


@app.get("/robot/ai/stability")
async def robot_ai_stability() -> dict[str, object]:
    return predict_robot_stability()


@app.get("/robot/ai/energy")
async def robot_ai_energy() -> dict[str, object]:
    return predict_robot_energy_use()


@app.get("/robot/ai/model")
async def robot_ai_model() -> dict[str, object]:
    return build_robot_ai_model()
