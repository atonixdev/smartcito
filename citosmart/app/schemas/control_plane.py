"""
================================================================================
 File: citosmart/app/schemas/control_plane.py
 Purpose:
   Pydantic response and request models for the SmartCito dashboard control
   plane, including device manager, security monitor, pipeline flow, and
   operator control actions.
================================================================================
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class DeviceTrustLevel(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    BLOCKED = "blocked"


class DeviceCategory(str, Enum):
    USB = "usb"
    CAMERA = "camera"
    GPS = "gps"
    IOT = "iot"


class OperatorControlState(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    DEGRADED = "degraded"


class PipelineState(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    BLOCKED = "blocked"


class ManagedDevice(BaseModel):
    id: str
    name: str
    category: DeviceCategory
    trust_level: DeviceTrustLevel
    driver_container: str
    endpoint: str
    firmware_version: str
    authenticated: bool
    signed_driver: bool
    last_seen_at: datetime


class SecurityAlert(BaseModel):
    id: str
    severity: str
    title: str
    status: str


class SecurityMonitorStatus(BaseModel):
    encryption_status: str
    iam_status: str
    audit_pipeline_status: str
    quantum_safe_status: str
    intrusion_alerts: list[SecurityAlert]


class DataFlowStage(BaseModel):
    id: str
    name: str
    protocol: str
    state: PipelineState
    throughput_hint: str
    destination: str


class OperatorControl(BaseModel):
    id: str
    name: str
    description: str
    state: OperatorControlState
    policy_mode: str
    action_label: str


class OperatorControlUpdateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    desired_state: OperatorControlState = Field(...)


class MapDeviceRegistrationIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    device_id: str = Field(..., min_length=3, max_length=80)
    device_type: DeviceCategory
    name: str = Field(..., min_length=3, max_length=120)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    trust_score: int = Field(..., ge=0, le=100)
    camera_feed_url: str | None = None
    sensor_type: str = Field(default="edge-node", max_length=80)
    sensor_value: float | None = None
    mqtt_topic: str | None = None


class MapDevice(BaseModel):
    id: str
    device_id: str
    name: str
    device_type: DeviceCategory
    latitude: float
    longitude: float
    trust_score: int
    trust_level: DeviceTrustLevel
    camera_feed_url: str | None = None
    sensor_type: str
    sensor_value: float | None = None
    gps_path: list[tuple[float, float]]
    last_seen_at: datetime


class MapHeatPoint(BaseModel):
    latitude: float
    longitude: float
    intensity: float = Field(..., ge=0, le=1)
    label: str


class MapOverview(BaseModel):
    devices: list[MapDevice]
    heatmap: list[MapHeatPoint]
    visible_layers: list[str]
    security_policy: str


class SceneDevice(BaseModel):
    id: str
    device_id: str
    name: str
    device_type: DeviceCategory
    x: float
    y: float
    z: float
    latitude: float
    longitude: float
    trust_score: int
    trust_level: DeviceTrustLevel
    status_color: str
    camera_feed_url: str | None = None
    sensor_type: str
    sensor_value: float | None = None
    gps_path_3d: list[tuple[float, float, float]]


class SceneThreat(BaseModel):
    id: str
    x: float
    y: float
    z: float
    severity: str
    radius: float
    source_device_id: str
    label: str


class SceneOverview(BaseModel):
    devices: list[SceneDevice]
    threats: list[SceneThreat]
    layers: list[str]
    camera_overlay_mode: str
    security_policy: str


class ControlPlaneOverview(BaseModel):
    devices: list[ManagedDevice]
    security: SecurityMonitorStatus
    data_flow: list[DataFlowStage]
    controls: list[OperatorControl]