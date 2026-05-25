from datetime import UTC, datetime

import pytest

from surveillance.adapters import MavlinkDroneAdapter
from surveillance.models import DroneCommand, DroneConnectionRequest, GeoPoint


class _EnumEntry:
    def __init__(self, name: str) -> None:
        self.name = name


class _FakeHeartbeat:
    type = 2


class _FakeAutopilotVersion:
    flight_sw_version = (1 << 24) | (15 << 16) | (2 << 8)


class _FakeMav:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...]]] = []

    def command_long_send(self, *args: object) -> None:
        self.calls.append(("command_long_send", args))

    def set_position_target_global_int_send(self, *args: object) -> None:
        self.calls.append(("set_position_target_global_int_send", args))

    def mission_clear_all_send(self, *args: object) -> None:
        self.calls.append(("mission_clear_all_send", args))

    def mission_count_send(self, *args: object) -> None:
        self.calls.append(("mission_count_send", args))

    def mission_item_int_send(self, *args: object) -> None:
        self.calls.append(("mission_item_int_send", args))


class _FakeConnection:
    def __init__(self) -> None:
        self.target_system = 1
        self.target_component = 1
        self.mav = _FakeMav()
        self.messages = {
            "HEARTBEAT": _FakeHeartbeat(),
            "AUTOPILOT_VERSION": _FakeAutopilotVersion(),
            "ATTITUDE": object(),
            "LOCAL_POSITION_NED": object(),
        }

    def wait_heartbeat(self, timeout: float | None = None) -> object:
        return self.messages["HEARTBEAT"]


class _FakeMavlinkModule:
    MAV_CMD_NAV_TAKEOFF = 22
    MAV_CMD_NAV_LAND = 21
    MAV_CMD_NAV_RETURN_TO_LAUNCH = 20
    MAV_CMD_NAV_LOITER_UNLIM = 17
    MAV_CMD_DO_CHANGE_ALTITUDE = 186
    MAV_CMD_NAV_WAYPOINT = 16
    MAV_CMD_SET_CAMERA_ZOOM = 531
    MAV_CMD_DO_GIMBAL_MANAGER_PITCHYAW = 1000
    MAV_CMD_VIDEO_START_CAPTURE = 2500
    MAV_CMD_VIDEO_STOP_CAPTURE = 2501
    MAV_FRAME_GLOBAL_RELATIVE_ALT_INT = 6
    POSITION_TARGET_TYPEMASK_VX_IGNORE = 8
    POSITION_TARGET_TYPEMASK_VY_IGNORE = 16
    POSITION_TARGET_TYPEMASK_VZ_IGNORE = 32
    POSITION_TARGET_TYPEMASK_AX_IGNORE = 64
    POSITION_TARGET_TYPEMASK_AY_IGNORE = 128
    POSITION_TARGET_TYPEMASK_AZ_IGNORE = 256
    POSITION_TARGET_TYPEMASK_YAW_IGNORE = 1024
    POSITION_TARGET_TYPEMASK_YAW_RATE_IGNORE = 2048
    enums = {"MAV_TYPE": {2: _EnumEntry("MAV_TYPE_QUADROTOR")}}


class _FakeMavutil:
    mavlink = _FakeMavlinkModule()

    def __init__(self) -> None:
        self.connections: list[_FakeConnection] = []

    def mavlink_connection(self, endpoint: str, **_kwargs: object) -> _FakeConnection:
        connection = _FakeConnection()
        self.connections.append(connection)
        return connection


@pytest.fixture
def fake_mavutil(monkeypatch: pytest.MonkeyPatch) -> _FakeMavutil:
    fake = _FakeMavutil()
    monkeypatch.setattr("surveillance.adapters._load_mavutil", lambda: fake)
    return fake


def test_mavlink_adapter_discovers_capabilities(fake_mavutil: _FakeMavutil) -> None:
    adapter = MavlinkDroneAdapter()
    capabilities = adapter.discover_capabilities(
        DroneConnectionRequest(
            drone_id="drone-mav-001",
            protocol="mavlink",
            endpoint="udp://127.0.0.1:14540",
        )
    )

    assert capabilities.drone_id == "drone-mav-001"
    assert capabilities.protocol == "mavlink"
    assert capabilities.firmware_version == "1.15.2"
    assert "visual-odometry" in capabilities.sensors
    assert capabilities.model == "PX4 Mav Type Quadrotor"
    assert len(fake_mavutil.connections) == 1


def test_mavlink_adapter_sends_position_and_mission_commands(fake_mavutil: _FakeMavutil) -> None:
    adapter = MavlinkDroneAdapter()
    adapter.discover_capabilities(
        DroneConnectionRequest(
            drone_id="drone-mav-002",
            protocol="mavlink",
            endpoint="udp://127.0.0.1:14540",
        )
    )

    move_to_status = adapter.send_command(
        DroneCommand(
            drone_id="drone-mav-002",
            action="move_to",
            target=GeoPoint(latitude=-25.7454, longitude=28.2438, altitude_m=95),
            requested_by="test",
        )
    )
    patrol_status = adapter.send_command(
        DroneCommand(
            drone_id="drone-mav-002",
            action="follow_path",
            path=[
                GeoPoint(latitude=-25.7479, longitude=28.2293, altitude_m=95),
                GeoPoint(latitude=-25.7454, longitude=28.2438, altitude_m=95),
            ],
            requested_by="test",
        )
    )

    calls = fake_mavutil.connections[0].mav.calls
    assert move_to_status == "mavlink-command-accepted:move_to"
    assert patrol_status == "mavlink-command-accepted:follow_path"
    assert any(call[0] == "set_position_target_global_int_send" for call in calls)
    assert any(call[0] == "mission_count_send" for call in calls)


def test_drone_gateway_returns_validation_error_for_missing_mavlink_endpoint() -> None:
    adapter = MavlinkDroneAdapter()

    with pytest.raises(ValueError, match="mavlink connections require endpoint"):
        adapter.discover_capabilities(
            DroneConnectionRequest(
                drone_id="drone-mav-003",
                protocol="mavlink",
                endpoint=None,
            )
        )