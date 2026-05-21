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
from app.schemas.control_plane import ControlPlaneOverview, OperatorControl, OperatorControlUpdateIn
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