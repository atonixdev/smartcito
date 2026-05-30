"""
================================================================================
 File: surveillance/geospatial.py
 Purpose:
   Shared geographic processing engine for GPS normalization, geofence
   evaluation, search, and Folium map rendering across Orca services.
================================================================================
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any
from urllib import parse, request

try:
    import folium
except ModuleNotFoundError:  # pragma: no cover - optional map rendering dependency.
    folium = None
try:
    import geopandas as gpd
except ModuleNotFoundError:  # pragma: no cover - optional geospatial dependency.
    gpd = None
try:
    import networkx as nx
except ModuleNotFoundError:  # pragma: no cover - optional routing dependency.
    nx = None
try:
    from pyproj import Transformer
except ModuleNotFoundError:  # pragma: no cover - optional projection dependency.
    Transformer = None
from shapely.geometry import LineString, Point, Polygon, mapping, shape

from surveillance.models import GeoPoint, MapOverlay


WGS84_CRS = "EPSG:4326"
WEB_MERCATOR_CRS = "EPSG:3857"
ALERT_BUFFER_METERS = 250.0


class _IdentityTransformer:
    @staticmethod
    def transform(x: float, y: float) -> tuple[float, float]:
        return x, y


if Transformer is None:
    _TO_WEB_MERCATOR = _IdentityTransformer()
    _TO_WGS84 = _IdentityTransformer()
else:
    _TO_WEB_MERCATOR = Transformer.from_crs(WGS84_CRS, WEB_MERCATOR_CRS, always_xy=True)
    _TO_WGS84 = Transformer.from_crs(WEB_MERCATOR_CRS, WGS84_CRS, always_xy=True)

GEOFENCE_SPECS = [
    {
        "id": "zone-1-cbd",
        "name": "CBD Operations Zone",
        "type": "geofence",
        "zone": "cbd",
        "criticality": "high",
        "polygon": [
            (28.2180, -25.7550),
            (28.2360, -25.7550),
            (28.2360, -25.7420),
            (28.2180, -25.7420),
        ],
    },
    {
        "id": "zone-2-transport",
        "name": "Transport Corridor",
        "type": "restricted_area",
        "zone": "transport",
        "criticality": "medium",
        "polygon": [
            (28.1700, -25.7600),
            (28.2050, -25.7600),
            (28.2050, -25.7350),
            (28.1700, -25.7350),
        ],
    },
    {
        "id": "zone-3-critical-infra",
        "name": "Critical Infrastructure Area",
        "type": "alert_zone",
        "zone": "critical_infrastructure",
        "criticality": "critical",
        "polygon": [
            (28.2360, -25.7520),
            (28.2600, -25.7520),
            (28.2600, -25.7380),
            (28.2360, -25.7380),
        ],
    },
]

LOCAL_SEARCH_INDEX = [
    {
        "name": "Johannesburg",
        "display_name": "Johannesburg, Gauteng, South Africa",
        "type": "city",
        "zone": "johannesburg",
        "timestamp": None,
        "latitude": -26.2041,
        "longitude": 28.0473,
    },
    {
        "name": "Winchester Hills",
        "display_name": "Winchester Hills, Johannesburg, Gauteng, South Africa",
        "type": "district",
        "zone": "johannesburg",
        "timestamp": None,
        "latitude": -26.2682,
        "longitude": 28.0202,
    },
    {
        "name": "Pretoria CBD",
        "display_name": "Pretoria CBD, Tshwane, Gauteng, South Africa",
        "type": "district",
        "zone": "pretoria",
        "timestamp": None,
        "latitude": -25.7479,
        "longitude": 28.2293,
    },
]


def _geometry_to_point(geometry: Point) -> GeoPoint:
    return GeoPoint(latitude=float(geometry.y), longitude=float(geometry.x))


def _build_geodataframe(records: list[dict[str, Any]]) -> gpd.GeoDataFrame:
    if gpd is None:
        raise RuntimeError("geopandas is not installed")
    return gpd.GeoDataFrame(records, geometry="geometry", crs=WGS84_CRS)


def _geofence_records() -> list[dict[str, Any]]:
    persisted_geofences = _dataset_features_by_type("geofence")
    persisted_zones = _dataset_features_by_type("zone")
    source_features = persisted_geofences + persisted_zones
    if source_features:
        return [
            {
                "id": item["feature_id"],
                "name": item["name"],
                "type": item["feature_type"],
                "zone": item.get("zone"),
                "timestamp": item.get("timestamp"),
                "criticality": item.get("properties", {}).get("criticality", "low"),
                "geometry": shape(item["geometry"]),
            }
            for item in source_features
        ]

    return [
        {
            "id": spec["id"],
            "name": spec["name"],
            "type": spec["type"],
            "zone": spec["zone"],
            "timestamp": None,
            "criticality": spec["criticality"],
            "geometry": Polygon(spec["polygon"]),
        }
        for spec in GEOFENCE_SPECS
    ]


def _backend_geospatial_url() -> str:
    return os.getenv("ORCAAPI_GEOSPATIAL_URL", "http://orcaapi:8000/api/v1/geospatial/dataset")


def fetch_persisted_geographic_dataset() -> dict[str, Any] | None:
    req = request.Request(url=_backend_geospatial_url(), headers={"Accept": "application/json"})
    try:
        with request.urlopen(req, timeout=4) as response:
            payload = json.loads(response.read().decode("utf-8") or "{}")
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _dataset_features_by_type(feature_type: str) -> list[dict[str, Any]]:
    dataset = fetch_persisted_geographic_dataset()
    if not dataset:
        return []
    if feature_type == "mission_route":
        candidate = dataset.get("mission_routes")
    elif feature_type == "drone_path":
        candidate = dataset.get("drone_paths")
    elif feature_type == "robot_path":
        candidate = dataset.get("robot_paths")
    else:
        candidate = dataset.get(f"{feature_type}s")
    return candidate if isinstance(candidate, list) else []


def _line_features_geojson(feature_type: str) -> dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": item.get("feature_id"),
                "geometry": item.get("geometry"),
                "properties": {
                    "name": item.get("name"),
                    "feature_type": item.get("feature_type"),
                    "zone": item.get("zone"),
                    **(item.get("properties") or {}),
                },
            }
            for item in _dataset_features_by_type(feature_type)
            if isinstance(item.get("geometry"), dict) and item["geometry"].get("type") == "LineString"
        ],
    }


def _point_features_geojson(feature_type: str) -> dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": item.get("feature_id"),
                "geometry": item.get("geometry"),
                "properties": {
                    "name": item.get("name"),
                    "feature_type": item.get("feature_type"),
                    "zone": item.get("zone"),
                    **(item.get("properties") or {}),
                },
            }
            for item in _dataset_features_by_type(feature_type)
            if isinstance(item.get("geometry"), dict) and item["geometry"].get("type") == "Point"
        ],
    }


def geofence_geodataframe() -> gpd.GeoDataFrame:
    return _build_geodataframe(_geofence_records())


def geofence_geodataframe_projected() -> gpd.GeoDataFrame:
    return geofence_geodataframe().to_crs(WEB_MERCATOR_CRS)


@lru_cache(maxsize=1)
def _city_reference_center() -> tuple[float, float]:
    if gpd is None:
        records = _geofence_records()
        if not records:
            return 0.0, 0.0
        latitudes = [float(item["geometry"].representative_point().y) for item in records]
        longitudes = [float(item["geometry"].representative_point().x) for item in records]
        return sum(latitudes) / len(latitudes), sum(longitudes) / len(longitudes)

    projected_centroids = geofence_geodataframe().to_crs(WEB_MERCATOR_CRS).geometry.centroid
    centroid_points = gpd.GeoSeries(projected_centroids, crs=WEB_MERCATOR_CRS).to_crs(WGS84_CRS)
    return float(centroid_points.y.mean()), float(centroid_points.x.mean())


def normalize_point(position: GeoPoint | None) -> dict[str, Any]:
    if position is None:
        return {
            "position": None,
            "coordinate_system": WGS84_CRS,
            "map_projection": WEB_MERCATOR_CRS,
            "projected": None,
        }

    projected_x, projected_y = _TO_WEB_MERCATOR.transform(position.longitude, position.latitude)
    normalized_x, normalized_y = _TO_WGS84.transform(projected_x, projected_y)
    normalized_point = GeoPoint(
        latitude=float(normalized_y),
        longitude=float(normalized_x),
        altitude_m=position.altitude_m,
    )
    return {
        "position": normalized_point,
        "coordinate_system": WGS84_CRS,
        "map_projection": WEB_MERCATOR_CRS,
        "projected": {"x": float(projected_x), "y": float(projected_y)},
    }


def resolve_zone(position: GeoPoint | None) -> dict[str, Any]:
    normalized = normalize_point(position)
    normalized_position = normalized["position"]
    if normalized_position is None:
        return {
            "zone_id": None,
            "zone_label": None,
            "criticality": None,
            "status": "unknown",
            "distance_m": None,
            "violation": False,
        }

    point = Point(normalized_position.longitude, normalized_position.latitude)
    point_projected = Point(*_TO_WEB_MERCATOR.transform(point.x, point.y))
    if gpd is None:
        records = _geofence_records()
        nearest_distance: float | None = None
        nearest: dict[str, Any] | None = None
        for record in records:
            geometry = record["geometry"]
            projected_geometry = shape(
                {
                    "type": geometry.geom_type,
                    "coordinates": [
                        _TO_WEB_MERCATOR.transform(x, y)
                        for x, y in geometry.exterior.coords
                    ],
                }
            )

            if geometry.contains(point) or geometry.intersects(point):
                return {
                    "zone_id": str(record["id"]),
                    "zone_label": str(record["name"]),
                    "criticality": str(record["criticality"]),
                    "status": "inside",
                    "distance_m": 0.0,
                    "violation": str(record["criticality"]) in {"high", "critical"},
                    "zone": str(record["zone"]),
                    "coordinate_system": WGS84_CRS,
                    "map_projection": WEB_MERCATOR_CRS,
                    "projected_position": normalized["projected"],
                    "buffer_m": ALERT_BUFFER_METERS,
                }

            buffered = projected_geometry.buffer(ALERT_BUFFER_METERS)
            if buffered.contains(point_projected):
                distance = float(projected_geometry.distance(point_projected))
                return {
                    "zone_id": str(record["id"]),
                    "zone_label": str(record["name"]),
                    "criticality": str(record["criticality"]),
                    "status": "nearby",
                    "distance_m": round(distance, 3),
                    "violation": False,
                    "zone": str(record["zone"]),
                    "coordinate_system": WGS84_CRS,
                    "map_projection": WEB_MERCATOR_CRS,
                    "projected_position": normalized["projected"],
                    "buffer_m": ALERT_BUFFER_METERS,
                }

            distance = float(projected_geometry.distance(point_projected))
            if nearest_distance is None or distance < nearest_distance:
                nearest_distance = distance
                nearest = record

        return {
            "zone_id": "outside-managed-zones",
            "zone_label": "Outside managed zones",
            "criticality": "low",
            "status": "outside",
            "distance_m": round(float(nearest_distance or 0.0), 3),
            "violation": False,
            "nearest_zone_id": None if nearest is None else str(nearest["id"]),
            "nearest_zone_label": None if nearest is None else str(nearest["name"]),
            "coordinate_system": WGS84_CRS,
            "map_projection": WEB_MERCATOR_CRS,
            "projected_position": normalized["projected"],
            "buffer_m": ALERT_BUFFER_METERS,
        }

    geofences = geofence_geodataframe()
    geofences_projected = geofence_geodataframe_projected()

    for index, row in geofences.iterrows():
        geometry = row.geometry
        if geometry.contains(point) or geometry.intersects(point):
            return {
                "zone_id": str(row["id"]),
                "zone_label": str(row["name"]),
                "criticality": str(row["criticality"]),
                "status": "inside",
                "distance_m": 0.0,
                "violation": str(row["criticality"]) in {"high", "critical"},
                "zone": str(row["zone"]),
                "coordinate_system": WGS84_CRS,
                "map_projection": WEB_MERCATOR_CRS,
                "projected_position": normalized["projected"],
                "buffer_m": ALERT_BUFFER_METERS,
            }

        projected_geometry = geofences_projected.geometry.iloc[index]
        buffered = projected_geometry.buffer(ALERT_BUFFER_METERS)
        if buffered.contains(point_projected):
            return {
                "zone_id": str(row["id"]),
                "zone_label": str(row["name"]),
                "criticality": str(row["criticality"]),
                "status": "nearby",
                "distance_m": round(float(projected_geometry.distance(point_projected)), 3),
                "violation": False,
                "zone": str(row["zone"]),
                "coordinate_system": WGS84_CRS,
                "map_projection": WEB_MERCATOR_CRS,
                "projected_position": normalized["projected"],
                "buffer_m": ALERT_BUFFER_METERS,
            }

    distances = geofences_projected.geometry.distance(point_projected)
    nearest_index = int(distances.idxmin())
    nearest = geofences.iloc[nearest_index]
    return {
        "zone_id": "outside-managed-zones",
        "zone_label": "Outside managed zones",
        "criticality": "low",
        "status": "outside",
        "distance_m": round(float(distances.iloc[nearest_index]), 3),
        "violation": False,
        "nearest_zone_id": str(nearest["id"]),
        "nearest_zone_label": str(nearest["name"]),
        "coordinate_system": WGS84_CRS,
        "map_projection": WEB_MERCATOR_CRS,
        "projected_position": normalized["projected"],
        "buffer_m": ALERT_BUFFER_METERS,
    }


def geofence_overlays() -> list[MapOverlay]:
    overlays: list[MapOverlay] = []
    if gpd is None:
        for record in _geofence_records():
            centroid = record["geometry"].representative_point()
            overlays.append(
                MapOverlay(
                    overlay_id=str(record["id"]),
                    overlay_type="geofence",
                    label=str(record["name"]),
                    position=GeoPoint(latitude=float(centroid.y), longitude=float(centroid.x)),
                    metadata={
                        "criticality": str(record["criticality"]),
                        "zone": str(record["zone"]),
                        "type": str(record["type"]),
                        "geometry": mapping(record["geometry"]),
                    },
                )
            )
        return overlays

    geofences = geofence_geodataframe()
    projected_centroids = geofences.to_crs(WEB_MERCATOR_CRS).geometry.centroid
    centroid_points = gpd.GeoSeries(projected_centroids, crs=WEB_MERCATOR_CRS).to_crs(WGS84_CRS)
    for index, row in geofences.iterrows():
        centroid = centroid_points.iloc[index]
        overlays.append(
            MapOverlay(
                overlay_id=str(row["id"]),
                overlay_type="geofence",
                label=str(row["name"]),
                position=_geometry_to_point(centroid),
                metadata={
                    "criticality": str(row["criticality"]),
                    "zone": str(row["zone"]),
                    "type": str(row["type"]),
                    "geometry": mapping(row.geometry),
                },
            )
        )
    return overlays


def evaluate_geofence_activity(
    current_position: GeoPoint,
    previous_position: GeoPoint | None = None,
    path: list[GeoPoint] | None = None,
) -> dict[str, Any]:
    if gpd is None:
        geofences = _geofence_records()
        current_point = Point(current_position.longitude, current_position.latitude)
        current_inside = [
            item for item in geofences if item["geometry"].contains(current_point) or item["geometry"].intersects(current_point)
        ]

        previous_ids: set[str] = set()
        if previous_position is not None:
            previous_point = Point(previous_position.longitude, previous_position.latitude)
            previous_inside = [
                item
                for item in geofences
                if item["geometry"].contains(previous_point) or item["geometry"].intersects(previous_point)
            ]
            previous_ids = {str(item["id"]) for item in previous_inside}

        path_intersections: set[str] = set()
        if path:
            route = LineString([(waypoint.longitude, waypoint.latitude) for waypoint in path])
            path_intersections = {str(item["id"]) for item in geofences if item["geometry"].intersects(route)}

        current_ids = {str(item["id"]) for item in current_inside}
        entries = sorted(current_ids - previous_ids)
        exits = sorted(previous_ids - current_ids)
        violations = sorted(
            {
                str(item["id"])
                for item in current_inside
                if str(item["criticality"]) in {"high", "critical"}
            }
            | {
                str(item["id"])
                for item in geofences
                if str(item["id"]) in path_intersections and str(item["criticality"]) in {"high", "critical"}
            }
        )
        return {
            "current_zone": resolve_zone(current_position),
            "entries": entries,
            "exits": exits,
            "intersections": sorted(path_intersections),
            "violations": violations,
        }

    geofences = geofence_geodataframe()
    current_point = Point(current_position.longitude, current_position.latitude)
    current_inside = geofences[geofences.geometry.apply(lambda geometry: geometry.contains(current_point) or geometry.intersects(current_point))]

    previous_ids: set[str] = set()
    if previous_position is not None:
        previous_point = Point(previous_position.longitude, previous_position.latitude)
        previous_inside = geofences[geofences.geometry.apply(lambda geometry: geometry.contains(previous_point) or geometry.intersects(previous_point))]
        previous_ids = {str(value) for value in previous_inside["id"].tolist()}

    path_intersections: set[str] = set()
    if path:
        route = LineString([(waypoint.longitude, waypoint.latitude) for waypoint in path])
        path_intersections = {
            str(row["id"])
            for _, row in geofences.iterrows()
            if row.geometry.intersects(route)
        }

    current_ids = {str(value) for value in current_inside["id"].tolist()}
    entries = sorted(current_ids - previous_ids)
    exits = sorted(previous_ids - current_ids)
    violations = sorted(
        {
            str(row["id"])
            for _, row in current_inside.iterrows()
            if str(row["criticality"]) in {"high", "critical"}
        }
        | {
            str(row["id"])
            for _, row in geofences.iterrows()
            if str(row["id"]) in path_intersections and str(row["criticality"]) in {"high", "critical"}
        }
    )
    current_zone = resolve_zone(current_position)
    return {
        "current_zone": current_zone,
        "entries": entries,
        "exits": exits,
        "intersections": sorted(path_intersections),
        "violations": violations,
    }


def _route_polygon_barriers(extra_obstacles: list[dict[str, Any]] | None = None) -> list[Polygon]:
    polygons: list[Polygon] = []
    if gpd is None:
        for item in _geofence_records():
            if str(item["type"]) in {"restricted_area", "alert_zone"} or str(item["criticality"]) in {"high", "critical"}:
                polygons.append(item["geometry"])
    else:
        geofences = geofence_geodataframe()
        for _, row in geofences.iterrows():
            if str(row["type"]) in {"restricted_area", "alert_zone"} or str(row["criticality"]) in {"high", "critical"}:
                polygons.append(row.geometry)
    for obstacle in extra_obstacles or []:
        try:
            geometry = shape(obstacle)
        except Exception:
            continue
        if isinstance(geometry, Polygon):
            polygons.append(geometry)
    return polygons


def _route_node_coordinates(
    origin: GeoPoint,
    destinations: list[GeoPoint],
    barrier_polygons: list[Polygon],
) -> list[tuple[float, float]]:
    coordinates = [(origin.longitude, origin.latitude)]
    coordinates.extend((point.longitude, point.latitude) for point in destinations)
    for polygon in barrier_polygons:
        min_x, min_y, max_x, max_y = polygon.bounds
        padding = 0.0015
        for coordinate in [
            (min_x - padding, min_y - padding),
            (min_x - padding, max_y + padding),
            (max_x + padding, min_y - padding),
            (max_x + padding, max_y + padding),
        ]:
            coordinates.append(coordinate)
    return list(dict.fromkeys(coordinates))


def _segment_clear(segment: LineString, barrier_polygons: list[Polygon]) -> bool:
    start_point = Point(segment.coords[0])
    end_point = Point(segment.coords[-1])
    for polygon in barrier_polygons:
        endpoint_inside = (
            polygon.contains(start_point)
            or polygon.contains(end_point)
            or polygon.touches(start_point)
            or polygon.touches(end_point)
        )
        if not endpoint_inside and (segment.crosses(polygon) or segment.within(polygon)):
            return False
        if segment.intersects(polygon) and not endpoint_inside:
            return False
    return True


def route_mission(
    origin: GeoPoint,
    destinations: list[GeoPoint],
    *,
    extra_obstacles: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if not destinations:
        return {
            "path": [],
            "geojson": {"type": "FeatureCollection", "features": []},
            "segments": [],
            "distance_m": 0.0,
            "avoided_zone_ids": [],
        }

    if nx is None:
        sequence = [origin, *destinations]
        path_points = [
            GeoPoint(latitude=point.latitude, longitude=point.longitude, altitude_m=point.altitude_m)
            for point in sequence
        ]
        total_distance = 0.0
        segment_summaries: list[dict[str, Any]] = []
        for left, right in zip(sequence, sequence[1:]):
            left_projected = Point(*_TO_WEB_MERCATOR.transform(left.longitude, left.latitude))
            right_projected = Point(*_TO_WEB_MERCATOR.transform(right.longitude, right.latitude))
            distance = float(left_projected.distance(right_projected))
            total_distance += distance
            segment_summaries.append(
                {
                    "from": (left.longitude, left.latitude),
                    "to": (right.longitude, right.latitude),
                    "distance_m": round(distance, 3),
                    "node_count": 2,
                }
            )

        path_line = LineString([(point.longitude, point.latitude) for point in path_points]) if len(path_points) >= 2 else None
        return {
            "path": [point.model_dump(mode="json") for point in path_points],
            "geojson": {
                "type": "FeatureCollection",
                "features": [] if path_line is None else [{
                    "type": "Feature",
                    "geometry": mapping(path_line),
                    "properties": {
                        "distance_m": round(total_distance, 3),
                        "segment_count": len(segment_summaries),
                    },
                }],
            },
            "segments": segment_summaries,
            "distance_m": round(total_distance, 3),
            "avoided_zone_ids": [],
        }

    barrier_polygons = _route_polygon_barriers(extra_obstacles)
    graph = nx.Graph()
    node_coordinates = _route_node_coordinates(origin, destinations, barrier_polygons)

    for node_id, coordinate in enumerate(node_coordinates):
        graph.add_node(node_id, coordinate=coordinate)

    for left_id, left_coordinate in enumerate(node_coordinates):
        left_projected = Point(*_TO_WEB_MERCATOR.transform(*left_coordinate))
        for right_id in range(left_id + 1, len(node_coordinates)):
            right_coordinate = node_coordinates[right_id]
            segment = LineString([left_coordinate, right_coordinate])
            if not _segment_clear(segment, barrier_polygons):
                continue
            right_projected = Point(*_TO_WEB_MERCATOR.transform(*right_coordinate))
            weight = float(left_projected.distance(right_projected))
            graph.add_edge(left_id, right_id, weight=weight)

    origin_id = 0
    waypoint_ids = [node_coordinates.index((point.longitude, point.latitude)) for point in destinations]

    full_path_ids = [origin_id]
    total_distance = 0.0
    segment_summaries: list[dict[str, Any]] = []
    current_id = origin_id
    for target_id in waypoint_ids:
        shortest = nx.shortest_path(graph, source=current_id, target=target_id, weight="weight")
        segment_distance = sum(
            float(graph.edges[left_id, right_id]["weight"])
            for left_id, right_id in zip(shortest, shortest[1:])
        )
        total_distance += segment_distance
        if full_path_ids and shortest and full_path_ids[-1] == shortest[0]:
            full_path_ids.extend(shortest[1:])
        else:
            full_path_ids.extend(shortest)
        segment_summaries.append(
            {
                "from": graph.nodes[current_id]["coordinate"],
                "to": graph.nodes[target_id]["coordinate"],
                "distance_m": round(segment_distance, 3),
                "node_count": len(shortest),
            }
        )
        current_id = target_id

    path_points = [
        GeoPoint(latitude=float(graph.nodes[node_id]["coordinate"][1]), longitude=float(graph.nodes[node_id]["coordinate"][0]))
        for node_id in full_path_ids
    ]
    path_line = LineString([(point.longitude, point.latitude) for point in path_points]) if len(path_points) >= 2 else None
    if gpd is None:
        avoided_zone_ids = sorted(
            str(item["id"])
            for item in _geofence_records()
            if path_line is not None
            and not item["geometry"].intersects(path_line)
            and (str(item["type"]) in {"restricted_area", "alert_zone"} or str(item["criticality"]) in {"high", "critical"})
        )
    else:
        avoided_zone_ids = sorted(
            str(row["id"])
            for _, row in geofence_geodataframe().iterrows()
            if path_line is not None and not row.geometry.intersects(path_line) and (str(row["type"]) in {"restricted_area", "alert_zone"} or str(row["criticality"]) in {"high", "critical"})
        )

    return {
        "path": [point.model_dump(mode="json") for point in path_points],
        "geojson": {
            "type": "FeatureCollection",
            "features": [] if path_line is None else [{
                "type": "Feature",
                "geometry": mapping(path_line),
                "properties": {
                    "distance_m": round(total_distance, 3),
                    "segment_count": len(segment_summaries),
                },
            }],
        },
        "segments": segment_summaries,
        "distance_m": round(total_distance, 3),
        "avoided_zone_ids": avoided_zone_ids,
    }


def path_around(position: GeoPoint) -> list[GeoPoint]:
    normalized = normalize_point(position)["position"] or position
    route = LineString(
        [
            (normalized.longitude - 0.0012, normalized.latitude - 0.0011),
            (normalized.longitude - 0.0005, normalized.latitude - 0.0004),
            (normalized.longitude, normalized.latitude),
        ]
    )
    return [
        GeoPoint(latitude=float(latitude), longitude=float(longitude), altitude_m=position.altitude_m)
        for longitude, latitude in route.coords
    ]


def geofence_geojson() -> dict[str, Any]:
    if gpd is None:
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": str(item["id"]),
                    "geometry": mapping(item["geometry"]),
                    "properties": {
                        "name": str(item["name"]),
                        "type": str(item["type"]),
                        "zone": str(item["zone"]),
                        "criticality": str(item["criticality"]),
                    },
                }
                for item in _geofence_records()
            ],
        }

    geofences = geofence_geodataframe()
    return json.loads(geofences.to_json())


def _fetch_nominatim_results(query: str, limit: int) -> list[dict[str, Any]]:
    encoded_query = parse.urlencode({"q": query, "format": "jsonv2", "limit": limit})
    req = request.Request(
        url=f"https://nominatim.openstreetmap.org/search?{encoded_query}",
        headers={"User-Agent": "ORCA-GeographicEngine/1.0"},
    )
    try:
        with request.urlopen(req, timeout=4) as response:
            payload = json.loads(response.read().decode("utf-8") or "[]")
    except Exception:
        return []
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def _fallback_search_results(query: str) -> list[dict[str, Any]]:
    tokens = [token.strip().lower() for token in query.replace("->", " ").split() if token.strip()]
    if not tokens:
        return []
    matches = []
    for item in LOCAL_SEARCH_INDEX:
        haystack = f"{item['name']} {item['display_name']} {item['zone']}".lower()
        if all(token in haystack for token in tokens):
            matches.append(item)
    return matches


def search_locations(query: str, radius_km: float = 2.0, limit: int = 5) -> dict[str, Any]:
    raw_results = _fetch_nominatim_results(query, limit)
    source = "nominatim"
    if not raw_results:
        raw_results = _fallback_search_results(query)
        source = "fallback-index"

    records: list[dict[str, Any]] = []
    for item in raw_results[:limit]:
        latitude = float(item.get("lat", item.get("latitude")))
        longitude = float(item.get("lon", item.get("longitude")))
        records.append(
            {
                "name": str(item.get("name") or item.get("display_name") or query),
                "type": str(item.get("type") or item.get("addresstype") or "search_result"),
                "zone": str(item.get("zone") or item.get("address", {}).get("city") or "search"),
                "timestamp": None,
                "display_name": str(item.get("display_name") or item.get("name") or query),
                "geometry": Point(longitude, latitude),
            }
        )

    result_gdf = _build_geodataframe(records) if records else _build_geodataframe([])
    radius_geojson: dict[str, Any] | None = None
    if not result_gdf.empty:
        projected = result_gdf.to_crs(WEB_MERCATOR_CRS)
        first_geometry = projected.geometry.iloc[0]
        radius_polygon = first_geometry.buffer(radius_km * 1000)
        radius_geojson = mapping(radius_polygon)

    return {
        "query": query,
        "radius_km": radius_km,
        "source": source,
        "results": [
            {
                "name": str(row["name"]),
                "display_name": str(row["display_name"]),
                "type": str(row["type"]),
                "zone": str(row["zone"]),
                "geometry": mapping(row.geometry),
            }
            for _, row in result_gdf.iterrows()
        ],
        "geojson": json.loads(result_gdf.to_json()) if not result_gdf.empty else {"type": "FeatureCollection", "features": []},
        "radius": radius_geojson,
    }


def render_city_map(
    *,
    drone_overlays: list[MapOverlay] | None = None,
    sensor_overlays: list[MapOverlay] | None = None,
    threat_overlays: list[MapOverlay] | None = None,
    geofence_overlays_list: list[MapOverlay] | None = None,
) -> dict[str, Any]:
    if folium is None:
        raise RuntimeError("folium is required for map rendering")

    center_lat, center_lon = _city_reference_center()
    city_map = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="OpenStreetMap")
    persisted_dataset = fetch_persisted_geographic_dataset() or {}

    overlays_by_type = {
        "drones": drone_overlays or [],
        "sensors": sensor_overlays or [],
        "threats": threat_overlays or [],
        "geofences": geofence_overlays_list or geofence_overlays(),
    }

    folium.GeoJson(geofence_geojson(), name="geofences").add_to(city_map)

    for mission_route in persisted_dataset.get("mission_routes", []):
        geometry = mission_route.get("geometry", {})
        if geometry.get("type") == "LineString":
            folium.PolyLine(
                [(latitude, longitude) for longitude, latitude in geometry.get("coordinates", [])],
                tooltip=mission_route.get("name", "Mission route"),
            ).add_to(city_map)

    for path_feature in persisted_dataset.get("drone_paths", []) + persisted_dataset.get("robot_paths", []):
        geometry = path_feature.get("geometry", {})
        if geometry.get("type") == "LineString":
            folium.PolyLine(
                [(latitude, longitude) for longitude, latitude in geometry.get("coordinates", [])],
                tooltip=path_feature.get("name", "Asset path"),
                color="#8fb6ff" if path_feature.get("feature_type") == "drone_path" else "#6be3a8",
            ).add_to(city_map)

    for feature_group in (persisted_dataset.get("sensors", []), persisted_dataset.get("cameras", [])):
        for feature in feature_group:
            geometry = feature.get("geometry", {})
            coordinates = geometry.get("coordinates", [])
            if geometry.get("type") == "Point" and len(coordinates) == 2:
                folium.CircleMarker(
                    location=[coordinates[1], coordinates[0]],
                    radius=5,
                    tooltip=feature.get("name", "Geographic asset"),
                    fill=True,
                ).add_to(city_map)

    marker_layers: dict[str, list[dict[str, Any]]] = {key: [] for key in overlays_by_type}
    for layer_name, overlays in overlays_by_type.items():
        for overlay in overlays:
            if overlay.position is not None:
                folium.Marker(
                    location=[overlay.position.latitude, overlay.position.longitude],
                    tooltip=overlay.label,
                    popup=overlay.label,
                ).add_to(city_map)
                marker_layers[layer_name].append(
                    {
                        "overlay_id": overlay.overlay_id,
                        "label": overlay.label,
                        "latitude": overlay.position.latitude,
                        "longitude": overlay.position.longitude,
                    }
                )
            if overlay.path:
                folium.PolyLine([(point.latitude, point.longitude) for point in overlay.path], tooltip=overlay.label).add_to(city_map)

    folium.LayerControl().add_to(city_map)
    return {
        "html": city_map.get_root().render(),
        "geojson_layers": {
            "geofences": geofence_geojson(),
            "search_radius": None,
            "sensors": _point_features_geojson("sensor"),
            "cameras": _point_features_geojson("camera"),
            "drone_paths": _line_features_geojson("drone_path"),
            "robot_paths": _line_features_geojson("robot_path"),
            "mission_routes": persisted_dataset.get("geojson_layers", {}).get("mission_route", {"type": "FeatureCollection", "features": []}),
        },
        "marker_layers": marker_layers,
    }
