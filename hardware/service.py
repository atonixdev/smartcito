"""
================================================================================
 File: hardware/service.py
 Purpose:
   Minimal FastAPI hardware-domain service exposing demo monitoring samples.
================================================================================
"""

from __future__ import annotations

from fastapi import FastAPI

from hardware.monitoring.agent import collect_sample

app = FastAPI(title="SmartCito Hardware Domain")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "hardware-domain"}


@app.get("/monitoring/sample")
async def sample() -> dict[str, object]:
    sample = collect_sample("rack-a1")
    return {
        "rack_id": sample.rack_id,
        "temperature_c": sample.temperature_c,
        "power_kw": sample.power_kw,
    }
