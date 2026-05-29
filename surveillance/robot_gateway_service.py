"""
================================================================================
 File: surveillance/robot_gateway_service.py
 Purpose:
   Robot Gateway Service for Orca. It normalizes telemetry and commands
   from UGVs, patrol bots, and tunnel robots into the shared Orca event
   contract used by Mission Control and the operator dashboards.
================================================================================
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import os
import json
from urllib import error, request as urllib_request
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from orca_shared.crypto import build_secure_envelope

from surveillance.kafka import get_publisher
try:
    from surveillance.geospatial import normalize_point, resolve_zone
except ModuleNotFoundError:
    def normalize_point(position):  # type: ignore[no-redef]
        return {
            "position": position,
            "coordinate_system": "WGS84",
            "map_projection": "EPSG:4326",
            "projected": {
                "x": position.longitude,
                "y": position.latitude,
            },
        }

    def resolve_zone(position):  # type: ignore[no-redef]
        return {
            "zone_id": "zone-unknown",
            "zone_name": "Fallback Zone",
            "zone_type": "geofence",
            "criticality": "medium",
            "contains": True,
            "distance_to_boundary_m": None,
            "point": {
                "latitude": position.latitude,
                "longitude": position.longitude,
                "altitude_m": position.altitude_m,
            },
        }
from surveillance.models import (
    NormalizedEvent,
    PublishEnvelope,
    RobotCapabilities,
    RobotCommand,
    RobotCommandAck,
    RobotCommandAction,
    RobotConnectionRequest,
    RobotPatrolRoute,
    RobotRegistryStatus,
    RobotStatus,
    RobotTelemetry,
)
from surveillance.surveillance_pipeline import SurveillanceCycleRequest, run_surveillance_cycle, surveillance_architecture_contract
from surveillance.topics import ROBOT_EVENTS_TOPIC, ROBOT_MISSIONS_TOPIC, ROBOT_TELEMETRY_TOPIC, SURVEILLANCE_TOPICS


load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

app = FastAPI(title="Orca Robot Gateway Service")
_commands: dict[str, RobotCommand] = {}
_latest_telemetry: dict[str, RobotTelemetry] = {}
_robot_protocols: dict[str, str] = {}
_robot_registry: dict[str, RobotCapabilities] = {}
_robot_routes: dict[str, RobotPatrolRoute] = {}


def _threat_service_base_url() -> str:
    return os.getenv("THREAT_DETECTION_URL", "http://threat-detection:8023").rstrip("/")


def _mission_control_base_url() -> str:
    return os.getenv("MISSION_CONTROL_URL", "http://mission-control:8025").rstrip("/")


def _post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
    request_payload = urllib_request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json"},
        method="POST",
    )
    try:
        with urllib_request.urlopen(request_payload, timeout=5) as response:
            return json.loads(response.read().decode("utf-8") or "{}")
    except error.URLError as exc:
        return {"status": "unavailable", "reason": str(exc.reason)}
    except Exception as exc:  # pragma: no cover - defensive fallback around remote service failures
        return {"status": "failed", "reason": exc.__class__.__name__}


def _automation_payload_for_threat(robot_id: str, cycle: dict[str, object]) -> dict[str, object]:
    return {
        "robot_id": robot_id,
        "threat_detection": cycle.get("threat_detection", {}),
        "perception": cycle.get("perception", {}),
        "reaction": cycle.get("reaction", {}),
    }


def _automation_payload_for_dispatch(robot_id: str, cycle: dict[str, object]) -> dict[str, object]:
    perception = cycle.get("perception", {})
    terrain = perception.get("terrain", {}) if isinstance(perception, dict) else {}
    return {
        "robot_id": robot_id,
        "threat_level": str(cycle.get("threat_detection", {}).get("level", "low")) if isinstance(cycle.get("threat_detection", {}), dict) else "low",
        "reaction_action": str(cycle.get("reaction", {}).get("action", "continue_route")) if isinstance(cycle.get("reaction", {}), dict) else "continue_route",
        "environment": str(cycle.get("environment", "urban")),
        "latitude": terrain.get("latitude") if isinstance(terrain, dict) else None,
        "longitude": terrain.get("longitude") if isinstance(terrain, dict) else None,
    }


def _automate_surveillance_response(robot_id: str, cycle: dict[str, object]) -> dict[str, object]:
    threat_result = _post_json(
        f"{_threat_service_base_url()}/surveillance/escalate",
        _automation_payload_for_threat(robot_id, cycle),
    )
    dispatch_result = _post_json(
        f"{_mission_control_base_url()}/surveillance/dispatch",
        _automation_payload_for_dispatch(robot_id, cycle),
    )
    return {
        "threat_escalation": threat_result,
        "mission_dispatch": dispatch_result,
    }


def _seed_robot_state() -> None:
    if _robot_registry:
        return

    now = datetime.now(UTC)
    first = RobotCapabilities(
        robot_id="robot-patrol-007",
        model="Orca Patrol UGV",
        firmware_version="ugv-2.4.1",
        max_speed_mps=3.5,
        battery_capacity_mah=18000,
        camera_ids=["front-main", "rear-assist"],
        sensors=["lidar", "ultrasonic", "ir", "imu", "vibration"],
        autonomy_modes=["manual", "route_follow", "inspection_hold", "dock"],
        lidar_supported=True,
        status=RobotRegistryStatus.ONLINE,
        protocol="simulated",
        last_seen_at=now,
    )
    second = RobotCapabilities(
        robot_id="robot-tunnel-003",
        model="Orca Tunnel Inspector",
        firmware_version="tunnel-1.8.0",
        max_speed_mps=2.2,
        battery_capacity_mah=15000,
        camera_ids=["nav-main"],
        sensors=["lidar", "ultrasonic", "gas", "thermal", "wheel-slip"],
        autonomy_modes=["manual", "inspection_hold", "dock"],
        lidar_supported=True,
        status=RobotRegistryStatus.DEGRADED,
        protocol="simulated",
        last_seen_at=now,
    )
    _robot_registry[first.robot_id] = first
    _robot_registry[second.robot_id] = second
    _latest_telemetry[first.robot_id] = RobotTelemetry(
        robot_id=first.robot_id,
        protocol=first.protocol,
        position={"latitude": -25.7462, "longitude": 28.2372, "altitude_m": 0},
        speed_mps=1.8,
        heading_deg=124,
        battery_percent=81,
        autonomy_state="route_follow",
        status=RobotStatus.PATROLLING,
        slam_state="locked",
        timestamp=now,
    )
    _latest_telemetry[second.robot_id] = RobotTelemetry(
        robot_id=second.robot_id,
        protocol=second.protocol,
        position={"latitude": -25.7481, "longitude": 28.2329, "altitude_m": 0},
        speed_mps=1.1,
        heading_deg=88,
        battery_percent=63,
        autonomy_state="inspection_hold",
        status=RobotStatus.INSPECTING,
        slam_state="constrained",
        health_flags=["wheel-slip"],
        timestamp=now,
    )
    for route in [
        RobotPatrolRoute(
            robot_id=first.robot_id,
            name="Perimeter patrol alpha",
            checkpoints=["North gate", "Utility corridor", "Transit plaza", "Depot entry"],
            path=[
                {"latitude": -25.7467, "longitude": 28.2368, "altitude_m": 0},
                {"latitude": -25.7462, "longitude": 28.2372, "altitude_m": 0},
                {"latitude": -25.7458, "longitude": 28.2380, "altitude_m": 0},
            ],
        ),
        RobotPatrolRoute(
            robot_id=second.robot_id,
            name="Tunnel south loop",
            checkpoints=["Tunnel south", "Valve chamber", "Service hatch", "Return bay"],
            path=[
                {"latitude": -25.7486, "longitude": 28.2324, "altitude_m": 0},
                {"latitude": -25.7481, "longitude": 28.2329, "altitude_m": 0},
                {"latitude": -25.7478, "longitude": 28.2332, "altitude_m": 0},
            ],
        ),
    ]:
        _robot_routes[route.route_id] = route


def _discover_capabilities(request: RobotConnectionRequest) -> RobotCapabilities:
    return RobotCapabilities(
        robot_id=request.robot_id,
        model="Orca Connected Robot",
        firmware_version="robot-1.0.0",
        max_speed_mps=3.0,
        battery_capacity_mah=16000,
        camera_ids=["front-main"],
        sensors=["lidar", "ultrasonic", "ir", "imu"],
        autonomy_modes=["manual", "route_follow", "dock"],
        lidar_supported=True,
        status=RobotRegistryStatus.ONLINE,
        protocol=request.protocol,
    )


def _validate_command(command: RobotCommand) -> None:
    if command.action in {RobotCommandAction.SET_WAYPOINT} and command.target is None:
        raise HTTPException(status_code=422, detail="set_waypoint requires target")
    if command.action in {RobotCommandAction.FOLLOW_ROUTE} and not command.path:
        raise HTTPException(status_code=422, detail="follow_route requires path")


def _dispatch_command(command: RobotCommand) -> RobotCommandAck:
    _validate_command(command)
    command_id = str(uuid4())
    _commands[command_id] = command
    _robot_protocols[command.robot_id] = _robot_protocols.get(command.robot_id, "simulated")
    adapter_status = f"accepted:{command.action.value}"
    accepted = True

    current = _latest_telemetry.get(command.robot_id)
    if current is not None:
        next_status = current.status
        next_autonomy = current.autonomy_state
        if command.action == RobotCommandAction.HOLD:
            next_status = RobotStatus.HOLDING
            next_autonomy = "hold"
        elif command.action == RobotCommandAction.DOCK:
            next_status = RobotStatus.DOCKING
            next_autonomy = "dock"
        elif command.action == RobotCommandAction.FOLLOW_ROUTE:
            next_status = RobotStatus.PATROLLING
            next_autonomy = "route_follow"
        elif command.action == RobotCommandAction.SET_WAYPOINT:
            next_status = RobotStatus.INSPECTING
            next_autonomy = "waypoint"
        _latest_telemetry[command.robot_id] = current.model_copy(update={"status": next_status, "autonomy_state": next_autonomy, "timestamp": datetime.now(UTC)})

    event = NormalizedEvent(
        event_id=command_id,
        event_type=f"robot.command.{command.action.value}",
        source="robot-gateway",
        entity_id=command.robot_id,
        topic=ROBOT_EVENTS_TOPIC,
        payload={
            **command.model_dump(mode="json"),
            "adapter_status": adapter_status,
            "accepted": accepted,
            "security": build_secure_envelope(
                {**command.model_dump(mode="json"), "adapter_status": adapter_status, "accepted": accepted},
                purpose="robot-command",
                signer_id="robot-gateway",
                associated=command.robot_id,
            ),
        },
    )
    publish = get_publisher().publish_event(event)
    return RobotCommandAck(
        command_id=command_id,
        robot_id=command.robot_id,
        action=command.action,
        accepted=accepted,
        adapter_status=adapter_status,
        event=event,
        publish=publish,
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "robot-gateway"}


@app.get("/ready")
async def ready() -> dict[str, object]:
    _seed_robot_state()
    return {
        "service": "robot-gateway",
        "topics": {
            "telemetry": ROBOT_TELEMETRY_TOPIC,
            "events": ROBOT_EVENTS_TOPIC,
            "missions": ROBOT_MISSIONS_TOPIC,
        },
        "protocols": ["simulated", "rest", "websocket", "vendor-sdk"],
        "registry": "in-memory",
    }


@app.get("/surveillance/architecture")
async def surveillance_architecture() -> dict[str, object]:
    return surveillance_architecture_contract()


@app.post("/surveillance/cycle", response_model=PublishEnvelope)
async def execute_surveillance_cycle(request: SurveillanceCycleRequest) -> PublishEnvelope:
    cycle = run_surveillance_cycle(request)
    automation = _automate_surveillance_response(request.robot_id, cycle)
    event = NormalizedEvent(
        event_type="robot.surveillance.cycle.executed",
        source="robot-gateway",
        entity_id=request.robot_id,
        topic=ROBOT_EVENTS_TOPIC,
        payload={
            **cycle,
            "automation": automation,
            "security": build_secure_envelope(cycle, purpose="surveillance-cycle", signer_id="robot-gateway", associated=request.robot_id),
        },
    )
    return PublishEnvelope(event=event, publish=get_publisher().publish_event(event))


@app.post("/connect", response_model=RobotCapabilities)
async def connect_robot(request: RobotConnectionRequest) -> RobotCapabilities:
    capabilities = _discover_capabilities(request)
    _robot_registry[capabilities.robot_id] = capabilities
    _robot_protocols[request.robot_id] = request.protocol
    if request.robot_id not in _latest_telemetry:
        _latest_telemetry[request.robot_id] = RobotTelemetry(
            robot_id=request.robot_id,
            protocol=request.protocol,
            position={"latitude": -25.746, "longitude": 28.236, "altitude_m": 0},
            speed_mps=0,
            heading_deg=0,
            battery_percent=100,
            autonomy_state="manual",
            status=RobotStatus.IDLE,
            slam_state="mapping",
        )
    event = NormalizedEvent(
        event_type="robot.capabilities.discovered",
        source="robot-gateway",
        entity_id=request.robot_id,
        topic=ROBOT_EVENTS_TOPIC,
        payload=capabilities.model_dump(mode="json"),
    )
    get_publisher().publish_event(event)
    return capabilities


@app.post("/capabilities", response_model=RobotCapabilities)
async def upsert_capabilities(capabilities: RobotCapabilities) -> RobotCapabilities:
    _robot_registry[capabilities.robot_id] = capabilities
    _robot_protocols[capabilities.robot_id] = capabilities.protocol
    return capabilities


@app.get("/robots/{robot_id}/capabilities", response_model=RobotCapabilities)
async def get_capabilities(robot_id: str) -> RobotCapabilities:
    _seed_robot_state()
    capabilities = _robot_registry.get(robot_id)
    if capabilities is None:
        raise HTTPException(status_code=404, detail="robot capabilities not found")
    return capabilities


@app.post("/telemetry", response_model=PublishEnvelope)
async def ingest_telemetry(telemetry: RobotTelemetry) -> PublishEnvelope:
    _latest_telemetry[telemetry.robot_id] = telemetry
    _robot_protocols[telemetry.robot_id] = telemetry.protocol
    normalized = normalize_point(telemetry.position)
    normalized_position = normalized["position"] or telemetry.position
    telemetry_payload = {
        **telemetry.model_dump(mode="json"),
        "position": normalized_position.model_dump(mode="json"),
        "coordinate_system": normalized["coordinate_system"],
        "map_projection": normalized["map_projection"],
        "projected_position": normalized["projected"],
        "zone": resolve_zone(normalized_position),
    }
    event = NormalizedEvent(
        event_type="robot.telemetry.received",
        source="robot-gateway",
        entity_id=telemetry.robot_id,
        timestamp=telemetry.timestamp,
        topic=ROBOT_TELEMETRY_TOPIC,
        payload={
            **telemetry_payload,
            "security": build_secure_envelope(telemetry_payload, purpose="robot-telemetry", signer_id=telemetry.robot_id, associated=telemetry.robot_id),
        },
    )
    return PublishEnvelope(event=event, publish=get_publisher().publish_event(event))


@app.post("/commands", response_model=RobotCommandAck)
async def send_command(command: RobotCommand) -> RobotCommandAck:
    _seed_robot_state()
    return _dispatch_command(command)


@app.post("/robots/{robot_id}/commands", response_model=RobotCommandAck)
async def send_robot_command(robot_id: str, command: RobotCommand) -> RobotCommandAck:
    _seed_robot_state()
    if command.robot_id != robot_id:
        raise HTTPException(status_code=422, detail="path robot_id must match command.robot_id")
    return _dispatch_command(command)


@app.get("/robots")
async def list_robots() -> dict[str, list[dict[str, object]]]:
    _seed_robot_state()
    registry_robots = {item.robot_id: item.model_dump(mode="json") for item in _robot_registry.values()}
    return {
        "robots": [
            {
                **telemetry.model_dump(mode="json"),
                "capabilities": registry_robots.get(telemetry.robot_id),
            }
            for telemetry in _latest_telemetry.values()
        ],
        "registry": list(registry_robots.values()),
        "routes": [route.model_dump(mode="json") for route in _robot_routes.values()],
    }


@app.get("/topics")
async def topics() -> dict[str, str]:
    return SURVEILLANCE_TOPICS