"""
================================================================================
 File: surveillance/mapping_service.py
 Purpose:
   Mapping and Geospatial Service for drone/sensor overlays, geofence
   resolution, routes, and heatmap-ready operator dashboard APIs.
================================================================================
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from surveillance.geospatial import (
    evaluate_geofence_activity,
    geofence_geojson,
    geofence_overlays,
    normalize_point,
    path_around,
    route_mission,
    render_city_map,
    resolve_zone,
    search_locations,
)
from surveillance.kafka import get_publisher
from surveillance.models import DroneTelemetry, GeoPoint, MapOverlay, NormalizedEvent, SensorReading, SurveillanceOverview, ThreatAlert
from surveillance.topics import LOCATION_ENRICHED_TOPIC


load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

app = FastAPI(title="Orca Mapping and Geospatial Service")
_drones: dict[str, MapOverlay] = {}
_sensors: dict[str, MapOverlay] = {}
_threats: dict[str, MapOverlay] = {}


class GeofenceEvaluationRequest(BaseModel):
    current_position: GeoPoint
    previous_position: GeoPoint | None = None
    path: list[GeoPoint] = Field(default_factory=list)


class MissionRouteRequest(BaseModel):
    origin: GeoPoint
    destinations: list[GeoPoint] = Field(default_factory=list, min_length=1)
    obstacles: list[dict[str, object]] = Field(default_factory=list)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "mapping-geospatial"}


@app.get("/ready")
async def ready() -> dict[str, object]:
    return {
        "service": "mapping-geospatial",
        "providers": ["openstreetmap", "mapbox-compatible"],
        "topic": LOCATION_ENRICHED_TOPIC,
        "layers": ["drone-positions", "sensor-positions", "patrol-routes", "geofences", "heatmaps", "threats", "geojson", "markers"],
        "search": {"provider": "nominatim", "radius_unit": "km"},
    }


@app.post("/resolve")
async def resolve(position: GeoPoint) -> dict[str, object]:
    normalized = normalize_point(position)
    resolved_zone = resolve_zone(normalized["position"])
    return {
        "coordinate_system": normalized["coordinate_system"],
        "map_projection": normalized["map_projection"],
        "position": normalized["position"].model_dump(mode="json") if normalized["position"] is not None else None,
        "projected_position": normalized["projected"],
        "zone": resolved_zone,
    }


@app.get("/geofences")
async def geofences() -> dict[str, object]:
    return {"geojson": geofence_geojson(), "overlays": [overlay.model_dump(mode="json") for overlay in geofence_overlays()]}


@app.post("/geofences/evaluate")
async def evaluate_geofences(request: GeofenceEvaluationRequest) -> dict[str, object]:
    return evaluate_geofence_activity(
        request.current_position,
        previous_position=request.previous_position,
        path=request.path,
    )


@app.get("/search")
async def search(query: str, radius_km: float = 2.0, limit: int = 5) -> dict[str, object]:
    return search_locations(query, radius_km=radius_km, limit=limit)


@app.get("/maps/city")
async def city_map() -> dict[str, object]:
    return render_city_map(
        drone_overlays=list(_drones.values()),
        sensor_overlays=list(_sensors.values()),
        threat_overlays=list(_threats.values()),
        geofence_overlays_list=geofence_overlays(),
    )


@app.get("/maps/city.html", response_class=HTMLResponse)
async def city_map_html() -> HTMLResponse:
    rendered = render_city_map(
        drone_overlays=list(_drones.values()),
        sensor_overlays=list(_sensors.values()),
        threat_overlays=list(_threats.values()),
        geofence_overlays_list=geofence_overlays(),
    )
    return HTMLResponse(rendered["html"])


@app.post("/routes/mission")
async def mission_route(request: MissionRouteRequest) -> dict[str, object]:
    return route_mission(
        request.origin,
        request.destinations,
        extra_obstacles=request.obstacles,
    )


@app.post("/overlays/drone")
async def upsert_drone_overlay(telemetry: DroneTelemetry) -> dict[str, object]:
    normalized = normalize_point(telemetry.position)
    normalized_position = normalized["position"] or telemetry.position
    zone = resolve_zone(normalized_position)
    overlay = MapOverlay(
        overlay_id=telemetry.drone_id,
        overlay_type="drone",
        label=f"Drone {telemetry.drone_id}",
        position=normalized_position,
        path=path_around(normalized_position),
        intensity=max(0.1, min(1, telemetry.battery_percent / 100)),
        metadata={
            "status": telemetry.status.value,
            "speed_mps": telemetry.speed_mps,
            "heading_deg": telemetry.heading_deg,
            "battery_percent": telemetry.battery_percent,
            "zone": zone,
            "coordinate_system": normalized["coordinate_system"],
            "map_projection": normalized["map_projection"],
            "projected_position": normalized["projected"],
        },
    )
    _drones[telemetry.drone_id] = overlay
    event = NormalizedEvent(
        event_type="location.drone.enriched",
        source="mapping-geospatial",
        entity_id=telemetry.drone_id,
        topic=LOCATION_ENRICHED_TOPIC,
        payload=overlay.model_dump(mode="json"),
    )
    publish = get_publisher().publish_event(event)
    return {"overlay": overlay.model_dump(mode="json"), "publish": publish.model_dump(mode="json")}


@app.post("/overlays/sensor")
async def upsert_sensor_overlay(reading: SensorReading) -> dict[str, object]:
    normalized = normalize_point(reading.position)
    normalized_position = normalized["position"] or reading.position
    overlay = MapOverlay(
        overlay_id=reading.device_id,
        overlay_type="sensor",
        label=f"{reading.sensor_type} sensor {reading.device_id}",
        position=normalized_position,
        intensity=1 if reading.alert else min(1, abs(reading.value) / 100),
        metadata={
            "sensor_type": reading.sensor_type,
            "value": reading.value,
            "unit": reading.unit,
            "alert": reading.alert,
            "zone": resolve_zone(normalized_position),
            "coordinate_system": normalized["coordinate_system"],
            "map_projection": normalized["map_projection"],
            "projected_position": normalized["projected"],
        },
    )
    _sensors[reading.device_id] = overlay
    event = NormalizedEvent(
        event_type="location.sensor.enriched",
        source="mapping-geospatial",
        entity_id=reading.device_id,
        topic=LOCATION_ENRICHED_TOPIC,
        payload=overlay.model_dump(mode="json"),
    )
    publish = get_publisher().publish_event(event)
    return {"overlay": overlay.model_dump(mode="json"), "publish": publish.model_dump(mode="json")}


@app.post("/overlays/threat")
async def upsert_threat_overlay(alert: ThreatAlert) -> dict[str, object]:
    overlay = MapOverlay(
        overlay_id=alert.alert_id,
        overlay_type="threat",
        label=alert.title,
        position=alert.position,
        intensity=alert.confidence,
        metadata={
            "threat_level": alert.threat_level.value,
            "zone": alert.zone,
            "source_ids": alert.source_ids,
            "recommended_actions": alert.recommended_actions,
        },
    )
    _threats[alert.alert_id] = overlay
    return {"overlay": overlay.model_dump(mode="json")}


@app.get("/overlays", response_model=SurveillanceOverview)
async def overlays() -> SurveillanceOverview:
    return SurveillanceOverview(
        drones=list(_drones.values()),
        sensors=list(_sensors.values()),
        threats=list(_threats.values()),
        geofences=geofence_overlays(),
    )
