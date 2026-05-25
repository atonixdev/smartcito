"""
================================================================================
 File: surveillance/drone_gateway_service.py
 Purpose:
   Drone Gateway Service for SmartCito. It normalizes telemetry and commands
   from MAVLink, vendor SDKs, REST, WebSocket, or simulated drones into the
   shared SmartCito event contract and Kafka topics.
================================================================================
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response
from smartcito_shared.crypto import build_secure_envelope

from surveillance.adapters import adapter_for, supported_protocols
from surveillance.geospatial import resolve_zone
from surveillance.kafka import get_publisher
from surveillance.metrics import metrics
from surveillance.models import DroneCapabilities, DroneCommand, DroneCommandAck, DroneConnectionRequest, DroneTelemetry, NormalizedEvent, PublishEnvelope
from surveillance.registry import registry
from surveillance.topics import DRONE_EVENTS_TOPIC, DRONE_MISSIONS_TOPIC, DRONE_TELEMETRY_TOPIC, SURVEILLANCE_TOPICS


load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

app = FastAPI(title="SmartCito Drone Gateway Service")
_commands: dict[str, DroneCommand] = {}
_latest_telemetry: dict[str, DroneTelemetry] = {}
_drone_protocols: dict[str, str] = {}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "drone-gateway"}


@app.get("/ready")
async def ready() -> dict[str, object]:
    return {
        "service": "drone-gateway",
        "topics": {
            "telemetry": DRONE_TELEMETRY_TOPIC,
            "events": DRONE_EVENTS_TOPIC,
            "missions": DRONE_MISSIONS_TOPIC,
        },
        "protocols": supported_protocols(),
        "registry": registry.db_status,
    }


@app.get("/metrics")
async def gateway_metrics() -> Response:
    return Response(metrics.prometheus_text(), media_type="text/plain; version=0.0.4")


@app.post("/connect", response_model=DroneCapabilities)
async def connect_drone(request: DroneConnectionRequest) -> DroneCapabilities:
    adapter = adapter_for(request.protocol)
    try:
        capabilities = adapter.discover_capabilities(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    registry_status = registry.upsert(capabilities)
    _drone_protocols[request.drone_id] = request.protocol
    metrics.increment("drone_connected")

    event = NormalizedEvent(
        event_type="drone.capabilities.discovered",
        source="drone-gateway",
        entity_id=request.drone_id,
        topic=DRONE_EVENTS_TOPIC,
        payload={**capabilities.model_dump(mode="json"), "registry_status": registry_status},
    )
    get_publisher().publish_event(event)
    return capabilities


@app.post("/capabilities", response_model=DroneCapabilities)
async def upsert_capabilities(capabilities: DroneCapabilities) -> DroneCapabilities:
    registry_status = registry.upsert(capabilities)
    _drone_protocols[capabilities.drone_id] = capabilities.protocol
    metrics.increment("capabilities_synced")
    event = NormalizedEvent(
        event_type="drone.capabilities.synced",
        source="drone-gateway",
        entity_id=capabilities.drone_id,
        topic=DRONE_EVENTS_TOPIC,
        payload={**capabilities.model_dump(mode="json"), "registry_status": registry_status},
    )
    get_publisher().publish_event(event)
    return capabilities


@app.get("/drones/{drone_id}/capabilities", response_model=DroneCapabilities)
async def get_capabilities(drone_id: str) -> DroneCapabilities:
    capabilities = registry.get(drone_id)
    if capabilities is None:
        raise HTTPException(status_code=404, detail="drone capabilities not found")
    return capabilities


@app.post("/telemetry", response_model=PublishEnvelope)
async def ingest_telemetry(telemetry: DroneTelemetry) -> PublishEnvelope:
    _latest_telemetry[telemetry.drone_id] = telemetry
    _drone_protocols[telemetry.drone_id] = telemetry.protocol
    metrics.increment("telemetry_received")
    zone = resolve_zone(telemetry.position)
    telemetry_payload = {
        **telemetry.model_dump(mode="json"),
        "coordinate_system": "WGS84",
        "zone": zone,
    }
    event = NormalizedEvent(
        event_type="drone.telemetry.received",
        source="drone-gateway",
        entity_id=telemetry.drone_id,
        timestamp=telemetry.timestamp,
        topic=DRONE_TELEMETRY_TOPIC,
        payload={
            **telemetry_payload,
            "security": build_secure_envelope(telemetry_payload, purpose="drone-telemetry", signer_id=telemetry.drone_id, associated=telemetry.drone_id),
        },
    )
    return PublishEnvelope(event=event, publish=get_publisher().publish_event(event))


def _validate_command(command: DroneCommand) -> None:
    if command.action.value == "move_to" and command.target is None:
        raise HTTPException(status_code=422, detail="move_to requires target")
    if command.action.value == "follow_path" and not command.path:
        raise HTTPException(status_code=422, detail="follow_path requires path")
    if command.action.value == "change_altitude" and command.altitude_m is None:
        raise HTTPException(status_code=422, detail="change_altitude requires altitude_m")
    if command.action.value in {"camera_zoom", "gimbal_move"} and command.camera_id is None:
        raise HTTPException(status_code=422, detail="camera actions require camera_id")


def _dispatch_command(command: DroneCommand) -> DroneCommandAck:
    _validate_command(command)

    command_id = str(uuid4())
    _commands[command_id] = command
    protocol = _drone_protocols.get(command.drone_id)
    capabilities = registry.get(command.drone_id)
    if protocol is None and capabilities is not None:
        protocol = capabilities.protocol
    try:
        adapter_status = adapter_for(protocol or "simulated").send_command(command)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    accepted = "accepted" in adapter_status
    metrics.increment("commands_accepted" if accepted else "commands_rejected")

    event = NormalizedEvent(
        event_id=command_id,
        event_type=f"drone.command.{command.action.value}",
        source="drone-gateway",
        entity_id=command.drone_id,
        topic=DRONE_EVENTS_TOPIC,
        payload={
            **command.model_dump(mode="json"),
            "adapter_status": adapter_status,
            "accepted": accepted,
            "security": build_secure_envelope(
                {**command.model_dump(mode="json"), "adapter_status": adapter_status, "accepted": accepted},
                purpose="drone-command",
                signer_id="drone-gateway",
                associated=command.drone_id,
            ),
        },
    )
    publish = get_publisher().publish_event(event)
    return DroneCommandAck(
        command_id=command_id,
        drone_id=command.drone_id,
        action=command.action,
        accepted=accepted,
        adapter_status=adapter_status,
        event=event,
        publish=publish,
    )


@app.post("/commands", response_model=DroneCommandAck)
async def send_command(command: DroneCommand) -> DroneCommandAck:
    return _dispatch_command(command)


@app.post("/drones/{drone_id}/commands", response_model=DroneCommandAck)
async def send_drone_command(drone_id: str, command: DroneCommand) -> DroneCommandAck:
    if command.drone_id != drone_id:
        raise HTTPException(status_code=422, detail="path drone_id must match command.drone_id")
    return _dispatch_command(command)


@app.get("/drones")
async def list_drones() -> dict[str, list[dict[str, object]]]:
    registry_drones = {item.drone_id: item.model_dump(mode="json") for item in registry.list()}
    return {
        "drones": [
            {
                **telemetry.model_dump(mode="json"),
                "capabilities": registry_drones.get(telemetry.drone_id),
            }
            for telemetry in _latest_telemetry.values()
        ],
        "registry": list(registry_drones.values()),
    }


@app.get("/topics")
async def topics() -> dict[str, str]:
    return SURVEILLANCE_TOPICS
