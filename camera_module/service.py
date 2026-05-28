"""
================================================================================
 File: camera_module/service.py
 Purpose:
   Minimal FastAPI camera-domain service exposing protocol capabilities and
   stream validation hooks for Orca contributors.
================================================================================
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from camera_module.drivers.rtsp_driver import build_rtsp_stream_config


load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

app = FastAPI(title="Orca Camera Module")


class CameraProbeRequest(BaseModel):
    """Request body for building a normalized RTSP stream config."""

    device_id: str = Field(..., min_length=1)
    host: str = Field(..., min_length=1)
    path: str = "/stream/main"


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "camera-module"}


@app.get("/drivers")
async def drivers() -> dict[str, list[str]]:
    return {"supported": ["onvif", "rtsp"]}


@app.post("/probe")
async def probe_camera(request: CameraProbeRequest) -> dict[str, object]:
    config = build_rtsp_stream_config(
        device_id=request.device_id,
        host=request.host,
        path=request.path,
    )
    return {
        "device_id": config.device_id,
        "stream_uri": config.stream_uri,
        "protocol": config.protocol,
        "secure_transport": config.secure_transport,
    }
