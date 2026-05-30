"""
================================================================================
 File: app/api/v1/endpoints/events.py
 Purpose:
   Live event, historical analytics, and alert APIs for dashboard/webapp.
================================================================================
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import decode_token
from app.core.security import require_role
from app.db.session import get_session
from app.schemas.events import AlertEvent, HistoricalAnalyticsPoint, NormalizedEvent
from app.services.event_pipeline import event_pipeline_service
from app.services.realtime_bus import realtime_bus_service

router = APIRouter()

VALID_CHANNELS = {"global", "drone", "robot", "city", "mission", "individualization"}


def _normalize_channel(raw_channel: str | None) -> str:
    channel = (raw_channel or "global").strip().lower()
    if channel not in VALID_CHANNELS:
        return "global"
    return channel


def _resolve_raw_token(websocket: WebSocket, token: str | None) -> str | None:
    if token is not None:
        return token

    authorization = websocket.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1]
    return None


async def _stream_snapshot_loop(websocket: WebSocket, channel: str, token: str | None) -> None:
    settings = get_settings()

    raw_token = _resolve_raw_token(websocket, token)
    auth_required = settings.is_production

    if auth_required and raw_token is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    if raw_token is not None:
        try:
            decode_token(raw_token)
        except Exception:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    await websocket.accept()

    try:
        while True:
            await websocket.send_json(await realtime_bus_service.snapshot(channel=channel))
            await asyncio.sleep(settings.realtime_snapshot_interval_seconds)
    except WebSocketDisconnect:
        return


@router.get(
    "/live",
    response_model=list[NormalizedEvent],
    dependencies=[Depends(require_role("viewer"))],
    summary="Return recent live events",
)
async def live_events(limit: int = Query(25, ge=1, le=200)) -> list[NormalizedEvent]:
    return list(event_pipeline_service.live_events(limit=limit))


@router.get(
    "/history",
    response_model=list[HistoricalAnalyticsPoint],
    dependencies=[Depends(require_role("viewer"))],
    summary="Return historical analytics for processed events",
)
async def history(
    limit: int = Query(20, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> list[HistoricalAnalyticsPoint]:
    return await event_pipeline_service.historical_analytics(session, limit=limit)


@router.get(
    "/alerts",
    response_model=list[AlertEvent],
    dependencies=[Depends(require_role("viewer"))],
    summary="Return recent alert events",
)
async def alerts(limit: int = Query(25, ge=1, le=100)) -> list[AlertEvent]:
    return list(event_pipeline_service.alerts(limit=limit))


@router.websocket("/stream")
async def stream_events(
    websocket: WebSocket,
    token: str | None = Query(default=None),
    channel: str | None = Query(default="global"),
) -> None:
    await _stream_snapshot_loop(websocket, _normalize_channel(channel), token)


@router.websocket("/stream/{channel}")
async def stream_events_by_channel(
    websocket: WebSocket,
    channel: str,
    token: str | None = Query(default=None),
) -> None:
    await _stream_snapshot_loop(websocket, _normalize_channel(channel), token)
