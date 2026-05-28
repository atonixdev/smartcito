"""
================================================================================
 File: app/services/realtime_bus.py
 Purpose:
   Aggregates dashboard snapshots for the Orca WebSocket event bus.
================================================================================
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.services.control_plane import control_plane_service
from app.services.event_pipeline import event_pipeline_service


class RealtimeBusService:
    def __init__(self) -> None:
        self._settings = get_settings()

    async def snapshot(self) -> dict[str, Any]:
        async with AsyncSessionLocal() as session:
            overview = await control_plane_service.overview(session)
            map_overview = await control_plane_service.map_overview(session)

        surveillance = await self._fetch_surveillance_surfaces()

        return {
            "type": "command-center.snapshot",
            "generated_at": datetime.now(UTC).isoformat(),
            "events": [event.model_dump(mode="json") for event in event_pipeline_service.live_events(limit=20)],
            "alerts": [alert.model_dump(mode="json") for alert in event_pipeline_service.alerts(limit=20)],
            "control_plane": overview.model_dump(mode="json"),
            "map": map_overview.model_dump(mode="json"),
            "surveillance": surveillance,
        }

    async def _fetch_surveillance_surfaces(self) -> dict[str, Any]:
        timeout = httpx.Timeout(2.5, connect=1.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            drones, missions, feeds, threats, overlays = await self._gather_surveillance(client)

        return {
            "drones": drones,
            "missions": missions,
            "camera_feeds": feeds,
            "threat_alerts": threats,
            "mapping_overlays": overlays,
        }

    async def _gather_surveillance(self, client: httpx.AsyncClient) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
        drones = await self._safe_get_json(client, self._settings.drone_gateway_url, "/drones", fallback={"drones": [], "registry": []})
        missions = await self._safe_get_json(client, self._settings.mission_control_url, "/missions", fallback=[])
        feeds = await self._safe_get_json(client, self._settings.drone_camera_url, "/feeds", fallback=[])
        threats = await self._safe_get_json(client, self._settings.threat_detection_url, "/alerts", fallback=[])
        overlays = await self._safe_get_json(client, self._settings.mapping_geospatial_url, "/overlays", fallback={"drones": [], "sensors": [], "threats": [], "geofences": []})
        if isinstance(threats, dict):
            threats = threats.get("alerts", [])
        return drones, missions, feeds, threats, overlays

    async def _safe_get_json(self, client: httpx.AsyncClient, base_url: str, path: str, *, fallback: Any) -> Any:
        try:
            response = await client.get(f"{base_url}{path}")
            response.raise_for_status()
            return response.json()
        except Exception:
            return fallback


realtime_bus_service = RealtimeBusService()