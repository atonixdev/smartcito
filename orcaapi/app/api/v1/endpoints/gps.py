"""
================================================================================
 File: orcaapi/app/api/v1/endpoints/gps.py
 Purpose:
   HTTP GPS ingestion and device tracking endpoints.

 Endpoints:
   POST /api/v1/ingest/gps                  Ingest one GPS point.
   GET  /api/v1/devices/{device_id}/last-position
   GET  /api/v1/devices/{device_id}/track
   GET  /api/v1/fleet/live
================================================================================
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import decode_token
from app.core.security import require_role
from app.db.session import get_session
from app.schemas.gps import GPSDashboardChannel
from app.schemas.gps import GPSFleetLiveResponse
from app.schemas.gps import GPSGatewayIn
from app.schemas.gps import GPSLiveDevice
from app.schemas.gps import GPSPointIn
from app.schemas.gps import GPSPointOut
from app.schemas.gps import GPSStreamMessage
from app.services.gps_realtime_gateway import gps_realtime_gateway_service
from app.services.gps_realtime_gateway import now_utc_iso
from app.services.gps_tracking import gps_tracking_service

router = APIRouter()


def _resolve_websocket_token(websocket: WebSocket, token: str | None) -> str | None:
    if token is not None:
        return token

    authorization = websocket.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1]
    return None


def _to_datetime(value: int | datetime) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    return datetime.fromtimestamp(value, tz=timezone.utc)


def _to_live_device(payload: GPSGatewayIn) -> GPSLiveDevice:
    channel = gps_realtime_gateway_service.channel_for_device_type(payload.device_type)
    return GPSLiveDevice(
        device_id=payload.device_id,
        channel=channel,  # type: ignore[arg-type]
        device_type=payload.device_type,
        name=payload.name or payload.device_id,
        icon=payload.icon or payload.device_type,
        color=payload.color or "#57c7d4",
        status=payload.status or "active",
        latitude=payload.latitude,
        longitude=payload.longitude,
        altitude=payload.altitude or 0.0,
        speed=payload.speed or 0.0,
        heading=payload.heading or 0.0,
        timestamp=_to_datetime(payload.timestamp),
    )


async def _publish_live_device(device: GPSLiveDevice) -> None:
    await gps_realtime_gateway_service.publish(device.model_dump(mode="json"))


@router.post(
    "/ingest/gps",
    response_model=GPSPointOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("operator"))],
    summary="Ingest a GPS point",
)
async def ingest_gps_point(
    point: GPSPointIn,
    session: AsyncSession = Depends(get_session),
) -> GPSPointOut:
    """Validate and persist one GPS point."""
    persisted = await gps_tracking_service.ingest(session, point)
    await _publish_live_device(
        GPSLiveDevice(
            device_id=persisted.device_id,
            channel="global",
            device_type="unknown",
            name=persisted.device_id,
            icon="unknown",
            color="#57c7d4",
            status="active",
            latitude=persisted.lat,
            longitude=persisted.lon,
            altitude=0.0,
            speed=persisted.speed or 0.0,
            heading=persisted.heading or 0.0,
            timestamp=persisted.ts,
        )
    )
    return persisted


@router.post(
    "/gps/gateway/ingest",
    response_model=GPSLiveDevice,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("operator"))],
    summary="Ingest a GPS gateway payload and broadcast live updates",
)
async def ingest_gateway_payload(
    payload: GPSGatewayIn,
    session: AsyncSession = Depends(get_session),
) -> GPSLiveDevice:
    """Accept canonical gateway payload format and fan out to GPS streams."""
    await gps_tracking_service.ingest(
        session,
        GPSPointIn(
            device_id=payload.device_id,
            lat=payload.latitude,
            lon=payload.longitude,
            speed=payload.speed,
            heading=payload.heading,
            ts=_to_datetime(payload.timestamp),
        ),
    )
    device = _to_live_device(payload)
    await _publish_live_device(device)
    return device


@router.get(
    "/devices/{device_id}/last-position",
    response_model=GPSPointOut,
    dependencies=[Depends(require_role("viewer"))],
    summary="Get the last known position for one device",
)
async def get_last_position(
    device_id: str,
    session: AsyncSession = Depends(get_session),
) -> GPSPointOut:
    """Return the latest stored position for the requested device."""
    point = await gps_tracking_service.get_last_position(session, device_id)
    if point is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No GPS points found for device '{device_id}'",
        )
    return point


@router.get(
    "/devices/{device_id}/track",
    response_model=list[GPSPointOut],
    dependencies=[Depends(require_role("viewer"))],
    summary="Get the historical track for one device",
)
async def get_device_track(
    device_id: str,
    from_ts: datetime | None = Query(None, alias="from"),
    to_ts: datetime | None = Query(None, alias="to"),
    limit: int = Query(1000, ge=1, le=5000),
    session: AsyncSession = Depends(get_session),
) -> list[GPSPointOut]:
    """Return GPS history for a device within the supplied time range."""
    return await gps_tracking_service.get_track(
        session,
        device_id,
        from_ts=from_ts,
        to_ts=to_ts,
        limit=limit,
    )


@router.get(
    "/fleet/live",
    response_model=GPSFleetLiveResponse,
    dependencies=[Depends(require_role("viewer"))],
    summary="Get the latest live position for all active devices",
)
async def get_live_fleet(
    active_within_minutes: int = Query(15, ge=1, le=1440),
    session: AsyncSession = Depends(get_session),
) -> GPSFleetLiveResponse:
    """Return the latest point per device for devices active in the window."""
    devices = await gps_tracking_service.get_live_fleet(
        session,
        active_within_minutes=active_within_minutes,
    )
    return GPSFleetLiveResponse(
        active_within_minutes=active_within_minutes,
        devices=devices,
    )


@router.websocket("/gps/stream")
async def gps_stream_default(
    websocket: WebSocket,
    channel: GPSDashboardChannel | None = Query(default="global"),
    token: str | None = Query(default=None),
) -> None:
    await _stream_gps_channel(websocket, channel or "global", token)


@router.websocket("/gps/stream/{channel}")
async def gps_stream_by_channel(
    websocket: WebSocket,
    channel: str,
    token: str | None = Query(default=None),
) -> None:
    await _stream_gps_channel(websocket, channel, token)


async def _stream_gps_channel(websocket: WebSocket, channel: str, token: str | None) -> None:
    settings = get_settings()
    raw_token = _resolve_websocket_token(websocket, token)

    if settings.is_production and raw_token is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    if raw_token is not None:
        try:
            decode_token(raw_token)
        except Exception:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    normalized_channel = gps_realtime_gateway_service.normalize_channel(channel)
    queue = await gps_realtime_gateway_service.subscribe(normalized_channel)
    await websocket.accept()

    snapshot = await gps_realtime_gateway_service.snapshot(normalized_channel)
    await websocket.send_json(
        GPSStreamMessage(
            type="gps.snapshot",
            channel=normalized_channel,  # type: ignore[arg-type]
            devices=[GPSLiveDevice.model_validate(item) for item in snapshot],
        ).model_dump(mode="json")
    )

    try:
        while True:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=10.0)
                await websocket.send_json(
                    GPSStreamMessage(
                        type="gps.update",
                        channel=normalized_channel,  # type: ignore[arg-type]
                        devices=[GPSLiveDevice.model_validate(message)],
                    ).model_dump(mode="json")
                )
            except TimeoutError:
                await websocket.send_json(
                    {
                        "type": "gps.heartbeat",
                        "channel": normalized_channel,
                        "generated_at": now_utc_iso(),
                        "devices": [],
                    }
                )
    except WebSocketDisconnect:
        return
    finally:
        await gps_realtime_gateway_service.unsubscribe(normalized_channel, queue)
