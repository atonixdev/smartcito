"""
================================================================================
 File: surveillance/mission_control_service.py
 Purpose:
   Mission Control Service for Orca. It validates patrol routes, tracks
   mission lifecycle, uploads missions through Drone Gateway, and exposes a
   monitoring-friendly API for the operator dashboard.
================================================================================
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from urllib import error, request

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from orca_shared.crypto import build_integrity_record, build_secure_envelope
from pydantic import BaseModel, Field

try:
    from surveillance.geospatial import evaluate_geofence_activity, resolve_zone, route_mission
except ModuleNotFoundError:
    def resolve_zone(_position):  # type: ignore[no-redef]
        return {
            "zone_id": "zone-unknown",
            "zone_name": "Fallback Zone",
            "zone_type": "geofence",
            "criticality": "medium",
            "contains": True,
            "distance_to_boundary_m": None,
            "point": None,
        }

    def evaluate_geofence_activity(_position, previous_position=None, path=None):  # type: ignore[no-redef]
        return {"violations": [], "entries": []}

    def route_mission(origin, destinations, extra_obstacles=None):  # type: ignore[no-redef]
        destination = destinations[0]
        origin_dump = origin.model_dump(mode="json") if hasattr(origin, "model_dump") else dict(origin)
        destination_dump = destination.model_dump(mode="json") if hasattr(destination, "model_dump") else dict(destination)
        return {"path": [origin_dump, destination_dump]}
from surveillance.kafka import get_publisher
from surveillance.models import (
    CityMissionAssignmentIn,
    CityMission,
    CityMissionDispatchResult,
    CityMissionRequest,
    DroneMission,
    GeoPoint,
    MissionAssetType,
    MissionStatus,
    MissionUploadRequest,
    MissionValidationResult,
    MissionWaypoint,
    NormalizedEvent,
)
from surveillance.topics import DRONE_EVENTS_TOPIC, DRONE_MISSIONS_TOPIC, ROBOT_EVENTS_TOPIC


load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

app = FastAPI(title="Orca Mission Control Service")
_missions: dict[str, DroneMission] = {}
_city_missions: dict[str, CityMission] = {}


class SurveillanceDispatchRequest(BaseModel):
    robot_id: str = Field(..., min_length=2, max_length=80)
    threat_level: str = Field(default="low")
    reaction_action: str = Field(default="continue_route")
    environment: str = Field(default="urban")
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    operator_id: str = Field(default="mission-control", min_length=2, max_length=120)


def _gateway_base_url() -> str:
    return os.getenv("DRONE_GATEWAY_URL", "http://drone-gateway:8020").rstrip("/")


def _robot_gateway_base_url() -> str:
    return os.getenv("ROBOT_GATEWAY_URL", "http://robot-gateway:8026").rstrip("/")


def _validate(request_payload: MissionUploadRequest, *, mission_id: str | None = None) -> MissionValidationResult:
    issues: list[str] = []
    zones: list[str] = []
    requires_operator_review = False

    for index, waypoint in enumerate(request_payload.waypoints, start=1):
        zone = resolve_zone(waypoint)
        zones.append(str(zone["zone_id"] or "outside-managed-zones"))
        if zone["criticality"] == "critical":
            requires_operator_review = True
            issues.append(f"waypoint {index} enters critical zone {zone['zone_id']}")

    for index, (previous_waypoint, current_waypoint) in enumerate(zip(request_payload.waypoints, request_payload.waypoints[1:]), start=2):
        segment_activity = evaluate_geofence_activity(
            current_waypoint,
            previous_position=previous_waypoint,
            path=[previous_waypoint, current_waypoint],
        )
        if segment_activity["violations"]:
            requires_operator_review = True
            issues.append(
                f"path segment {index - 1}->{index} intersects restricted zones: {', '.join(segment_activity['violations'])}"
            )
        zones.extend(segment_activity["entries"])

    unique_zones = sorted(set(zones))
    if request_payload.altitude_m > 120:
        requires_operator_review = True
        issues.append("mission altitude exceeds standard patrol ceiling of 120m")
    if request_payload.speed_mps > 20:
        issues.append("mission speed exceeds standard patrol profile of 20 m/s")
    if len(unique_zones) > 3:
        requires_operator_review = True
        issues.append("mission crosses multiple managed zones and requires review")

    return MissionValidationResult(
        mission_id=mission_id,
        valid=not issues,
        status=MissionStatus.DRAFT,
        issues=issues,
        zones=unique_zones,
        requires_operator_review=requires_operator_review,
    )


def _upload_to_gateway(mission: DroneMission) -> str:
    routed_path = _route_path(mission.waypoints)
    payload = {
        "drone_id": mission.drone_id,
        "action": "follow_path",
        "path": [waypoint.model_dump(mode="json", exclude_none=True) for waypoint in routed_path],
        "requested_by": "mission-control",
    }
    body = json.dumps(payload).encode("utf-8")
    gateway_request = request.Request(
        url=f"{_gateway_base_url()}/drones/{mission.drone_id}/commands",
        data=body,
        headers={"content-type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(gateway_request, timeout=5) as response:
            response_body = json.loads(response.read().decode("utf-8") or "{}")
    except error.URLError as exc:
        return f"gateway-unavailable:{exc.reason}"
    except Exception as exc:  # pragma: no cover - defensive fallback for remote gateway issues
        return f"gateway-failed:{exc.__class__.__name__}"

    if response_body.get("accepted") is True:
        return "uploaded"
    return str(response_body.get("adapter_status", "gateway-rejected"))


def _mission_integrity_payload(mission: DroneMission | CityMission, operator_id: str) -> dict[str, object]:
    return {
        "mission_id": mission.mission_id,
        "name": mission.name,
        "operator_id": operator_id,
        "status": mission.status.value,
        "created_at": mission.created_at.isoformat(),
        "updated_at": mission.updated_at.isoformat(),
        "body": mission.model_dump(mode="json", exclude={"integrity"}),
    }


def _attach_mission_integrity(mission: DroneMission | CityMission, operator_id: str) -> None:
    signable = _mission_integrity_payload(mission, operator_id)
    mission.integrity = {
        **build_integrity_record(signable, signer_id=operator_id),
        "envelope": build_secure_envelope(signable, purpose="mission-file", signer_id=operator_id, associated=mission.mission_id),
    }


def _publish_mission_event(mission: DroneMission, event_type: str, upload_status: str) -> dict[str, object]:
    mission_payload = {
        **mission.model_dump(mode="json"),
        "upload_status": upload_status,
    }
    event = NormalizedEvent(
        event_type=event_type,
        source="mission-control",
        entity_id=mission.mission_id,
        topic=DRONE_MISSIONS_TOPIC,
        payload={
            **mission_payload,
            "security": build_secure_envelope(mission_payload, purpose="mission-event", signer_id="mission-control", associated=mission.mission_id),
        },
    )
    publish = get_publisher().publish_event(event)
    control_event = NormalizedEvent(
        event_type=f"mission.control.{mission.status.value}",
        source="mission-control",
        entity_id=mission.drone_id,
        topic=DRONE_EVENTS_TOPIC,
        payload={
            "mission_id": mission.mission_id,
            "drone_id": mission.drone_id,
            "status": mission.status.value,
            "upload_status": upload_status,
        },
    )
    get_publisher().publish_event(control_event)
    return {"event": event.model_dump(mode="json"), "publish": publish.model_dump(mode="json")}


def _dispatch_city_assignment(assignment: CityMissionRequest) -> CityMissionDispatchResult:  # type: ignore[type-arg]
    raise RuntimeError("unreachable helper signature")


def _route_path(path: list[object]) -> list[object]:
    if len(path) < 2:
        return path

    routed_path: list[object] = [path[0]]
    current_waypoint = path[0]
    for next_waypoint in path[1:]:
        try:
            route = route_mission(current_waypoint, [next_waypoint])
            route_points = route.get("path", [])
        except Exception:
            route_points = []

        if route_points:
            segment_points = [
                next_waypoint.__class__(**route_point)
                for route_point in route_points
            ]
            routed_path.extend(segment_points[1:] if len(segment_points) > 1 else segment_points)
        else:
            routed_path.append(next_waypoint)
        current_waypoint = next_waypoint

    return routed_path


def _dispatch_assignment_payload(asset_type: MissionAssetType, asset_id: str, path: list[object]) -> tuple[str, dict[str, object]]:
    if asset_type == MissionAssetType.DRONE:
        return (
            f"{_gateway_base_url()}/drones/{asset_id}/commands",
            {
                "drone_id": asset_id,
                "action": "follow_path",
                "path": path,
                "requested_by": "mission-control",
            },
        )

    return (
        f"{_robot_gateway_base_url()}/robots/{asset_id}/commands",
        {
            "robot_id": asset_id,
            "action": "follow_route",
            "path": path,
            "requested_by": "mission-control",
        },
    )


def _dispatch_city_mission(mission: CityMission) -> list[CityMissionDispatchResult]:
    dispatch_results: list[CityMissionDispatchResult] = []
    for assignment in mission.assignments:
        routed_path = _route_path(assignment.path)
        url, payload = _dispatch_assignment_payload(
            assignment.asset_type,
            assignment.asset_id,
            [waypoint.model_dump(mode="json", exclude_none=True) for waypoint in routed_path],
        )
        gateway_request = request.Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"content-type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(gateway_request, timeout=5) as response:
                response_body = json.loads(response.read().decode("utf-8") or "{}")
        except error.URLError as exc:
            dispatch_results.append(
                CityMissionDispatchResult(
                    asset_type=assignment.asset_type,
                    asset_id=assignment.asset_id,
                    accepted=False,
                    adapter_status=f"gateway-unavailable:{exc.reason}",
                )
            )
            continue
        except Exception as exc:  # pragma: no cover - defensive fallback for remote gateway issues
            dispatch_results.append(
                CityMissionDispatchResult(
                    asset_type=assignment.asset_type,
                    asset_id=assignment.asset_id,
                    accepted=False,
                    adapter_status=f"gateway-failed:{exc.__class__.__name__}",
                )
            )
            continue

        dispatch_results.append(
            CityMissionDispatchResult(
                asset_type=assignment.asset_type,
                asset_id=assignment.asset_id,
                accepted=response_body.get("accepted") is True,
                adapter_status=str(response_body.get("adapter_status", "gateway-rejected")),
            )
        )
    return dispatch_results


def _publish_city_mission_event(mission: CityMission) -> None:
    mission_payload = mission.model_dump(mode="json")
    mission_event = NormalizedEvent(
        event_type=f"city-mission.{mission.status.value}",
        source="mission-control",
        entity_id=mission.mission_id,
        topic=DRONE_MISSIONS_TOPIC,
        payload={
            **mission_payload,
            "security": build_secure_envelope(mission_payload, purpose="city-mission-event", signer_id="mission-control", associated=mission.mission_id),
        },
    )
    get_publisher().publish_event(mission_event)

    for result in mission.dispatch_results:
        asset_event = NormalizedEvent(
            event_type=f"city-mission.dispatch.{result.asset_type.value}",
            source="mission-control",
            entity_id=result.asset_id,
            topic=DRONE_EVENTS_TOPIC if result.asset_type == MissionAssetType.DRONE else ROBOT_EVENTS_TOPIC,
            payload={"mission_id": mission.mission_id, **result.model_dump(mode="json")},
        )
        get_publisher().publish_event(asset_event)


def _reactive_patrol_points(request_payload: SurveillanceDispatchRequest) -> list[MissionWaypoint]:
    center = GeoPoint(
        latitude=request_payload.latitude if request_payload.latitude is not None else -25.7460,
        longitude=request_payload.longitude if request_payload.longitude is not None else 28.2360,
        altitude_m=0,
    )
    return [
        MissionWaypoint(latitude=center.latitude, longitude=center.longitude, altitude_m=0),
        MissionWaypoint(latitude=center.latitude + 0.0007, longitude=center.longitude + 0.0006, altitude_m=0),
        MissionWaypoint(latitude=center.latitude + 0.0011, longitude=center.longitude + 0.0001, altitude_m=0),
    ]


def _build_reactive_city_mission(request_payload: SurveillanceDispatchRequest) -> CityMission:
    route = _reactive_patrol_points(request_payload)
    assignments: list[CityMissionAssignmentIn] = [
        CityMissionAssignmentIn(
            asset_type=MissionAssetType.ROBOT,
            asset_id=request_payload.robot_id,
            path=route,
            speed_mps=1.5,
        )
    ]

    if request_payload.threat_level.lower() in {"high", "critical"}:
        assignments.append(
            CityMissionAssignmentIn(
                asset_type=MissionAssetType.DRONE,
                asset_id="drone-safe-001",
                path=route,
                altitude_m=90,
                speed_mps=8,
            )
        )

    mission = CityMission(
        name=f"Reactive surveillance dispatch ({request_payload.threat_level.lower()})",
        city="SmartCito",
        district=request_payload.environment,
        radius_km=3,
        assignments=assignments,
    )
    _attach_mission_integrity(mission, request_payload.operator_id)
    mission.dispatch_results = _dispatch_city_mission(mission)
    mission.status = MissionStatus.UPLOADED if any(result.accepted for result in mission.dispatch_results) else MissionStatus.FAILED
    mission.updated_at = datetime.now(UTC)
    _city_missions[mission.mission_id] = mission
    _publish_city_mission_event(mission)
    return mission


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "mission-control"}


@app.get("/ready")
async def ready() -> dict[str, object]:
    return {
        "service": "mission-control",
        "topics": {"missions": DRONE_MISSIONS_TOPIC, "events": DRONE_EVENTS_TOPIC},
        "gateway": _gateway_base_url(),
        "mission_count": len(_missions),
    }


@app.post("/missions/validate", response_model=MissionValidationResult)
async def validate_mission(request_payload: MissionUploadRequest) -> MissionValidationResult:
    return _validate(request_payload)


@app.get("/missions", response_model=list[DroneMission])
async def list_missions() -> list[DroneMission]:
    return sorted(_missions.values(), key=lambda mission: mission.updated_at, reverse=True)


@app.get("/missions/{mission_id}", response_model=DroneMission)
async def get_mission(mission_id: str) -> DroneMission:
    mission = _missions.get(mission_id)
    if mission is None:
        raise HTTPException(status_code=404, detail="mission not found")
    return mission


@app.post("/missions", response_model=DroneMission)
async def create_mission(request_payload: MissionUploadRequest) -> DroneMission:
    mission = DroneMission(
        drone_id=request_payload.drone_id,
        name=request_payload.name,
        altitude_m=request_payload.altitude_m,
        speed_mps=request_payload.speed_mps,
        waypoints=request_payload.waypoints,
    )
    _attach_mission_integrity(mission, request_payload.operator_id)
    validation = _validate(request_payload, mission_id=mission.mission_id)
    if validation.requires_operator_review:
        mission.validation = validation
        mission.updated_at = datetime.now(UTC)
        _missions[mission.mission_id] = mission
        _publish_mission_event(mission, "mission.review_required", "review-required")
        return mission

    upload_status = _upload_to_gateway(mission)
    mission.status = MissionStatus.UPLOADED if upload_status == "uploaded" else MissionStatus.FAILED
    mission.progress_percent = 5 if mission.status == MissionStatus.UPLOADED else 0
    mission.validation = validation.model_copy(update={"status": mission.status})
    mission.updated_at = datetime.now(UTC)
    _missions[mission.mission_id] = mission
    _publish_mission_event(mission, "mission.uploaded" if mission.status == MissionStatus.UPLOADED else "mission.upload_failed", upload_status)
    return mission


@app.post("/missions/{mission_id}/status", response_model=DroneMission)
async def update_mission_status(mission_id: str, status: MissionStatus, progress_percent: float | None = None) -> DroneMission:
    mission = _missions.get(mission_id)
    if mission is None:
        raise HTTPException(status_code=404, detail="mission not found")

    mission.status = status
    if progress_percent is not None:
        mission.progress_percent = progress_percent
    elif status == MissionStatus.COMPLETED:
        mission.progress_percent = 100
    mission.updated_at = datetime.now(UTC)
    _publish_mission_event(mission, "mission.status.updated", "operator-update")
    return mission


@app.get("/city-missions", response_model=list[CityMission])
async def list_city_missions() -> list[CityMission]:
    return sorted(_city_missions.values(), key=lambda mission: mission.updated_at, reverse=True)


@app.post("/city-missions", response_model=CityMission)
async def create_city_mission(request_payload: CityMissionRequest) -> CityMission:
    mission = CityMission(
        name=request_payload.name,
        city=request_payload.city,
        district=request_payload.district,
        radius_km=request_payload.radius_km,
        assignments=request_payload.assignments,
    )
    _attach_mission_integrity(mission, request_payload.operator_id)
    mission.dispatch_results = _dispatch_city_mission(mission)
    mission.status = MissionStatus.UPLOADED if any(result.accepted for result in mission.dispatch_results) else MissionStatus.FAILED
    mission.updated_at = datetime.now(UTC)
    _city_missions[mission.mission_id] = mission
    _publish_city_mission_event(mission)
    return mission


@app.post("/surveillance/dispatch", response_model=CityMission)
async def dispatch_from_surveillance(request_payload: SurveillanceDispatchRequest) -> CityMission:
    return _build_reactive_city_mission(request_payload)