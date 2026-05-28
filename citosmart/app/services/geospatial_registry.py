"""
================================================================================
 File: citosmart/app/services/geospatial_registry.py
 Purpose:
   DB-backed geospatial registry for geofences, zones, sensors, cameras, and
   mission routes, persisted in PostGIS-compatible form with GeoJSON output.
================================================================================
"""

from __future__ import annotations

from datetime import datetime

from geoalchemy2.shape import from_shape
from shapely.geometry import shape
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.crypto import build_integrity_record
from app.db.models import GeoFeatureORM
from app.schemas.geospatial import GeoDatasetOut, GeoFeatureCollection, GeoFeatureIn, GeoFeatureOut, GeoFeatureType


class GeospatialRegistryService:
    """Persistence layer for geographic assets shared across Orca."""

    async def upsert_feature(self, session: AsyncSession, feature: GeoFeatureIn) -> GeoFeatureOut:
        record = await session.scalar(select(GeoFeatureORM).where(GeoFeatureORM.feature_id == feature.feature_id))
        geometry_geojson = feature.geometry.model_dump(mode="json")
        geometry_value = self._geometry_value(session, geometry_geojson)
        now = datetime.utcnow()

        if record is None:
            record = GeoFeatureORM(
                feature_id=feature.feature_id,
                name=feature.name,
                feature_type=feature.feature_type.value,
                zone=feature.zone,
                geometry_type=feature.geometry.type.value,
                geometry_geojson=geometry_geojson,
                geometry=geometry_value,
                properties=feature.properties,
                source_service=feature.source_service,
                timestamp=feature.timestamp,
                created_at=now,
                updated_at=now,
            )
            session.add(record)
        else:
            record.name = feature.name
            record.feature_type = feature.feature_type.value
            record.zone = feature.zone
            record.geometry_type = feature.geometry.type.value
            record.geometry_geojson = geometry_geojson
            record.geometry = geometry_value
            record.properties = feature.properties
            record.source_service = feature.source_service
            record.timestamp = feature.timestamp
            record.updated_at = now

        await session.commit()
        return self._to_schema(record)

    async def list_features(self, session: AsyncSession, *, feature_type: GeoFeatureType | None = None) -> list[GeoFeatureOut]:
        statement = select(GeoFeatureORM).order_by(GeoFeatureORM.updated_at.desc())
        if feature_type is not None:
            statement = statement.where(GeoFeatureORM.feature_type == feature_type.value)
        rows = await session.scalars(statement)
        features = [self._to_schema(record) for record in rows.all()]
        if features:
            return features
        return await self.seed_demo_features(session)

    async def delete_feature(self, session: AsyncSession, feature_id: str) -> bool:
        record = await session.scalar(select(GeoFeatureORM).where(GeoFeatureORM.feature_id == feature_id))
        if record is None:
            return False
        await session.delete(record)
        await session.commit()
        return True

    async def dataset(self, session: AsyncSession) -> GeoDatasetOut:
        rows = await self.list_features(session)
        grouped = {
            GeoFeatureType.GEOFENCE.value: [],
            GeoFeatureType.ZONE.value: [],
            GeoFeatureType.SENSOR.value: [],
            GeoFeatureType.CAMERA.value: [],
            GeoFeatureType.DRONE_PATH.value: [],
            GeoFeatureType.ROBOT_PATH.value: [],
            GeoFeatureType.MISSION_ROUTE.value: [],
        }
        for row in rows:
            grouped[row.feature_type.value].append(row)

        return GeoDatasetOut(
            geofences=grouped[GeoFeatureType.GEOFENCE.value],
            zones=grouped[GeoFeatureType.ZONE.value],
            sensors=grouped[GeoFeatureType.SENSOR.value],
            cameras=grouped[GeoFeatureType.CAMERA.value],
            drone_paths=grouped[GeoFeatureType.DRONE_PATH.value],
            robot_paths=grouped[GeoFeatureType.ROBOT_PATH.value],
            mission_routes=grouped[GeoFeatureType.MISSION_ROUTE.value],
            geojson_layers={key: self._feature_collection(items) for key, items in grouped.items()},
        )

    async def seed_demo_features(self, session: AsyncSession) -> list[GeoFeatureOut]:
        settings = get_settings()
        if settings.is_production:
            return []

        count = await session.scalar(select(func.count()).select_from(GeoFeatureORM))
        if count and count > 0:
            rows = await session.scalars(select(GeoFeatureORM).order_by(GeoFeatureORM.updated_at.desc()))
            return [self._to_schema(record) for record in rows.all()]

        demo_features = [
            GeoFeatureIn(
                feature_id="geo-zone-1-cbd",
                name="CBD Operations Zone",
                feature_type=GeoFeatureType.GEOFENCE,
                zone="cbd",
                geometry={"type": "Polygon", "coordinates": [[[28.2180, -25.7550], [28.2360, -25.7550], [28.2360, -25.7420], [28.2180, -25.7420], [28.2180, -25.7550]]]},
                properties={"criticality": "high"},
                source_service="system:demo-seed",
            ),
            GeoFeatureIn(
                feature_id="geo-zone-2-transport",
                name="Transport Corridor",
                feature_type=GeoFeatureType.ZONE,
                zone="transport",
                geometry={"type": "Polygon", "coordinates": [[[28.1700, -25.7600], [28.2050, -25.7600], [28.2050, -25.7350], [28.1700, -25.7350], [28.1700, -25.7600]]]},
                properties={"criticality": "medium"},
                source_service="system:demo-seed",
            ),
            GeoFeatureIn(
                feature_id="geo-sensor-em-001",
                name="Magnetic Wave Grid A1",
                feature_type=GeoFeatureType.SENSOR,
                zone="cbd",
                geometry={"type": "Point", "coordinates": [28.2455, -25.7448]},
                properties={"sensor_type": "magnetic/em", "unit": "mT"},
                source_service="system:demo-seed",
            ),
            GeoFeatureIn(
                feature_id="geo-camera-demo-body-001",
                name="Pretoria Camera Node",
                feature_type=GeoFeatureType.CAMERA,
                zone="cbd",
                geometry={"type": "Point", "coordinates": [28.2293, -25.7479]},
                properties={"camera_feed_url": "rtsp://fleet/demo-body-001"},
                source_service="system:demo-seed",
            ),
            GeoFeatureIn(
                feature_id="geo-route-cbd-perimeter",
                name="CBD perimeter patrol",
                feature_type=GeoFeatureType.MISSION_ROUTE,
                zone="cbd",
                geometry={"type": "LineString", "coordinates": [[28.2281, -25.7490], [28.2293, -25.7479], [28.2361, -25.7461], [28.2438, -25.7454]]},
                properties={"asset_type": "drone", "asset_id": "drone-patrol-001"},
                source_service="system:demo-seed",
            ),
            GeoFeatureIn(
                feature_id="geo-drone-path-patrol-001",
                name="Drone patrol live path",
                feature_type=GeoFeatureType.DRONE_PATH,
                zone="cbd",
                geometry={"type": "LineString", "coordinates": [[28.2275, -25.7495], [28.2310, -25.7481], [28.2388, -25.7460], [28.2438, -25.7454]]},
                properties={"asset_type": "drone", "asset_id": "drone-patrol-001", "path_kind": "live"},
                source_service="system:demo-seed",
            ),
            GeoFeatureIn(
                feature_id="geo-robot-path-patrol-001",
                name="Robot perimeter live path",
                feature_type=GeoFeatureType.ROBOT_PATH,
                zone="cbd",
                geometry={"type": "LineString", "coordinates": [[28.2287, -25.7488], [28.2299, -25.7481], [28.2322, -25.7474], [28.2346, -25.7467]]},
                properties={"asset_type": "robot", "asset_id": "robot-cap-001", "path_kind": "live"},
                source_service="system:demo-seed",
            ),
        ]

        persisted: list[GeoFeatureOut] = []
        for feature in demo_features:
            persisted.append(await self.upsert_feature(session, feature))
        return persisted

    def _geometry_value(self, session: AsyncSession, geometry_geojson: dict) -> object:
        bind = session.get_bind()
        if bind is not None and bind.dialect.name == "postgresql":
            return from_shape(shape(geometry_geojson), srid=4326)
        return geometry_geojson

    def _to_schema(self, record: GeoFeatureORM) -> GeoFeatureOut:
        signable_payload = {
            "feature_id": record.feature_id,
            "name": record.name,
            "feature_type": record.feature_type,
            "zone": record.zone,
            "geometry": record.geometry_geojson,
            "properties": record.properties,
            "source_service": record.source_service,
            "timestamp": record.timestamp.isoformat() if record.timestamp else None,
        }
        return GeoFeatureOut(
            id=record.id,
            feature_id=record.feature_id,
            name=record.name,
            feature_type=GeoFeatureType(record.feature_type),
            zone=record.zone,
            geometry=record.geometry_geojson,
            properties=record.properties,
            source_service=record.source_service,
            timestamp=record.timestamp,
            integrity=build_integrity_record(signable_payload, signer_id="citosmart-geospatial-registry"),
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def _feature_collection(self, rows: list[GeoFeatureOut]) -> GeoFeatureCollection:
        return GeoFeatureCollection(
            features=[
                {
                    "type": "Feature",
                    "id": row.feature_id,
                    "geometry": row.geometry.model_dump(mode="json"),
                    "properties": {
                        "name": row.name,
                        "feature_type": row.feature_type.value,
                        "zone": row.zone,
                        **row.properties,
                    },
                }
                for row in rows
            ]
        )


geospatial_registry_service = GeospatialRegistryService()