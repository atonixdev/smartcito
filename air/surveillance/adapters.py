"""
================================================================================
 File: surveillance/adapters.py
 Purpose:
   Vendor-agnostic drone adapter contracts for the Drone Gateway. Real MAVLink,
   vendor SDK, REST, or WebSocket integrations plug in behind this interface;
   the gateway API remains stable for the rest of Orca.
================================================================================
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Protocol
from urllib.parse import parse_qs, urlparse

from surveillance.models import DroneCapabilities, DroneCommand, DroneConnectionRequest, DroneRegistryStatus


def _load_mavutil():
    try:
        from pymavlink import mavutil
    except ModuleNotFoundError:
        return None
    return mavutil


class DroneAdapter(Protocol):
    protocol: str

    def discover_capabilities(self, request: DroneConnectionRequest) -> DroneCapabilities:
        ...

    def send_command(self, command: DroneCommand) -> str:
        ...


class SimulatedDroneAdapter:
    protocol = "simulated"

    def discover_capabilities(self, request: DroneConnectionRequest) -> DroneCapabilities:
        return DroneCapabilities(
            drone_id=request.drone_id,
            model="Orca Simulated Patrol Drone",
            firmware_version="sim-1.0.0",
            max_speed_mps=18.0,
            max_altitude_m=500.0,
            battery_capacity_mah=6000,
            camera_types=["rgb", "thermal", "zoom"],
            sensors=["gps", "imu", "barometer", "magnetometer", "link-quality"],
            payload_supported=True,
            status=DroneRegistryStatus.ONLINE,
            protocol=self.protocol,
            last_seen_at=datetime.now(UTC),
        )

    def send_command(self, command: DroneCommand) -> str:
        return f"simulated-command-accepted:{command.action.value}"


class RestDroneAdapter(SimulatedDroneAdapter):
    protocol = "rest"


class MavlinkDroneAdapter(SimulatedDroneAdapter):
    protocol = "mavlink"

    def __init__(self) -> None:
        self._connections: dict[str, object] = {}
        self._endpoints: dict[str, str] = {}

    def _camera_types(self) -> list[str]:
        raw = os.getenv("ORCA_MAVLINK_CAMERA_TYPES", "rgb,thermal,zoom")
        return [item.strip() for item in raw.split(",") if item.strip()]

    def _resolve_endpoint(self, drone_id: str, endpoint: str | None) -> str:
        resolved = endpoint or self._endpoints.get(drone_id) or os.getenv("ORCA_MAVLINK_ENDPOINT")
        if not resolved:
            raise ValueError("mavlink connections require endpoint or ORCA_MAVLINK_ENDPOINT")
        return resolved

    def _open_connection(self, endpoint: str) -> object:
        mavutil = _load_mavutil()
        if mavutil is None:
            raise RuntimeError("pymavlink is unavailable")

        parsed = urlparse(endpoint)
        params = parse_qs(parsed.query)
        source_system = int(params.get("source_system", [255])[0])
        heartbeat_timeout = float(params.get("heartbeat_timeout", [2])[0])
        connection_target = endpoint
        connection_kwargs: dict[str, object] = {"source_system": source_system}

        if parsed.scheme == "serial":
            connection_target = parsed.path or parsed.netloc
            if not connection_target:
                raise ValueError("serial mavlink endpoint must include device path")
            if "baud" in params:
                connection_kwargs["baud"] = int(params["baud"][0])

        connection = mavutil.mavlink_connection(connection_target, **connection_kwargs)
        connection.wait_heartbeat(timeout=heartbeat_timeout)
        return connection

    def _connection_for(self, drone_id: str, endpoint: str | None = None) -> object:
        resolved_endpoint = self._resolve_endpoint(drone_id, endpoint)
        cached = self._connections.get(drone_id)
        if cached is not None and self._endpoints.get(drone_id) == resolved_endpoint:
            return cached

        connection = self._open_connection(resolved_endpoint)
        self._connections[drone_id] = connection
        self._endpoints[drone_id] = resolved_endpoint
        return connection

    def _firmware_version(self, connection: object) -> str:
        version_message = getattr(connection, "messages", {}).get("AUTOPILOT_VERSION")
        packed = getattr(version_message, "flight_sw_version", 0)
        if not packed:
            return "mavlink-live"
        major = (packed >> 24) & 0xFF
        minor = (packed >> 16) & 0xFF
        patch = (packed >> 8) & 0xFF
        return f"{major}.{minor}.{patch}"

    def _vehicle_model(self, connection: object) -> str:
        mavutil = _load_mavutil()
        heartbeat = getattr(connection, "messages", {}).get("HEARTBEAT")
        if mavutil is None or heartbeat is None:
            return "PX4 MAVLink Vehicle"
        enum_entry = getattr(mavutil.mavlink.enums.get("MAV_TYPE", {}), "get", lambda *_args, **_kwargs: None)(getattr(heartbeat, "type", None))
        if enum_entry is None:
            return "PX4 MAVLink Vehicle"
        return f"PX4 {enum_entry.name.replace('_', ' ').title()}"

    def discover_capabilities(self, request: DroneConnectionRequest) -> DroneCapabilities:
        connection = self._connection_for(request.drone_id, request.endpoint)
        sensors = ["gps", "imu", "barometer", "magnetometer", "link-quality"]
        if getattr(connection, "messages", {}).get("ATTITUDE") is not None:
            sensors.append("attitude")
        if getattr(connection, "messages", {}).get("LOCAL_POSITION_NED") is not None:
            sensors.append("visual-odometry")

        return DroneCapabilities(
            drone_id=request.drone_id,
            model=self._vehicle_model(connection),
            firmware_version=self._firmware_version(connection),
            max_speed_mps=float(os.getenv("ORCA_MAVLINK_MAX_SPEED_MPS", "20")),
            max_altitude_m=float(os.getenv("ORCA_MAVLINK_MAX_ALTITUDE_M", "500")),
            battery_capacity_mah=int(os.getenv("ORCA_MAVLINK_BATTERY_CAPACITY_MAH", "6000")),
            camera_types=self._camera_types(),
            sensors=sorted(set(sensors)),
            payload_supported=True,
            status=DroneRegistryStatus.ONLINE,
            protocol=self.protocol,
            last_seen_at=datetime.now(UTC),
        )

    def _target_ids(self, connection: object) -> tuple[int, int]:
        target_system = int(getattr(connection, "target_system", 1) or 1)
        target_component = int(getattr(connection, "target_component", 1) or 1)
        return target_system, target_component

    def _command_long(self, connection: object, command_id: int, *params: float) -> None:
        target_system, target_component = self._target_ids(connection)
        padded = list(params[:7]) + [0.0] * max(0, 7 - len(params))
        connection.mav.command_long_send(target_system, target_component, command_id, 0, *padded[:7])

    def _send_position_target(self, connection: object, command: DroneCommand) -> None:
        mavutil = _load_mavutil()
        if mavutil is None or command.target is None:
            raise RuntimeError("pymavlink position targeting unavailable")

        target_system, target_component = self._target_ids(connection)
        lat_int = int(command.target.latitude * 1e7)
        lon_int = int(command.target.longitude * 1e7)
        alt = float(command.target.altitude_m or command.altitude_m or 30)
        position_mask = int(
            mavutil.mavlink.POSITION_TARGET_TYPEMASK_VX_IGNORE
            | mavutil.mavlink.POSITION_TARGET_TYPEMASK_VY_IGNORE
            | mavutil.mavlink.POSITION_TARGET_TYPEMASK_VZ_IGNORE
            | mavutil.mavlink.POSITION_TARGET_TYPEMASK_AX_IGNORE
            | mavutil.mavlink.POSITION_TARGET_TYPEMASK_AY_IGNORE
            | mavutil.mavlink.POSITION_TARGET_TYPEMASK_AZ_IGNORE
            | mavutil.mavlink.POSITION_TARGET_TYPEMASK_YAW_IGNORE
            | mavutil.mavlink.POSITION_TARGET_TYPEMASK_YAW_RATE_IGNORE
        )
        connection.mav.set_position_target_global_int_send(
            0,
            target_system,
            target_component,
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
            position_mask,
            lat_int,
            lon_int,
            alt,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        )

    def _upload_mission_path(self, connection: object, command: DroneCommand) -> None:
        mavutil = _load_mavutil()
        if mavutil is None or not command.path:
            raise RuntimeError("pymavlink mission upload unavailable")

        target_system, target_component = self._target_ids(connection)
        connection.mav.mission_clear_all_send(target_system, target_component)
        connection.mav.mission_count_send(target_system, target_component, len(command.path))
        for index, waypoint in enumerate(command.path):
            connection.mav.mission_item_int_send(
                target_system,
                target_component,
                index,
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
                mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                1 if index == 0 else 0,
                1,
                float(getattr(waypoint, "hold_seconds", 0) or 0),
                0,
                0,
                0,
                int(waypoint.latitude * 1e7),
                int(waypoint.longitude * 1e7),
                float(waypoint.altitude_m or command.altitude_m or 30),
            )

    def send_command(self, command: DroneCommand) -> str:
        mavutil = _load_mavutil()
        if mavutil is None:
            raise RuntimeError("pymavlink is unavailable")

        connection = self._connection_for(command.drone_id)
        mavlink = mavutil.mavlink

        if command.action.value == "takeoff":
            self._command_long(connection, mavlink.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, 0, 0, 0, float(command.altitude_m or 30))
        elif command.action.value == "land":
            self._command_long(connection, mavlink.MAV_CMD_NAV_LAND)
        elif command.action.value == "return_to_base":
            self._command_long(connection, mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH)
        elif command.action.value == "hover":
            self._command_long(connection, mavlink.MAV_CMD_NAV_LOITER_UNLIM)
        elif command.action.value == "move_to":
            self._send_position_target(connection, command)
        elif command.action.value == "change_altitude":
            self._command_long(connection, getattr(mavlink, "MAV_CMD_DO_CHANGE_ALTITUDE", mavlink.MAV_CMD_NAV_WAYPOINT), float(command.altitude_m or 30))
        elif command.action.value == "follow_path":
            self._upload_mission_path(connection, command)
        elif command.action.value == "start_camera_stream":
            self._command_long(connection, getattr(mavlink, "MAV_CMD_VIDEO_START_CAPTURE", 2500), 0, 0, 0, 0, 1, 0, 0)
        elif command.action.value == "stop_camera_stream":
            self._command_long(connection, getattr(mavlink, "MAV_CMD_VIDEO_STOP_CAPTURE", 2501), 0, 0, 0, 0, 0, 0, 0)
        elif command.action.value == "camera_zoom":
            self._command_long(connection, getattr(mavlink, "MAV_CMD_SET_CAMERA_ZOOM", 531), 0, float(command.zoom_level or 1), 0, 0, 0, 0, 0)
        elif command.action.value == "gimbal_move":
            self._command_long(
                connection,
                getattr(mavlink, "MAV_CMD_DO_GIMBAL_MANAGER_PITCHYAW", 1000),
                float(command.gimbal_pitch_deg or 0),
                float(command.gimbal_yaw_deg or 0),
                0,
                0,
                0,
                0,
                0,
            )
        else:
            raise ValueError(f"unsupported mavlink command: {command.action.value}")

        return f"mavlink-command-accepted:{command.action.value}"


class WebSocketDroneAdapter(SimulatedDroneAdapter):
    protocol = "websocket"


class VendorSdkDroneAdapter(SimulatedDroneAdapter):
    protocol = "vendor-sdk"


_ADAPTERS: dict[str, DroneAdapter] = {
    "simulated": SimulatedDroneAdapter(),
    "rest": RestDroneAdapter(),
    "mavlink": MavlinkDroneAdapter(),
    "websocket": WebSocketDroneAdapter(),
    "vendor-sdk": VendorSdkDroneAdapter(),
}


def adapter_for(protocol: str) -> DroneAdapter:
    return _ADAPTERS.get(protocol, _ADAPTERS["simulated"])


def supported_protocols() -> list[str]:
    return sorted(_ADAPTERS)
