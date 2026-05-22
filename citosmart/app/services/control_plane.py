"""
================================================================================
 File: citosmart/app/services/control_plane.py
 Purpose:
   Aggregates SmartCito device, security, pipeline, and operator-control state
   for the dashboard control plane.
================================================================================
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import sys
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditEventORM
from app.schemas.control_plane import (
    ControlPlaneOverview,
    DataFlowStage,
    DeviceCategory,
    DeviceTrustLevel,
    MapDevice,
    MapDeviceRegistrationIn,
    MapHeatPoint,
    MapOverview,
    ManagedDevice,
    OperatorControl,
    OperatorControlState,
    PipelineState,
    SceneDevice,
    SceneOverview,
    SceneThreat,
    SecurityAlert,
    SecurityMonitorStatus,
)
from app.services.camera_registry import camera_registry_service

try:
    from hardware.usb_module.detector import detect_usb_devices
except ModuleNotFoundError:  # pragma: no cover - exercised in backend-only test environments
    repo_root = Path(__file__).resolve().parents[3]
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.append(repo_root_str)
    from hardware.usb_module.detector import detect_usb_devices


class ControlPlaneService:
    def __init__(self) -> None:
        self._controls: dict[str, OperatorControlState] = {
            "camera-service": OperatorControlState.RUNNING,
            "gps-service": OperatorControlState.RUNNING,
            "usb-service": OperatorControlState.RUNNING,
            "security-policies": OperatorControlState.RUNNING,
        }
        self._map_devices: dict[str, MapDevice] = {}

    async def overview(self, session: AsyncSession) -> ControlPlaneOverview:
        cameras = await camera_registry_service.list_devices(session)
        if not cameras:
            cameras = await camera_registry_service.seed_demo_devices(session)

        devices = [
            ManagedDevice(
                id=str(device.id),
                name=device.device_id,
                category=DeviceCategory.CAMERA,
                trust_level=(
                    DeviceTrustLevel.BLOCKED if device.tamper_detected else DeviceTrustLevel.VERIFIED
                ),
                driver_container="camera-service",
                endpoint=f"rtsp://fleet/{device.device_id}",
                firmware_version=device.firmware_version,
                authenticated=True,
                signed_driver=True,
                last_seen_at=device.last_seen_at,
            )
            for device in cameras
        ]

        devices.extend(
            ManagedDevice(
                id=usb.id,
                name=usb.name,
                category=DeviceCategory(usb.category),
                trust_level=DeviceTrustLevel(usb.trust_level),
                driver_container=usb.driver_container,
                endpoint=usb.endpoint,
                firmware_version=usb.firmware_version,
                authenticated=usb.authenticated,
                signed_driver=usb.signed_driver,
                last_seen_at=usb.last_seen_at,
            )
            for usb in detect_usb_devices()
        )

        alert_count = await session.scalar(
            select(func.count()).select_from(AuditEventORM).where(AuditEventORM.action.like("%telemetry%"))
        )
        alerts = [
            SecurityAlert(
                id="iam-baseline",
                severity="info",
                title="IAM token validation healthy",
                status="open",
            )
        ]
        if alert_count and alert_count > 1:
            alerts.append(
                SecurityAlert(
                    id="telemetry-watch",
                    severity="medium",
                    title="Recent device telemetry changes detected",
                    status="monitoring",
                )
            )

        security = SecurityMonitorStatus(
            encryption_status="quantum-ready hybrid envelope active",
            iam_status="rbac + jwt enforced",
            audit_pipeline_status="ci and api audit capture enabled",
            quantum_safe_status="ml-kem + qkd ingest ready",
            intrusion_alerts=alerts,
        )

        data_flow = [
            DataFlowStage(
                id="usb-adapter",
                name="USB and field adapters",
                protocol="udev / usb",
                state=PipelineState.HEALTHY,
                throughput_hint="event-driven",
                destination="device manager",
            ),
            DataFlowStage(
                id="camera-ingestion",
                name="Camera and RTSP ingest",
                protocol="onvif / rtsp",
                state=PipelineState.HEALTHY,
                throughput_hint="video + metadata",
                destination="kafka backbone",
            ),
            DataFlowStage(
                id="gps-flow",
                name="GPS and telemetry ingest",
                protocol="nmea / mqtt",
                state=PipelineState.HEALTHY,
                throughput_hint="low-latency telemetry",
                destination="postgres + dashboard",
            ),
            DataFlowStage(
                id="analytics",
                name="Analytics and persistence",
                protocol="kafka / spark / sql",
                state=PipelineState.HEALTHY,
                throughput_hint="streaming",
                destination="dashboards and audit",
            ),
        ]

        controls = [
            OperatorControl(
                id="camera-service",
                name="Camera Service",
                description="Handles camera ingestion and stream validation.",
                state=self._controls["camera-service"],
                policy_mode="strict",
                action_label=self._action_label(self._controls["camera-service"]),
            ),
            OperatorControl(
                id="gps-service",
                name="GPS Service",
                description="Normalizes GPS devices and secure NMEA ingestion.",
                state=self._controls["gps-service"],
                policy_mode="strict",
                action_label=self._action_label(self._controls["gps-service"]),
            ),
            OperatorControl(
                id="usb-service",
                name="USB Driver Service",
                description="Maps USB devices to containerized drivers and dashboard state.",
                state=self._controls["usb-service"],
                policy_mode="verified-only",
                action_label=self._action_label(self._controls["usb-service"]),
            ),
            OperatorControl(
                id="security-policies",
                name="Security Policies",
                description="Applies trust, IAM, and intrusion policy decisions.",
                state=self._controls["security-policies"],
                policy_mode="quantum-ready",
                action_label=self._action_label(self._controls["security-policies"]),
            ),
        ]

        return ControlPlaneOverview(
            devices=sorted(devices, key=self._last_seen_sort_key, reverse=True),
            security=security,
            data_flow=data_flow,
            controls=controls,
        )

    async def update_control(
        self,
        session: AsyncSession,
        *,
        control_id: str,
        desired_state: OperatorControlState,
        actor: str,
    ) -> OperatorControl | None:
        if control_id not in self._controls:
            return None

        self._controls[control_id] = desired_state
        session.add(
            AuditEventORM(
                id=str(uuid4()),
                entity_type="operator_control",
                entity_id=control_id,
                action="control-plane.operator-control.updated",
                actor=actor,
                payload={"desired_state": desired_state.value},
            )
        )
        await session.commit()

        overview = await self.overview(session)
        return next(control for control in overview.controls if control.id == control_id)

    async def map_overview(self, session: AsyncSession) -> MapOverview:
        cameras = await camera_registry_service.list_devices(session)
        if not cameras:
            cameras = await camera_registry_service.seed_demo_devices(session)

        devices: list[MapDevice] = []
        for index, device in enumerate(cameras):
            latitude, longitude = self._camera_location(device.location, index)
            trust_score = 0 if device.tamper_detected else 96
            if trust_score > 80:
                devices.append(
                    MapDevice(
                        id=str(device.id),
                        device_id=device.device_id,
                        name=device.device_id,
                        device_type=DeviceCategory.CAMERA,
                        latitude=latitude,
                        longitude=longitude,
                        trust_score=trust_score,
                        trust_level=DeviceTrustLevel.VERIFIED,
                        camera_feed_url=f"rtsp://fleet/{device.device_id}",
                        sensor_type="camera-feed",
                        sensor_value=device.battery_level,
                        gps_path=self._path_around(latitude, longitude),
                        last_seen_at=device.last_seen_at,
                    )
                )

        for index, usb in enumerate(detect_usb_devices()):
            trust_score = self._trust_score(DeviceTrustLevel(usb.trust_level))
            if trust_score > 80:
                latitude, longitude = self._usb_location(index)
                devices.append(
                    MapDevice(
                        id=usb.id,
                        device_id=usb.id,
                        name=usb.name,
                        device_type=DeviceCategory(usb.category),
                        latitude=latitude,
                        longitude=longitude,
                        trust_score=trust_score,
                        trust_level=DeviceTrustLevel(usb.trust_level),
                        camera_feed_url=None,
                        sensor_type="gps" if usb.category == "gps" else "iot-sensor",
                        sensor_value=0.68,
                        gps_path=self._path_around(latitude, longitude),
                        last_seen_at=usb.last_seen_at,
                    )
                )

        if "raspi-edge-001" not in self._map_devices:
            now = datetime.now(UTC)
            self._map_devices["raspi-edge-001"] = MapDevice(
                id="raspi-edge-001",
                device_id="raspi-edge-001",
                name="Raspberry Pi Edge Node",
                device_type=DeviceCategory.IOT,
                latitude=-25.7461,
                longitude=28.1881,
                trust_score=92,
                trust_level=DeviceTrustLevel.VERIFIED,
                camera_feed_url="rtsp://edge/raspi-edge-001/camera",
                sensor_type="air-quality",
                sensor_value=0.74,
                gps_path=[(-25.7472, 28.1868), (-25.7467, 28.1875), (-25.7461, 28.1881)],
                last_seen_at=now,
            )

        devices.extend(device for device in self._map_devices.values() if device.trust_score > 80)
        devices = sorted(devices, key=self._last_seen_sort_key, reverse=True)
        heatmap = [
            MapHeatPoint(
                latitude=device.latitude,
                longitude=device.longitude,
                intensity=min(max((device.sensor_value or 0.45), 0.15), 1),
                label=f"{device.name} {device.sensor_type}",
            )
            for device in devices
        ]

        return MapOverview(
            devices=devices,
            heatmap=heatmap,
            visible_layers=["verified-devices", "camera-overlays", "gps-paths", "sensor-heatmap"],
            security_policy="verified devices only; trust score must be greater than 80; registration and map updates are audited",
        )

    async def scene_overview(self, session: AsyncSession, *, actor: str) -> SceneOverview:
        map_overview = await self.map_overview(session)
        scene_devices = [self._scene_device(device) for device in map_overview.devices]
        threats = [
            SceneThreat(
                id=f"threat-{device.device_id}",
                x=device.x,
                y=0.04,
                z=device.z,
                severity="medium" if (device.sensor_value or 0) < 0.8 else "high",
                radius=1.7 + (device.sensor_value or 0.5),
                source_device_id=device.device_id,
                label=f"AI watch zone: {device.sensor_type}",
            )
            for device in scene_devices
            if (device.sensor_value or 0) >= 0.7 or device.device_type == DeviceCategory.CAMERA
        ]
        session.add(
            AuditEventORM(
                id=str(uuid4()),
                entity_type="dashboard_scene",
                entity_id="3d-control-plane",
                action="control-plane.scene.visualized",
                actor=actor,
                payload={
                    "device_count": len(scene_devices),
                    "threat_count": len(threats),
                    "policy": "jwt-rbac-and-trust-score",
                },
            )
        )
        await session.commit()
        return SceneOverview(
            devices=scene_devices,
            threats=threats,
            layers=["city-map", "iot-devices", "gps-paths", "camera-overlays", "threat-waves"],
            camera_overlay_mode="popup-texture-ready",
            security_policy="JWT + RBAC required; objects are color-coded by trust score and visible only after map trust policy validation",
        )

    async def register_map_device(
        self,
        session: AsyncSession,
        *,
        registration: MapDeviceRegistrationIn,
        actor: str,
    ) -> MapDevice:
        trust_level = self._trust_level(registration.trust_score)
        device = MapDevice(
            id=registration.device_id,
            device_id=registration.device_id,
            name=registration.name,
            device_type=registration.device_type,
            latitude=registration.latitude,
            longitude=registration.longitude,
            trust_score=registration.trust_score,
            trust_level=trust_level,
            camera_feed_url=registration.camera_feed_url,
            sensor_type=registration.sensor_type,
            sensor_value=registration.sensor_value,
            gps_path=self._path_around(registration.latitude, registration.longitude),
            last_seen_at=datetime.now(UTC),
        )
        self._map_devices[registration.device_id] = device
        session.add(
            AuditEventORM(
                id=str(uuid4()),
                entity_type="map_device",
                entity_id=registration.device_id,
                action="control-plane.map-device.registered",
                actor=actor,
                payload={
                    "trust_score": registration.trust_score,
                    "device_type": registration.device_type.value,
                    "mqtt_topic": registration.mqtt_topic,
                    "shown_on_map": registration.trust_score > 80,
                },
            )
        )
        await session.commit()
        return device

    def _action_label(self, state: OperatorControlState) -> str:
        return "stop" if state == OperatorControlState.RUNNING else "start"

    def _last_seen_sort_key(self, device: ManagedDevice | MapDevice) -> float:
        timestamp = device.last_seen_at
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)
        return timestamp.timestamp()

    def _trust_score(self, trust_level: DeviceTrustLevel) -> int:
        if trust_level == DeviceTrustLevel.VERIFIED:
            return 100
        if trust_level == DeviceTrustLevel.UNVERIFIED:
            return 50
        return 0

    def _trust_level(self, trust_score: int) -> DeviceTrustLevel:
        if trust_score > 80:
            return DeviceTrustLevel.VERIFIED
        if trust_score > 0:
            return DeviceTrustLevel.UNVERIFIED
        return DeviceTrustLevel.BLOCKED

    def _camera_location(self, location: dict[str, float] | None, index: int) -> tuple[float, float]:
        if location and "lat" in location and "lon" in location:
            return float(location["lat"]), float(location["lon"])
        demo_locations = [(-25.7479, 28.2293), (-26.2041, 28.0473)]
        return demo_locations[index % len(demo_locations)]

    def _usb_location(self, index: int) -> tuple[float, float]:
        demo_locations = [(-25.7469, 28.2299), (-25.7491, 28.2268)]
        return demo_locations[index % len(demo_locations)]

    def _path_around(self, latitude: float, longitude: float) -> list[tuple[float, float]]:
        return [
            (latitude - 0.0011, longitude - 0.0012),
            (latitude - 0.0004, longitude - 0.0005),
            (latitude, longitude),
        ]

    def _scene_device(self, device: MapDevice) -> SceneDevice:
        x_position, _, z_position = self._scene_coordinates(device.latitude, device.longitude)
        return SceneDevice(
            id=device.id,
            device_id=device.device_id,
            name=device.name,
            device_type=device.device_type,
            x=x_position,
            y=0.35,
            z=z_position,
            latitude=device.latitude,
            longitude=device.longitude,
            trust_score=device.trust_score,
            trust_level=device.trust_level,
            status_color=self._status_color(device.trust_score),
            camera_feed_url=device.camera_feed_url,
            sensor_type=device.sensor_type,
            sensor_value=device.sensor_value,
            gps_path_3d=[
                (*self._scene_coordinates(latitude, longitude),)
                for latitude, longitude in device.gps_path
            ],
        )

    def _scene_coordinates(self, latitude: float, longitude: float) -> tuple[float, float, float]:
        anchor_latitude = -25.7479
        anchor_longitude = 28.2293
        x_position = (longitude - anchor_longitude) * 180
        z_position = (latitude - anchor_latitude) * -180
        return x_position, 0.05, z_position

    def _status_color(self, trust_score: int) -> str:
        if trust_score > 80:
            return "#67d5a5"
        if trust_score > 0:
            return "#f1c96b"
        return "#f87171"


control_plane_service = ControlPlaneService()