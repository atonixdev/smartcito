from __future__ import annotations

from hardware.drone_edge.schemas import DroneProfile, GeoPoint, TelemetrySample


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def build_drone_profile(
    *,
    drone_id: str,
    mavlink_endpoint: str,
    autopilot_payload: dict[str, object],
    autonomy_payload: dict[str, object] | None = None,
) -> DroneProfile:
    autonomy_payload = autonomy_payload or {}
    sensors = ["imu", "gps", "barometer", "magnetometer"]
    sensors.extend(str(sensor) for sensor in autonomy_payload.get("extra_sensors", []))

    camera_types = ["rgb"]
    if bool(autopilot_payload.get("thermal_camera", False)):
        camera_types.append("thermal")
    if bool(autopilot_payload.get("zoom_camera", False)):
        camera_types.append("zoom")

    return DroneProfile(
        drone_id=drone_id,
        model=str(autopilot_payload.get("model", "PX4 Companion Airframe")),
        firmware_version=str(autopilot_payload.get("firmware_version", "px4-unknown")),
        max_speed_mps=float(autopilot_payload.get("max_speed_mps", 18.0)),
        max_altitude_m=float(autopilot_payload.get("max_altitude_m", 500.0)),
        battery_capacity_mah=int(autopilot_payload.get("battery_capacity_mah", 6000)),
        camera_types=sorted(set(camera_types)),
        sensors=sorted(set(sensors + ["visual-odometry"] if autonomy_payload.get("visual_odometry", True) else sensors)),
        payload_supported=bool(autopilot_payload.get("payload_supported", True)),
        protocol="mavlink",
        endpoint=mavlink_endpoint,
        auth_profile=str(autonomy_payload.get("auth_profile", "drone-edge")),
    )


def normalize_mavlink_telemetry(
    *,
    drone_id: str,
    mavlink_payload: dict[str, object],
    protocol: str = "mavlink",
) -> TelemetrySample:
    battery_percent = _clamp(float(mavlink_payload.get("battery_remaining_pct", mavlink_payload.get("battery_percent", 0))), 0, 100)
    link_quality = mavlink_payload.get("link_quality")
    position = GeoPoint(
        latitude=float(mavlink_payload.get("latitude", 0.0)),
        longitude=float(mavlink_payload.get("longitude", 0.0)),
        altitude_m=float(mavlink_payload.get("altitude_m", mavlink_payload.get("relative_alt_m", 0.0))),
    )

    health_flags = [
        name
        for name, active in {
            "ekf_ok": bool(mavlink_payload.get("ekf_ok", True)),
            "gps_lock": bool(mavlink_payload.get("gps_lock", True)),
            "link_ok": bool(mavlink_payload.get("link_ok", True)),
        }.items()
        if not active
    ]

    return TelemetrySample(
        drone_id=drone_id,
        protocol=protocol,
        position=position,
        speed_mps=float(mavlink_payload.get("groundspeed_mps", mavlink_payload.get("speed_mps", 0.0))),
        heading_deg=float(mavlink_payload.get("heading_deg", 0.0)),
        battery_percent=battery_percent,
        link_quality=None if link_quality is None else _clamp(float(link_quality), 0, 1),
        flight_mode=str(mavlink_payload.get("flight_mode", "unknown")),
        status=str(mavlink_payload.get("status", "idle")),
        health_flags=health_flags,
    )