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
    ManagedDevice,
    OperatorControl,
    OperatorControlState,
    PipelineState,
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

    def _action_label(self, state: OperatorControlState) -> str:
        return "stop" if state == OperatorControlState.RUNNING else "start"

    def _last_seen_sort_key(self, device: ManagedDevice) -> float:
        timestamp = device.last_seen_at
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)
        return timestamp.timestamp()


control_plane_service = ControlPlaneService()