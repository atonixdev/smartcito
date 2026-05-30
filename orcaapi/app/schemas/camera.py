"""
================================================================================
 File: orcaapi/app/schemas/camera.py
 Purpose:
   Pydantic models for Orca camera registration and telemetry.

   These schemas define the wire contract for hardware devices and the
   dashboard/API consumers that need camera fleet state.
================================================================================
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class CameraDeviceType(str, Enum):
    """Supported camera device categories."""

    BODY_CAMERA = "body_camera"
    MICRO_CAMERA = "micro_camera"


class StreamProtocol(str, Enum):
    """Protocols Orca accepts for camera media/control."""

    ONVIF = "onvif"
    RTSP = "rtsp"
    HTTP2 = "http2"
    WEBRTC = "webrtc"


class NetworkTransport(str, Enum):
    """Network transports supported by the hardware fleet."""

    LTE = "lte"
    FIVE_G = "5g"
    WIFI6 = "wifi6"
    ETHERNET = "ethernet"


class SignalProfile(str, Enum):
    """Mobility profile for device connectivity."""

    MOBILE = "mobile"
    FIXED = "fixed"
    HYBRID = "hybrid"


class IdentityMode(str, Enum):
    """Supported device identity mechanisms."""

    SHARED_SECRET = "device_secret"  # nosec B105
    CERTIFICATE = "certificate"
    SECURE_ELEMENT = "secure_element"


class MountSensorType(str, Enum):
    """Sensor choices for magnetic mount detection."""

    HALL_EFFECT = "hall_effect"
    REED_SWITCH = "reed_switch"
    NONE = "none"


class StreamStatus(str, Enum):
    """Lifecycle state of a registered camera stream."""

    OFFLINE = "offline"
    CONNECTING = "connecting"
    LIVE = "live"
    DEGRADED = "degraded"


class CameraCapabilities(BaseModel):
    """Device feature declaration provided at registration time."""

    model_config = ConfigDict(extra="forbid")

    gps: bool
    tamper_detection: bool
    mount_detection: bool
    stream_protocols: list[StreamProtocol] = Field(min_length=1)
    local_encrypted_storage: bool = False


class CameraNetwork(BaseModel):
    """Transport details used by the hardware unit."""

    model_config = ConfigDict(extra="forbid")

    transport: NetworkTransport
    signal_profile: SignalProfile


class CameraSecurity(BaseModel):
    """Security controls the device promises to enforce."""

    model_config = ConfigDict(extra="forbid")

    identity_mode: IdentityMode
    tls_required: bool = True
    storage_encryption: str = Field("aes-256", pattern="^aes-256$")


class CameraMounting(BaseModel):
    """Optional mount and magnetic sensor metadata."""

    model_config = ConfigDict(extra="forbid")

    magnetic_base: bool = False
    mount_sensor_type: MountSensorType = MountSensorType.NONE


class CameraLocation(BaseModel):
    """Latest known location snapshot for a camera."""

    model_config = ConfigDict(extra="forbid")

    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    accuracy_m: float | None = Field(None, ge=0)


class CameraRegistrationIn(BaseModel):
    """Registration payload posted by a hardware device or fleet manager."""

    model_config = ConfigDict(extra="forbid")

    device_id: str = Field(..., min_length=3, max_length=128)
    device_type: CameraDeviceType
    firmware_version: str = Field(..., min_length=1, max_length=64)
    capabilities: CameraCapabilities
    network: CameraNetwork
    security: CameraSecurity
    mounting: CameraMounting = Field(default_factory=CameraMounting)


class CameraTelemetryIn(BaseModel):
    """Periodic state update from a registered camera."""

    model_config = ConfigDict(extra="forbid")

    stream_status: StreamStatus
    location: CameraLocation | None = None
    battery_level: int | None = Field(None, ge=0, le=100)
    mounted: bool | None = None
    tamper_detected: bool = False


class CameraDeviceOut(CameraRegistrationIn):
    """Camera device record as returned to API consumers."""

    id: UUID = Field(default_factory=uuid4)
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)
    stream_status: StreamStatus = StreamStatus.OFFLINE
    location: CameraLocation | None = None
    battery_level: int | None = None
    mounted: bool | None = None
    tamper_detected: bool = False
