"""
================================================================================
 File: gps_module/service.py
 Purpose:
   Minimal FastAPI GPS-domain service exposing NMEA parsing and standards
   metadata for SmartCito contributors.
================================================================================
"""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from gps_module.nmea import parse_gpgga

app = FastAPI(title="SmartCito GPS Module")


class NmeaRequest(BaseModel):
    """Request body for parsing one NMEA sentence."""

    sentence: str = Field(..., min_length=6)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "gps-module"}


@app.get("/standards")
async def standards() -> dict[str, list[str]]:
    return {"supported": ["nmea0183", "nmea2000", "json"]}


@app.post("/parse")
async def parse_sentence(request: NmeaRequest) -> dict[str, object]:
    fix = parse_gpgga(request.sentence)
    return {
        "latitude": fix.latitude,
        "longitude": fix.longitude,
        "quality": fix.quality,
        "satellites": fix.satellites,
    }
