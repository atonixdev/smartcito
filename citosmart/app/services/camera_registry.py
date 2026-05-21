"""
================================================================================
 File: citosmart/app/services/camera_registry.py
 Purpose:
   DB-backed camera fleet registry with audit event emission.

   This replaces the in-memory registry so camera state survives process
   restarts and can be queried consistently across API workers.
================================================================================
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import AuditEventORM, CameraDeviceORM
from app.schemas.camera import CameraDeviceOut, CameraRegistrationIn, CameraTelemetryIn, StreamStatus


class CameraRegistryService:
    """Persistence layer for registered cameras and their audit trail."""

    async def register(
        self,
        session: AsyncSession,
        registration: CameraRegistrationIn,
        *,
        actor: str,
    ) -> CameraDeviceOut:
        """Create or refresh a device profile and append an audit event."""
        device = await self._get_device(session, registration.device_id)
        now = datetime.utcnow()
        payload = registration.model_dump(mode="json")

        if device is None:
            device = CameraDeviceORM(
                id=str(uuid4()),
                registered_at=now,
                **payload,
                stream_status=StreamStatus.OFFLINE.value,
                last_seen_at=now,
            )
            session.add(device)
            action = "camera.registered"
        else:
            device.device_type = registration.device_type.value
            device.firmware_version = registration.firmware_version
            device.capabilities = payload["capabilities"]
            device.network = payload["network"]
            device.security = payload["security"]
            device.mounting = payload["mounting"]
            device.last_seen_at = now
            action = "camera.re_registered"

        await self._append_audit_event(
            session,
            entity_id=registration.device_id,
            action=action,
            actor=actor,
            payload=payload,
        )
        await session.commit()
        return self._to_schema(device)

    async def update_telemetry(
        self,
        session: AsyncSession,
        device_id: str,
        telemetry: CameraTelemetryIn,
        *,
        actor: str,
    ) -> CameraDeviceOut | None:
        """Persist latest live state for a device and append an audit event."""
        device = await self._get_device(session, device_id)
        if device is None:
            return None

        payload = telemetry.model_dump(mode="json")
        device.stream_status = telemetry.stream_status.value
        device.location = payload["location"]
        device.battery_level = telemetry.battery_level
        device.mounted = telemetry.mounted
        device.tamper_detected = telemetry.tamper_detected
        device.last_seen_at = datetime.utcnow()

        await self._append_audit_event(
            session,
            entity_id=device_id,
            action="camera.telemetry_updated",
            actor=actor,
            payload=payload,
        )
        await session.commit()
        return self._to_schema(device)

    async def list_devices(self, session: AsyncSession) -> list[CameraDeviceOut]:
        """Return all registered cameras, newest first."""
        rows = await session.scalars(
            select(CameraDeviceORM).order_by(CameraDeviceORM.registered_at.desc())
        )
        return [self._to_schema(device) for device in rows.all()]

    async def seed_demo_devices(self, session: AsyncSession) -> list[CameraDeviceOut]:
        """Seed a demo fleet in non-production when the registry is empty."""
        settings = get_settings()
        if settings.is_production:
            return await self.list_devices(session)

        count = await session.scalar(select(func.count()).select_from(CameraDeviceORM))
        if count and count > 0:
            return await self.list_devices(session)

        demo_devices = [
            CameraDeviceORM(
                id=str(uuid4()),
                device_id="demo-body-001",
                device_type="body_camera",
                firmware_version="demo-1.0.0",
                capabilities={
                    "gps": True,
                    "tamper_detection": True,
                    "mount_detection": True,
                    "stream_protocols": ["rtsp", "http2"],
                    "local_encrypted_storage": True,
                },
                network={"transport": "5g", "signal_profile": "mobile"},
                security={
                    "identity_mode": "secure_element",
                    "tls_required": True,
                    "storage_encryption": "aes-256",
                },
                mounting={"magnetic_base": False, "mount_sensor_type": "none"},
                stream_status=StreamStatus.LIVE.value,
                location={"lat": -25.7479, "lon": 28.2293, "accuracy_m": 4.2},
                battery_level=87,
                mounted=True,
                tamper_detected=False,
            ),
            CameraDeviceORM(
                id=str(uuid4()),
                device_id="demo-micro-007",
                device_type="micro_camera",
                firmware_version="demo-2.4.1",
                capabilities={
                    "gps": True,
                    "tamper_detection": True,
                    "mount_detection": True,
                    "stream_protocols": ["onvif", "rtsp"],
                    "local_encrypted_storage": False,
                },
                network={"transport": "wifi6", "signal_profile": "hybrid"},
                security={
                    "identity_mode": "certificate",
                    "tls_required": True,
                    "storage_encryption": "aes-256",
                },
                mounting={"magnetic_base": True, "mount_sensor_type": "hall_effect"},
                stream_status=StreamStatus.CONNECTING.value,
                location={"lat": -26.2041, "lon": 28.0473, "accuracy_m": 8.0},
                battery_level=52,
                mounted=True,
                tamper_detected=False,
            ),
        ]

        for device in demo_devices:
            session.add(device)
            await self._append_audit_event(
                session,
                entity_id=device.device_id,
                action="camera.demo_seeded",
                actor="system:demo-seed",
                payload={
                    "device_type": device.device_type,
                    "stream_status": device.stream_status,
                },
            )

        await session.commit()
        return [self._to_schema(device) for device in demo_devices]

    async def _get_device(self, session: AsyncSession, device_id: str) -> CameraDeviceORM | None:
        """Fetch one device by its public device id."""
        return await session.scalar(
            select(CameraDeviceORM).where(CameraDeviceORM.device_id == device_id)
        )

    async def _append_audit_event(
        self,
        session: AsyncSession,
        *,
        entity_id: str,
        action: str,
        actor: str,
        payload: dict,
    ) -> None:
        """Append a structured audit event."""
        session.add(
            AuditEventORM(
                id=str(uuid4()),
                entity_type="camera_device",
                entity_id=entity_id,
                action=action,
                actor=actor,
                payload=payload,
            )
        )

    def _to_schema(self, device: CameraDeviceORM) -> CameraDeviceOut:
        """Convert an ORM row into the public API response shape."""
        return CameraDeviceOut(
            id=device.id,
            device_id=device.device_id,
            device_type=device.device_type,
            firmware_version=device.firmware_version,
            capabilities=device.capabilities,
            network=device.network,
            security=device.security,
            mounting=device.mounting,
            registered_at=device.registered_at,
            last_seen_at=device.last_seen_at,
            stream_status=device.stream_status,
            location=device.location,
            battery_level=device.battery_level,
            mounted=device.mounted,
            tamper_detected=device.tamper_detected,
        )


camera_registry_service = CameraRegistryService()
