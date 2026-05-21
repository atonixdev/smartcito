"""
================================================================================
 File: backend/app/api/v1/router.py
 Purpose:
   Aggregates every v1 endpoint module under a single APIRouter so that
   `app.main` only needs to include one router. Adding a new module is a
   two-line change: import + include_router.
================================================================================
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, sensors, traffic

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(sensors.router, prefix="/sensors", tags=["sensors"])
api_router.include_router(traffic.router, prefix="/traffic", tags=["traffic"])
