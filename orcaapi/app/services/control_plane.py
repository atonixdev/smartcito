"""
================================================================================
 File: orcaapi/app/services/control_plane.py
 Purpose:
   Aggregates Orca device, security, pipeline, and operator-control state
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
    MapCameraCorridor,
    MapDevice,
    MapDeviceRegistrationIn,
    MapHeatPoint,
    MapOverview,
    ManagedDevice,
    OperatorControl,
    OperatorControlState,
    PipelineState,
    SceneCameraCorridor,
    SceneDevice,
    SceneOverview,
    SceneThreat,
    SecurityAlert,
    SecurityMonitorStatus,
)
from app.services.cache import CacheKeyBuilder, cache_service
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
            "drone-gateway": OperatorControlState.RUNNING,
            "sensor-gateway": OperatorControlState.RUNNING,
            "threat-detection": OperatorControlState.RUNNING,
        }
        self._map_devices: dict[str, MapDevice] = {}
        self._overview_cache_key = CacheKeyBuilder.build(
            "api", "dashboard-summary", "control-plane-overview"
        )
        self._map_cache_key = CacheKeyBuilder.build("dashboard", "summary", "map-overview")
        self._scene_cache_key = CacheKeyBuilder.build("dashboard", "summary", "scene-overview")

    async def overview(self, session: AsyncSession) -> ControlPlaneOverview:
        cached = cache_service.get_json(self._overview_cache_key)
        if cached is not None:
            return ControlPlaneOverview.model_validate(cached)

        cameras = await camera_registry_service.list_devices(session)
        if not cameras:
            cameras = await camera_registry_service.seed_demo_devices(session)

        devices = [
            ManagedDevice(
                id=str(device.id),
                name=device.device_id,
                category=DeviceCategory.CAMERA,
                trust_level=(
                    DeviceTrustLevel.BLOCKED
                    if device.tamper_detected
                    else DeviceTrustLevel.VERIFIED
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
            select(func.count())
            .select_from(AuditEventORM)
            .where(AuditEventORM.action.like("%telemetry%"))
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
        alerts.append(
            SecurityAlert(
                id="drone-surveillance-watch",
                severity="high",
                title="Drone and sensor surveillance correlation active",
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
            DataFlowStage(
                id="drone-surveillance",
                name="Drone and sensor surveillance",
                protocol="mavlink / rtsp / mqtt / kafka",
                state=PipelineState.HEALTHY,
                throughput_hint="telemetry + frames + alerts",
                destination="spark + threat intelligence",
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
            OperatorControl(
                id="drone-gateway",
                name="Drone Gateway",
                description="Normalizes drone telemetry and command traffic for Kafka.",
                state=self._controls["drone-gateway"],
                policy_mode="mission-audited",
                action_label=self._action_label(self._controls["drone-gateway"]),
            ),
            OperatorControl(
                id="sensor-gateway",
                name="Sensor Gateway",
                description=(
                    "Publishes fixed and mobile sensor readings into the "
                    "surveillance stream."
                ),
                state=self._controls["sensor-gateway"],
                policy_mode="schema-validated",
                action_label=self._action_label(self._controls["sensor-gateway"]),
            ),
            OperatorControl(
                id="threat-detection",
                name="Threat Detection",
                description="Correlates video, sensor, GPS, and geofence events into alerts.",
                state=self._controls["threat-detection"],
                policy_mode="ai-assisted",
                action_label=self._action_label(self._controls["threat-detection"]),
            ),
        ]

        overview = ControlPlaneOverview(
            devices=sorted(devices, key=self._last_seen_sort_key, reverse=True),
            security=security,
            data_flow=data_flow,
            controls=controls,
        )
        cache_service.set_json(
            self._overview_cache_key,
            overview.model_dump(mode="json"),
            cache_service.policies.dashboard,
        )
        return overview

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
        self._invalidate_dashboard_caches()

        overview = await self.overview(session)
        return next(control for control in overview.controls if control.id == control_id)

    async def map_overview(self, session: AsyncSession) -> MapOverview:
        cached = cache_service.get_json(self._map_cache_key)
        if cached is not None:
            return MapOverview.model_validate(cached)

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
            self._map_devices["drone-patrol-001"] = MapDevice(
                id="drone-patrol-001",
                device_id="drone-patrol-001",
                name="Drone Patrol Unit 001",
                device_type=DeviceCategory.DRONE,
                latitude=-25.7454,
                longitude=28.2438,
                trust_score=94,
                trust_level=DeviceTrustLevel.VERIFIED,
                camera_feed_url="rtsp://drone-patrol-001/camera/main",
                sensor_type="drone-telemetry",
                sensor_value=0.88,
                gps_path=[(-25.7479, 28.2293), (-25.7461, 28.2361), (-25.7454, 28.2438)],
                last_seen_at=now,
            )
            self._map_devices["perimeter-sensor-003"] = MapDevice(
                id="perimeter-sensor-003",
                device_id="perimeter-sensor-003",
                name="Perimeter Motion Sensor 003",
                device_type=DeviceCategory.SENSOR,
                latitude=-25.7448,
                longitude=28.2455,
                trust_score=91,
                trust_level=DeviceTrustLevel.VERIFIED,
                camera_feed_url=None,
                sensor_type="motion",
                sensor_value=0.92,
                gps_path=[(-25.7452, 28.2442), (-25.7448, 28.2455)],
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
        camera_corridors = [
            self._camera_corridor(device)
            for device in devices
            if device.device_type == DeviceCategory.CAMERA
        ]

        overview = MapOverview(
            devices=devices,
            heatmap=heatmap,
            camera_corridors=camera_corridors,
            visible_layers=[
                "verified-devices",
                "camera-overlays",
                "gps-paths",
                "sensor-heatmap",
                "drone-patrols",
                "threat-zones",
            ],
            security_policy=(
                "verified devices only; trust score must be greater than 80; "
                "drone, sensor, camera, and map updates are audited"
            ),
        )
        cache_service.set_json(
            self._map_cache_key,
            overview.model_dump(mode="json"),
            cache_service.policies.dashboard,
        )
        return overview

    async def scene_overview(self, session: AsyncSession, *, actor: str) -> SceneOverview:
        cached = cache_service.get_json(self._scene_cache_key)
        if cached is not None:
            await self._record_scene_audit(
                session,
                actor=actor,
                device_count=len(cached.get("devices", [])),
                threat_count=len(cached.get("threats", [])),
            )
            return SceneOverview.model_validate(cached)

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
            if (device.sensor_value or 0) >= 0.7
            or device.device_type == DeviceCategory.CAMERA
        ]
        await self._record_scene_audit(
            session,
            actor=actor,
            device_count=len(scene_devices),
            threat_count=len(threats),
        )
        overview = SceneOverview(
            devices=scene_devices,
            threats=threats,
            camera_corridors=[
                self._scene_camera_corridor(device)
                for device in map_overview.devices
                if device.device_type == DeviceCategory.CAMERA
            ],
            layers=[
                "city-map",
                "iot-devices",
                "gps-paths",
                "camera-overlays",
                "threat-waves",
            ],
            camera_overlay_mode="popup-texture-ready",
            security_policy=(
                "JWT + RBAC required; objects are color-coded by trust score "
                "and visible only after map trust policy validation"
            ),
        )
        cache_service.set_json(
            self._scene_cache_key,
            overview.model_dump(mode="json"),
            cache_service.policies.dashboard,
        )
        return overview

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
        self._invalidate_dashboard_caches()
        cache_service.delete(CacheKeyBuilder.build("device", "metadata", registration.device_id))
        return device

    async def _record_scene_audit(
        self,
        session: AsyncSession,
        *,
        actor: str,
        device_count: int,
        threat_count: int,
    ) -> None:
        session.add(
            AuditEventORM(
                id=str(uuid4()),
                entity_type="dashboard_scene",
                entity_id="3d-control-plane",
                action="control-plane.scene.visualized",
                actor=actor,
                payload={
                    "device_count": device_count,
                    "threat_count": threat_count,
                    "policy": "jwt-rbac-and-trust-score",
                },
            )
        )
        await session.commit()

    def _invalidate_dashboard_caches(self) -> None:
        cache_service.delete_many(
            [
                self._overview_cache_key,
                self._map_cache_key,
                self._scene_cache_key,
            ]
        )

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

    def _camera_location(
        self, location: dict[str, float] | None, index: int
    ) -> tuple[float, float]:
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

    def _camera_corridor(self, device: MapDevice) -> MapCameraCorridor:
        target_latitude, target_longitude = (
            device.gps_path[0]
            if device.gps_path
            else (device.latitude + 0.0012, device.longitude + 0.0018)
        )
        delta_latitude = target_latitude - device.latitude
        delta_longitude = target_longitude - device.longitude
        length = max((delta_latitude**2 + delta_longitude**2) ** 0.5, 0.0008)
        normal_latitude = -delta_longitude / length
        normal_longitude = delta_latitude / length
        width = 0.00045

        return MapCameraCorridor(
            id=f"{device.device_id}-corridor",
            source_device_id=device.device_id,
            label=f"{device.name} corridor",
            polygon=[
                (
                    device.latitude + normal_latitude * width,
                    device.longitude + normal_longitude * width,
                ),
                (
                    device.latitude - normal_latitude * width,
                    device.longitude - normal_longitude * width,
                ),
                (
                    target_latitude - normal_latitude * width * 1.6,
                    target_longitude - normal_longitude * width * 1.6,
                ),
                (
                    target_latitude + normal_latitude * width * 1.6,
                    target_longitude + normal_longitude * width * 1.6,
                ),
            ],
            coverage_score=min(max((device.sensor_value or 0.72), 0.2), 1),
        )

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

    def _scene_camera_corridor(self, device: MapDevice) -> SceneCameraCorridor:
        corridor = self._camera_corridor(device)
        return SceneCameraCorridor(
            id=corridor.id,
            source_device_id=corridor.source_device_id,
            label=corridor.label,
            polygon_3d=[
                self._scene_coordinates(latitude, longitude)
                for latitude, longitude in corridor.polygon
            ],
            coverage_score=corridor.coverage_score,
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
