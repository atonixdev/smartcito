"""
================================================================================
 File: citosmart/app/api/v1/endpoints/platform.py
 Purpose:
   Resource-based SmartCito platform API for frontend dashboard integration.
================================================================================
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket
from pydantic import BaseModel, Field

from app.core.security import require_role
from app.schemas.api_response import api_envelope

router = APIRouter(tags=["platform"])

DEVICES: dict[str, dict] = {
    "cam-001": {
        "id": "cam-001",
        "type": "camera",
        "status": "online",
        "location": {"lat": -26.2041, "lng": 28.0473},
        "trust_score": 96,
    },
    "gps-001": {
        "id": "gps-001",
        "type": "gps",
        "status": "online",
        "location": {"lat": -26.205, "lng": 28.048},
        "trust_score": 92,
    },
}

EVENTS = [
    {
        "id": "evt-001",
        "kind": "log",
        "severity": "info",
        "message": "Dashboard API online",
        "timestamp": datetime.now(UTC).isoformat(),
    }
]


class LocationIn(BaseModel):
    lat: float
    lng: float


class DeviceIn(BaseModel):
    id: str = Field(..., min_length=3, max_length=80)
    type: str
    status: str = "online"
    location: LocationIn
    trust_score: int = Field(default=90, ge=0, le=100)


class DeviceStatusIn(BaseModel):
    status: str


@router.get("/devices")
async def list_devices(request: Request):
    return api_envelope(request, {"devices": list(DEVICES.values())})


@router.post("/devices", dependencies=[Depends(require_role("operator"))])
async def register_device(request: Request, payload: DeviceIn):
    DEVICES[payload.id] = payload.model_dump()
    return api_envelope(request, {"device": DEVICES[payload.id]})


@router.get("/devices/{device_id}")
async def get_device(request: Request, device_id: str):
    device = DEVICES.get(device_id)
    if not device:
      raise HTTPException(status_code=404, detail="Device not found")
    return api_envelope(request, {"device": device})


@router.patch("/devices/{device_id}/status", dependencies=[Depends(require_role("operator"))])
async def update_device_status(request: Request, device_id: str, payload: DeviceStatusIn):
    if device_id not in DEVICES:
        raise HTTPException(status_code=404, detail="Device not found")
    DEVICES[device_id]["status"] = payload.status
    return api_envelope(request, {"device": DEVICES[device_id]})


@router.get("/cameras")
async def list_cameras(request: Request):
    cameras = [
        {
            **device,
            "stream_url": f"rtsp://smartcito.local/{device['id']}",
            "health": "healthy",
            "recording": True,
        }
        for device in DEVICES.values()
        if device["type"] == "camera"
    ]
    return api_envelope(request, {"cameras": cameras})


@router.get("/gps/live")
async def live_gps(request: Request):
    points = [
        {
            "device_id": device["id"],
            "lat": device["location"]["lat"],
            "lng": device["location"]["lng"],
            "speed": 45.2,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        for device in DEVICES.values()
        if device["type"] == "gps"
    ]
    return api_envelope(request, {"coordinates": points})


@router.get("/gps/{device_id}/history")
async def gps_history(request: Request, device_id: str):
    device = DEVICES.get(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    lat = device["location"]["lat"]
    lng = device["location"]["lng"]
    return api_envelope(request, {
        "route": [
            {"lat": lat - 0.001, "lng": lng - 0.001},
            {"lat": lat - 0.0005, "lng": lng - 0.0005},
            {"lat": lat, "lng": lng},
        ]
    })


@router.get("/events")
async def list_events(request: Request):
    return api_envelope(request, {"events": EVENTS})


@router.get("/map/layers")
async def map_layers(request: Request):
    return api_envelope(request, {
        "geojson": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"id": device["id"], "type": device["type"]},
                    "geometry": {
                        "type": "Point",
                        "coordinates": [device["location"]["lng"], device["location"]["lat"]],
                    },
                }
                for device in DEVICES.values()
            ],
        },
        "markers": list(DEVICES.values()),
    })


@router.websocket("/ws/gps")
async def gps_socket(websocket: WebSocket):
    await websocket.accept()
    while True:
        await websocket.send_json({
            "device_id": "gps-001",
            "lat": -26.2041,
            "lng": 28.0473,
            "speed": 45.2,
            "timestamp": datetime.now(UTC).isoformat(),
        })
        await asyncio.sleep(5)


@router.websocket("/ws/events")
async def events_socket(websocket: WebSocket):
    await websocket.accept()
    while True:
        await websocket.send_json({
            "id": str(uuid4()),
            "kind": "log",
            "severity": "info",
            "message": "Live SmartCito event stream",
            "timestamp": datetime.now(UTC).isoformat(),
        })
        await asyncio.sleep(5)
