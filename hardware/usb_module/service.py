"""
================================================================================
 File: hardware/usb_module/service.py
 Purpose:
   FastAPI service exposing detected USB devices for the SmartCito dashboard
   device manager and hardware integration tests.
================================================================================
"""

from __future__ import annotations

from fastapi import FastAPI

from hardware.usb_module.detector import detect_usb_devices

app = FastAPI(title="SmartCito USB Module")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "usb-module"}


@app.get("/devices")
async def devices() -> list[dict[str, object]]:
    return [device.__dict__ for device in detect_usb_devices()]