"""
================================================================================
 File: citosmart/app/api/v1/endpoints/control_plane.py
 Purpose:
   Dashboard control-plane endpoints for devices, security posture, data flow,
   and operator control actions.
================================================================================
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_role
from app.db.session import get_session
from app.schemas.control_plane import (
    ControlPlaneOverview,
    MapDevice,
    MapDeviceRegistrationIn,
    MapOverview,
    OperatorControl,
    OperatorControlUpdateIn,
    SceneOverview,
)
from app.services.control_plane import control_plane_service

router = APIRouter()


@router.get(
    "/overview",
    response_model=ControlPlaneOverview,
    dependencies=[Depends(require_role("viewer"))],
    summary="Return device, security, pipeline, and operator control overview",
)
async def get_control_plane_overview(
    session: AsyncSession = Depends(get_session),
) -> ControlPlaneOverview:
    return await control_plane_service.overview(session)


@router.post(
    "/operator-controls/{control_id}",
    response_model=OperatorControl,
    dependencies=[Depends(require_role("operator"))],
    summary="Update one operator control state",
)
async def update_operator_control(
    control_id: str,
    update: OperatorControlUpdateIn,
    session: AsyncSession = Depends(get_session),
) -> OperatorControl:
    control = await control_plane_service.update_control(
        session,
        control_id=control_id,
        desired_state=update.desired_state,
        actor="api:operator-control",
    )
    if control is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown operator control '{control_id}'",
        )
    return control


@router.get(
    "/map",
    response_model=MapOverview,
    dependencies=[Depends(require_role("viewer"))],
    summary="Return verified IoT, GPS, and camera devices for the dashboard map",
)
async def get_map_overview(session: AsyncSession = Depends(get_session)) -> MapOverview:
    return await control_plane_service.map_overview(session)


@router.post(
    "/map/register",
    response_model=MapDevice,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("operator"))],
    summary="Register a Raspberry Pi or IoT edge node for map display",
)
async def register_map_device(
    registration: MapDeviceRegistrationIn,
    session: AsyncSession = Depends(get_session),
) -> MapDevice:
    return await control_plane_service.register_map_device(
        session,
        registration=registration,
        actor="api:map-device-register",
    )


@router.get(
    "/scene",
    response_model=SceneOverview,
    dependencies=[Depends(require_role("viewer"))],
    summary="Return 3D-ready city scene data for IoT, GPS, cameras, and threats",
)
async def get_scene_overview(session: AsyncSession = Depends(get_session)) -> SceneOverview:
    return await control_plane_service.scene_overview(session, actor="api:scene-overview")