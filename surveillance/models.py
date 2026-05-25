"""
================================================================================
 File: surveillance/models.py
 Purpose:
   Shared domain schemas for SmartCito drone, sensor, camera, threat, and map
   surveillance services.
================================================================================
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DroneStatus(str, Enum):
    IDLE = "idle"
    IN_MISSION = "in_mission"
    HOVERING = "hovering"
    RETURNING = "returning"
    LANDED = "landed"
    ERROR = "error"


class DroneCommandAction(str, Enum):
    TAKEOFF = "takeoff"
    LAND = "land"
    MOVE_TO = "move_to"
    CHANGE_ALTITUDE = "change_altitude"
    FOLLOW_PATH = "follow_path"
    HOVER = "hover"
    RETURN_TO_BASE = "return_to_base"
    START_CAMERA_STREAM = "start_camera_stream"
    STOP_CAMERA_STREAM = "stop_camera_stream"
    CAMERA_ZOOM = "camera_zoom"
    GIMBAL_MOVE = "gimbal_move"


class DroneRegistryStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class ThreatLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GeoPoint(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    altitude_m: float | None = None


class NormalizedEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    source: str
    entity_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    topic: str
    payload: dict[str, Any]


class PublishResult(BaseModel):
    topic: str
    key: str
    published: bool
    status: str


class PublishEnvelope(BaseModel):
    event: NormalizedEvent
    publish: PublishResult


class DroneTelemetry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    drone_id: str = Field(..., min_length=2, max_length=80)
    protocol: str = Field(default="simulated", max_length=40)
    position: GeoPoint
    speed_mps: float = Field(default=0, ge=0)
    heading_deg: float = Field(default=0, ge=0, le=360)
    battery_percent: float = Field(..., ge=0, le=100)
    link_quality: float | None = Field(default=None, ge=0, le=1)
    flight_mode: str = Field(default="unknown", max_length=60)
    status: DroneStatus = DroneStatus.IDLE
    health_flags: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DroneCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    drone_id: str = Field(..., min_length=2, max_length=80)
    action: DroneCommandAction
    target: GeoPoint | None = None
    path: list[GeoPoint] = Field(default_factory=list)
    altitude_m: float | None = Field(default=None, ge=0)
    camera_id: str | None = Field(default=None, max_length=80)
    zoom_level: float | None = Field(default=None, ge=1, le=200)
    gimbal_pitch_deg: float | None = Field(default=None, ge=-90, le=45)
    gimbal_yaw_deg: float | None = Field(default=None, ge=-180, le=180)
    requested_by: str = Field(default="operator", max_length=80)

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: list[GeoPoint]) -> list[GeoPoint]:
        if len(value) > 200:
            raise ValueError("path cannot contain more than 200 waypoints")
        return value


class DroneConnectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    drone_id: str = Field(..., min_length=2, max_length=80)
    protocol: Literal["mavlink", "rest", "websocket", "vendor-sdk", "simulated"] = "simulated"
    endpoint: str | None = Field(default=None, max_length=300)
    auth_profile: str | None = Field(default=None, max_length=80)


class DroneCapabilities(BaseModel):
    model_config = ConfigDict(extra="forbid")

    drone_id: str = Field(..., min_length=2, max_length=80)
    model: str = Field(..., min_length=2, max_length=120)
    firmware_version: str = Field(..., min_length=1, max_length=80)
    max_speed_mps: float = Field(..., ge=0)
    max_altitude_m: float = Field(..., ge=0)
    battery_capacity_mah: int = Field(..., ge=0)
    camera_types: list[str] = Field(default_factory=list)
    sensors: list[str] = Field(default_factory=list)
    payload_supported: bool = False
    status: DroneRegistryStatus = DroneRegistryStatus.ONLINE
    protocol: str = Field(default="simulated", max_length=40)
    last_seen_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DroneCommandAck(BaseModel):
    command_id: str
    drone_id: str
    action: DroneCommandAction
    accepted: bool
    adapter_status: str
    event: NormalizedEvent
    publish: PublishResult


class RobotStatus(str, Enum):
    IDLE = "idle"
    PATROLLING = "patrolling"
    HOLDING = "holding"
    INSPECTING = "inspecting"
    DOCKING = "docking"
    OFFLINE = "offline"
    ERROR = "error"


class RobotCommandAction(str, Enum):
    MOVE_FORWARD = "move_forward"
    MOVE_REVERSE = "move_reverse"
    TURN_LEFT = "turn_left"
    TURN_RIGHT = "turn_right"
    HOLD = "hold"
    DOCK = "dock"
    SET_WAYPOINT = "set_waypoint"
    FOLLOW_ROUTE = "follow_route"


class RobotRegistryStatus(str, Enum):
    ONLINE = "online"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class RobotTelemetry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    robot_id: str = Field(..., min_length=2, max_length=80)
    protocol: str = Field(default="simulated", max_length=40)
    position: GeoPoint
    speed_mps: float = Field(default=0, ge=0)
    heading_deg: float = Field(default=0, ge=0, le=360)
    battery_percent: float = Field(..., ge=0, le=100)
    autonomy_state: str = Field(default="manual", max_length=60)
    status: RobotStatus = RobotStatus.IDLE
    slam_state: str = Field(default="mapping", max_length=60)
    health_flags: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RobotCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    robot_id: str = Field(..., min_length=2, max_length=80)
    action: RobotCommandAction
    target: GeoPoint | None = None
    path: list[GeoPoint] = Field(default_factory=list)
    requested_by: str = Field(default="operator", max_length=80)

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: list[GeoPoint]) -> list[GeoPoint]:
        if len(value) > 200:
            raise ValueError("path cannot contain more than 200 waypoints")
        return value


class RobotConnectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    robot_id: str = Field(..., min_length=2, max_length=80)
    protocol: Literal["rest", "websocket", "vendor-sdk", "simulated"] = "simulated"
    endpoint: str | None = Field(default=None, max_length=300)
    auth_profile: str | None = Field(default=None, max_length=80)


class RobotCapabilities(BaseModel):
    model_config = ConfigDict(extra="forbid")

    robot_id: str = Field(..., min_length=2, max_length=80)
    model: str = Field(..., min_length=2, max_length=120)
    firmware_version: str = Field(..., min_length=1, max_length=80)
    max_speed_mps: float = Field(..., ge=0)
    battery_capacity_mah: int = Field(..., ge=0)
    camera_ids: list[str] = Field(default_factory=list)
    sensors: list[str] = Field(default_factory=list)
    autonomy_modes: list[str] = Field(default_factory=list)
    lidar_supported: bool = True
    status: RobotRegistryStatus = RobotRegistryStatus.ONLINE
    protocol: str = Field(default="simulated", max_length=40)
    last_seen_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RobotCommandAck(BaseModel):
    command_id: str
    robot_id: str
    action: RobotCommandAction
    accepted: bool
    adapter_status: str
    event: NormalizedEvent
    publish: PublishResult


class RobotPatrolRoute(BaseModel):
    route_id: str = Field(default_factory=lambda: str(uuid4()))
    robot_id: str = Field(..., min_length=2, max_length=80)
    name: str = Field(..., min_length=3, max_length=120)
    status: Literal["draft", "assigned", "running", "paused", "completed"] = "assigned"
    checkpoints: list[str] = Field(default_factory=list)
    path: list[GeoPoint] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MissionStatus(str, Enum):
    DRAFT = "draft"
    UPLOADED = "uploaded"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class MissionAssetType(str, Enum):
    DRONE = "drone"
    ROBOT = "robot"


class CityMissionAssignmentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_type: MissionAssetType
    asset_id: str = Field(..., min_length=2, max_length=80)
    path: list[MissionWaypoint] = Field(..., min_length=2, max_length=200)
    altitude_m: float | None = Field(default=None, ge=0, le=500)
    speed_mps: float | None = Field(default=None, ge=0, le=40)


class CityMissionDispatchResult(BaseModel):
    asset_type: MissionAssetType
    asset_id: str
    accepted: bool
    adapter_status: str


class CityMissionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=3, max_length=120)
    operator_id: str = Field(default="mission-control", min_length=2, max_length=120)
    city: str = Field(..., min_length=2, max_length=80)
    district: str = Field(..., min_length=2, max_length=80)
    radius_km: float = Field(..., gt=0, le=100)
    assignments: list[CityMissionAssignmentIn] = Field(..., min_length=1, max_length=16)


class CityMission(BaseModel):
    mission_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=3, max_length=120)
    city: str = Field(..., min_length=2, max_length=80)
    district: str = Field(..., min_length=2, max_length=80)
    radius_km: float = Field(..., gt=0, le=100)
    status: MissionStatus = MissionStatus.DRAFT
    assignments: list[CityMissionAssignmentIn]
    dispatch_results: list[CityMissionDispatchResult] = Field(default_factory=list)
    integrity: dict[str, Any] | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MissionWaypoint(GeoPoint):
    hold_seconds: int | None = Field(default=None, ge=0, le=3600)


class MissionUploadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    drone_id: str = Field(..., min_length=2, max_length=80)
    name: str = Field(..., min_length=3, max_length=120)
    operator_id: str = Field(default="mission-control", min_length=2, max_length=120)
    altitude_m: float = Field(..., ge=20, le=500)
    speed_mps: float = Field(..., ge=1, le=40)
    waypoints: list[MissionWaypoint] = Field(..., min_length=2, max_length=200)


class MissionValidationResult(BaseModel):
    mission_id: str | None = None
    valid: bool
    status: MissionStatus = MissionStatus.DRAFT
    issues: list[str] = Field(default_factory=list)
    zones: list[str] = Field(default_factory=list)
    requires_operator_review: bool = False


class DroneMission(BaseModel):
    mission_id: str = Field(default_factory=lambda: str(uuid4()))
    drone_id: str = Field(..., min_length=2, max_length=80)
    name: str = Field(..., min_length=3, max_length=120)
    status: MissionStatus = MissionStatus.DRAFT
    altitude_m: float = Field(..., ge=20, le=500)
    speed_mps: float = Field(..., ge=1, le=40)
    progress_percent: float = Field(default=0, ge=0, le=100)
    waypoints: list[MissionWaypoint] = Field(..., min_length=2, max_length=200)
    validation: MissionValidationResult | None = None
    integrity: dict[str, Any] | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CameraDetection(BaseModel):
    label: str = Field(..., min_length=2, max_length=80)
    confidence: float = Field(..., ge=0, le=1)


class CameraGimbalState(BaseModel):
    pitch_deg: float = Field(default=0, ge=-90, le=45)
    yaw_deg: float = Field(default=0, ge=-180, le=180)
    zoom_level: float = Field(default=1, ge=1, le=200)


class CameraFeedStatus(BaseModel):
    drone_id: str = Field(..., min_length=2, max_length=80)
    stream_url: str = Field(..., min_length=5)
    preview_url: str | None = None
    camera_id: str = Field(default="rgb-main", min_length=2, max_length=80)
    ai_detections: list[CameraDetection] = Field(default_factory=list)
    gimbal: CameraGimbalState = Field(default_factory=CameraGimbalState)


class CameraStreamRegistration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    drone_id: str = Field(..., min_length=2, max_length=80)
    stream_url: str = Field(..., min_length=5)
    protocol: Literal["rtsp", "webrtc", "vendor"] = "rtsp"
    position: GeoPoint | None = None
    preview_enabled: bool = True


class FrameMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    drone_id: str = Field(..., min_length=2, max_length=80)
    frame_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    position: GeoPoint | None = None
    stream_url: str | None = None
    preview_url: str | None = None
    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)


class SensorReading(BaseModel):
    model_config = ConfigDict(extra="forbid")

    device_id: str = Field(..., min_length=2, max_length=80)
    sensor_type: str = Field(..., min_length=2, max_length=80)
    position: GeoPoint
    value: float
    unit: str = Field(..., min_length=1, max_length=24)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    alert: bool = False


class AIDetection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(..., min_length=2, max_length=80)
    source_type: Literal["drone_camera", "sensor", "gps", "historical"]
    label: str = Field(..., min_length=2, max_length=80)
    confidence: float = Field(..., ge=0, le=1)
    position: GeoPoint | None = None
    zone: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ThreatAlert(BaseModel):
    alert_id: str = Field(default_factory=lambda: str(uuid4()))
    threat_level: ThreatLevel
    title: str
    source_ids: list[str]
    position: GeoPoint | None = None
    zone: str | None = None
    confidence: float = Field(..., ge=0, le=1)
    recommended_actions: list[str]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MapOverlay(BaseModel):
    overlay_id: str
    overlay_type: Literal["drone", "sensor", "route", "geofence", "heatmap", "threat"]
    label: str
    position: GeoPoint | None = None
    path: list[GeoPoint] = Field(default_factory=list)
    intensity: float | None = Field(default=None, ge=0, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SurveillanceOverview(BaseModel):
    drones: list[MapOverlay]
    sensors: list[MapOverlay]
    threats: list[MapOverlay]
    geofences: list[MapOverlay]
