"""
================================================================================
 File: citosmart/app/api/v1/endpoints/cameras.py
 Purpose:
   Camera fleet registration and telemetry endpoints.

 Endpoints:
   POST /api/v1/cameras/register                  Register or refresh a device.
   POST /api/v1/cameras/{device_id}/telemetry     Update stream/GPS state.
   GET  /api/v1/cameras                           List registered devices.
================================================================================
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_role
from app.db.session import get_session
from app.schemas.camera import CameraDeviceOut, CameraRegistrationIn, CameraTelemetryIn
from app.services.camera_registry import camera_registry_service

router = APIRouter()


@router.post(
    "/register",
    response_model=CameraDeviceOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("operator"))],
    summary="Register a body or micro camera",
)
async def register_camera(
    registration: CameraRegistrationIn,
    session: AsyncSession = Depends(get_session),
) -> CameraDeviceOut:
    """Register a new camera or refresh an existing device profile."""
    return await camera_registry_service.register(
        session=session,
        registration=registration,
        actor="api:camera-register",
    )


@router.post(
    "/{device_id}/telemetry",
    response_model=CameraDeviceOut,
    dependencies=[Depends(require_role("operator"))],
    summary="Update stream status and GPS telemetry for a camera",
)
async def update_camera_telemetry(
    device_id: str,
    telemetry: CameraTelemetryIn,
    session: AsyncSession = Depends(get_session),
) -> CameraDeviceOut:
    """Persist a live status update for a registered device."""
    device = await camera_registry_service.update_telemetry(
        session=session,
        device_id=device_id,
        telemetry=telemetry,
        actor="api:camera-telemetry",
    )
    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera '{device_id}' is not registered",
        )
    return device


@router.get(
    "",
    response_model=list[CameraDeviceOut],
    dependencies=[Depends(require_role("viewer"))],
    summary="List registered cameras and their latest fleet state",
)
async def list_cameras(session: AsyncSession = Depends(get_session)) -> list[CameraDeviceOut]:
    """Return every registered camera with its latest known status."""
    devices = await camera_registry_service.list_devices(session)
    if not devices:
        devices = await camera_registry_service.seed_demo_devices(session)
    return devices
