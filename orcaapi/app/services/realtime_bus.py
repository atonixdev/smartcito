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


DashboardChannel = str


class RealtimeBusService:
    def __init__(self) -> None:
        self._settings = get_settings()

    async def snapshot(self, channel: DashboardChannel = "global") -> dict[str, Any]:
        overview_payload: dict[str, Any]
        map_payload: dict[str, Any]

        try:
            async with AsyncSessionLocal() as session:
                overview = await control_plane_service.overview(session)
                map_overview = await control_plane_service.map_overview(session)
            overview_payload = overview.model_dump(mode="json")
            map_payload = map_overview.model_dump(mode="json")
        except Exception:
            overview_payload = {
                "device_manager": {
                    "devices": [],
                    "summary": {"camera": 0, "sensor": 0, "gps": 0, "iot": 0},
                },
                "security": {
                    "status": "degraded",
                    "alerts": [],
                    "audit_pipeline_status": "degraded",
                },
                "traffic": {"active_incidents": [], "alerts": [], "congestion_score": 0.0},
                "data_flow": [],
                "timestamp": datetime.now(UTC).isoformat(),
            }
            map_payload = {
                "devices": [],
                "heatmap": [],
                "camera_corridors": [],
                "visible_layers": [],
                "security_policy": "degraded",
            }

        surveillance = await self._fetch_surveillance_surfaces()

        filtered_surveillance = surveillance
        filtered_map = map_payload
        filtered_control_plane = overview_payload
        filtered_events = [
            event.model_dump(mode="json") for event in event_pipeline_service.live_events(limit=20)
        ]
        filtered_alerts = [
            alert.model_dump(mode="json") for alert in event_pipeline_service.alerts(limit=20)
        ]

        if channel == "drone":
            filtered_surveillance = {
                "drones": surveillance.get("drones", {}),
                "missions": surveillance.get("missions", []),
                "camera_feeds": surveillance.get("camera_feeds", []),
                "threat_alerts": surveillance.get("threat_alerts", []),
                "mapping_overlays": surveillance.get("mapping_overlays", {}),
            }
        elif channel == "robot":
            filtered_surveillance = {
                "drones": {"drones": [], "registry": []},
                "missions": [],
                "camera_feeds": [],
                "threat_alerts": surveillance.get("threat_alerts", []),
                "mapping_overlays": surveillance.get("mapping_overlays", {}),
            }
            filtered_events = [
                event
                for event in filtered_events
                if str(event.get("source", "")).startswith("robot")
            ]
        elif channel == "city":
            filtered_surveillance = {
                "drones": surveillance.get("drones", {}),
                "missions": surveillance.get("missions", []),
                "camera_feeds": surveillance.get("camera_feeds", []),
                "threat_alerts": surveillance.get("threat_alerts", []),
                "mapping_overlays": surveillance.get("mapping_overlays", {}),
            }
        elif channel == "mission":
            filtered_surveillance = {
                "drones": surveillance.get("drones", {}),
                "missions": surveillance.get("missions", []),
                "camera_feeds": [],
                "threat_alerts": surveillance.get("threat_alerts", []),
                "mapping_overlays": {},
            }
            filtered_map = {
                "devices": [],
                "heatmap": [],
                "camera_corridors": [],
                "visible_layers": [],
                "security_policy": str(map_payload.get("security_policy", "degraded")),
            }
        elif channel == "individualization":
            filtered_surveillance = {
                "drones": surveillance.get("drones", {}),
                "missions": [],
                "camera_feeds": [],
                "threat_alerts": [],
                "mapping_overlays": {},
            }
            filtered_events = []
            filtered_alerts = []
            filtered_map = {
                "devices": map_payload.get("devices", []),
                "heatmap": [],
                "camera_corridors": [],
                "visible_layers": ["asset-profiles"],
                "security_policy": str(map_payload.get("security_policy", "degraded")),
            }
            filtered_control_plane = {
                **overview_payload,
                "data_flow": [],
            }

        return {
            "type": "command-center.snapshot",
            "channel": channel,
            "generated_at": datetime.now(UTC).isoformat(),
            "events": filtered_events,
            "alerts": filtered_alerts,
            "control_plane": filtered_control_plane,
            "map": filtered_map,
            "surveillance": filtered_surveillance,
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

    async def _gather_surveillance(self, client: httpx.AsyncClient) -> tuple[
        dict[str, Any],
        list[dict[str, Any]],
        list[dict[str, Any]],
        list[dict[str, Any]],
        dict[str, Any],
    ]:
        drones = await self._safe_get_json(
            client,
            self._settings.drone_gateway_url,
            "/drones",
            fallback={"drones": [], "registry": []},
        )
        missions = await self._safe_get_json(
            client, self._settings.mission_control_url, "/missions", fallback=[]
        )
        feeds = await self._safe_get_json(
            client, self._settings.drone_camera_url, "/feeds", fallback=[]
        )
        threats = await self._safe_get_json(
            client, self._settings.threat_detection_url, "/alerts", fallback=[]
        )
        overlays = await self._safe_get_json(
            client,
            self._settings.mapping_geospatial_url,
            "/overlays",
            fallback={"drones": [], "sensors": [], "threats": [], "geofences": []},
        )
        if isinstance(threats, dict):
            threats = threats.get("alerts", [])
        return drones, missions, feeds, threats, overlays

    async def _safe_get_json(
        self, client: httpx.AsyncClient, base_url: str, path: str, *, fallback: Any
    ) -> Any:
        try:
            response = await client.get(f"{base_url}{path}")
            response.raise_for_status()
            return response.json()
        except Exception:
            return fallback


realtime_bus_service = RealtimeBusService()
