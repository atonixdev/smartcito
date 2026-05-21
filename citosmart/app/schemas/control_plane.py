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


class ControlPlaneOverview(BaseModel):
    devices: list[ManagedDevice]
    security: SecurityMonitorStatus
    data_flow: list[DataFlowStage]
    controls: list[OperatorControl]