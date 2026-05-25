"""
================================================================================
 File: citosmart/app/schemas/geospatial.py
 Purpose:
   Pydantic contracts for persisted geospatial features and grouped datasets.
================================================================================
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class GeoFeatureType(str, Enum):
    GEOFENCE = "geofence"
    ZONE = "zone"
    SENSOR = "sensor"
    CAMERA = "camera"
    DRONE_PATH = "drone_path"
    ROBOT_PATH = "robot_path"
    MISSION_ROUTE = "mission_route"


class GeoGeometryType(str, Enum):
    POINT = "Point"
    LINE_STRING = "LineString"
    POLYGON = "Polygon"


class GeoGeometry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: GeoGeometryType
    coordinates: list


class GeoFeatureIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    feature_id: str = Field(..., min_length=3, max_length=128)
    name: str = Field(..., min_length=2, max_length=160)
    feature_type: GeoFeatureType
    zone: str | None = Field(default=None, max_length=80)
    geometry: GeoGeometry
    properties: dict = Field(default_factory=dict)
    source_service: str = Field(default="citosmart", min_length=2, max_length=80)
    timestamp: datetime | None = None


class GeoFeatureOut(GeoFeatureIn):
    id: UUID = Field(default_factory=uuid4)
    integrity: dict | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class GeoFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[dict] = Field(default_factory=list)


class GeoDatasetOut(BaseModel):
    geofences: list[GeoFeatureOut]
    zones: list[GeoFeatureOut]
    sensors: list[GeoFeatureOut]
    cameras: list[GeoFeatureOut]
    drone_paths: list[GeoFeatureOut]
    robot_paths: list[GeoFeatureOut]
    mission_routes: list[GeoFeatureOut]
    geojson_layers: dict[str, GeoFeatureCollection]