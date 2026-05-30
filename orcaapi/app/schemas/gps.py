"""
================================================================================
 File: orcaapi/app/schemas/gps.py
 Purpose:
   Wire-format schemas for GPS ingestion and read APIs.
================================================================================
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class GPSPointIn(BaseModel):
    """Incoming GPS point from a tracker, drone, or edge device."""

    model_config = ConfigDict(extra="forbid")

    device_id: str = Field(..., min_length=3, max_length=128, examples=["drone-001"])
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    speed: float | None = Field(None, ge=0)
    heading: float | None = Field(None, ge=0, le=360)
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GPSPointOut(GPSPointIn):
    """GPS point as persisted by the platform."""

    id: int
    received_at: datetime


class GPSFleetLiveResponse(BaseModel):
    """Latest known position for currently active devices."""

    active_within_minutes: int
    devices: list[GPSPointOut]


GPSDashboardChannel = Literal["global", "drone", "robot", "city", "mission", "individualization"]
GPSDeviceType = Literal["drone", "robot", "vehicle", "sensor", "camera", "iot", "unknown"]


class GPSGatewayIn(BaseModel):
    """Gateway payload accepted from any GPS-enabled platform device."""

    model_config = ConfigDict(extra="forbid")

    device_id: str = Field(..., min_length=3, max_length=128, examples=["orca_unit_01"])
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    altitude: float | None = Field(default=None)
    speed: float | None = Field(default=None, ge=0)
    heading: float | None = Field(default=None, ge=0, le=360)
    timestamp: int | datetime = Field(..., description="Unix epoch seconds or ISO datetime")
    name: str | None = Field(default=None, max_length=160)
    device_type: GPSDeviceType = Field(default="unknown")
    icon: str | None = Field(default=None, max_length=64)
    color: str | None = Field(default=None, max_length=32)
    status: str | None = Field(default=None, max_length=64)


class GPSLiveDevice(BaseModel):
    """Live device state sent to realtime map dashboards."""

    device_id: str
    channel: GPSDashboardChannel
    device_type: GPSDeviceType
    name: str
    icon: str
    color: str
    status: str
    latitude: float
    longitude: float
    altitude: float
    speed: float
    heading: float
    timestamp: datetime


class GPSStreamMessage(BaseModel):
    """WebSocket frame payload for live GPS dashboards."""

    type: Literal["gps.snapshot", "gps.update", "gps.heartbeat"]
    channel: GPSDashboardChannel
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    devices: list[GPSLiveDevice] = Field(default_factory=list)
