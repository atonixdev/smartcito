from __future__ import annotations

import asyncio
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_session
from app.main import app
from app.services.ai_client import ai_client
from app.services.cache import CacheKeyBuilder, cache_service
from app.services.ingestion import ingestion_service


class FakeMemcacheClient:
    def __init__(self) -> None:
        self.store: dict[str, bytes] = {}

    def get(self, key: str) -> bytes | None:
        return self.store.get(key)

    def set(self, key: str, value: bytes, expire: int = 0) -> None:
        self.store[key] = value

    def delete(self, key: str) -> None:
        self.store.pop(key, None)


class FakeAIResponse:
    def __init__(self, payload: dict[str, object] | None = None) -> None:
        self._payload = payload or {"score": 0.91}

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self._payload


class FakeAIAsyncClient:
    calls: list[tuple[str, dict[str, object]]] = []

    def __init__(self, *args, **kwargs) -> None:  # noqa: D401, ANN003
        pass

    async def __aenter__(self) -> FakeAIAsyncClient:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        return None

    async def post(self, url: str, json: dict[str, object]) -> FakeAIResponse:
        self.calls.append((url, json))
        if url.endswith("/detect_objects"):
            return FakeAIResponse(
                {
                    "backend": "heuristic",
                    "requested_backend": str(json.get("backend", "auto")),
                    "image_width": 20,
                    "image_height": 20,
                    "detections": [
                        {
                            "label": "vehicle",
                            "confidence": 0.91,
                            "bbox": [1, 2, 8, 10],
                            "area_ratio": 0.18,
                        }
                    ],
                }
            )
        return FakeAIResponse()


@contextmanager
def _use_fake_cache() -> Generator[FakeMemcacheClient, None, None]:
    original_enabled = cache_service._enabled
    original_client = cache_service._client
    fake_client = FakeMemcacheClient()
    cache_service._enabled = True
    cache_service._client = fake_client
    try:
        yield fake_client
    finally:
        cache_service._enabled = original_enabled
        cache_service._client = original_client


def test_cache_key_builder_uses_shared_naming() -> None:
    assert CacheKeyBuilder.build("api", "user", "12345") == "api:user:12345"


@pytest.fixture()
def db_client(tmp_path: Path) -> Generator[TestClient, None, None]:
    db_path = tmp_path / "cache-layer.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

    async def _override_get_session():
        async with session_factory() as session:
            yield session

    async def _setup() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def _teardown() -> None:
        await engine.dispose()

    asyncio.run(_setup())
    app.dependency_overrides[get_session] = _override_get_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    asyncio.run(_teardown())


def _auth_headers(role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=f'{role}@orca.dev', role=role)}"}


def test_login_reuses_cached_session_token() -> None:
    with _use_fake_cache():
        client = TestClient(app)
        response_a = client.post(
            "/api/v1/auth/token",
            data={"username": "admin@orca.dev", "password": "changeme"},
        )
        response_b = client.post(
            "/api/v1/auth/token",
            data={"username": "admin@orca.dev", "password": "changeme"},
        )

        assert response_a.status_code == 200
        assert response_b.status_code == 200
        assert response_a.json()["access_token"] == response_b.json()["access_token"]


def test_recent_sensor_readings_are_cached_and_invalidated() -> None:
    with _use_fake_cache() as fake_cache:
        ingestion_service._buffer.clear()
        client = TestClient(app)
        operator_headers = _auth_headers("operator")
        viewer_headers = _auth_headers("viewer")

        first_ingest_response = client.post(
            "/api/v1/sensors",
            json={
                "sensor_id": "traffic-001",
                "kind": "traffic",
                "value": 21.5,
                "unit": "vehicles/min",
                "metadata": {},
            },
            headers=operator_headers,
        )
        assert first_ingest_response.status_code == 201

        cache_key = CacheKeyBuilder.build("api", "sensor-readings", "recent-50")
        first_recent = client.get("/api/v1/sensors/recent", headers=viewer_headers)
        second_recent = client.get("/api/v1/sensors/recent", headers=viewer_headers)

        assert first_recent.status_code == 200
        assert second_recent.status_code == 200
        assert cache_key in fake_cache.store

        second_ingest_response = client.post(
            "/api/v1/sensors",
            json={
                "sensor_id": "traffic-002",
                "kind": "traffic",
                "value": 18.0,
                "unit": "vehicles/min",
                "metadata": {},
            },
            headers=operator_headers,
        )
        assert second_ingest_response.status_code == 201
        assert cache_key not in fake_cache.store


def test_camera_listing_is_cached_and_invalidated(db_client: TestClient) -> None:
    with _use_fake_cache() as fake_cache:
        registration = {
            "device_id": "body-002",
            "device_type": "body_camera",
            "firmware_version": "1.0.1",
            "capabilities": {
                "gps": True,
                "tamper_detection": True,
                "mount_detection": True,
                "stream_protocols": ["rtsp"],
                "local_encrypted_storage": True,
            },
            "network": {"transport": "5g", "signal_profile": "mobile"},
            "security": {"identity_mode": "secure_element", "tls_required": True, "storage_encryption": "aes-256"},
            "mounting": {"magnetic_base": True, "mount_sensor_type": "hall_effect"},
        }

        create_res = db_client.post("/api/v1/cameras/register", json=registration, headers=_auth_headers("operator"))
        assert create_res.status_code == 201

        first_list = db_client.get("/api/v1/cameras", headers=_auth_headers("viewer"))
        second_list = db_client.get("/api/v1/cameras", headers=_auth_headers("viewer"))

        assert first_list.status_code == 200
        assert second_list.status_code == 200
        fleet_key = CacheKeyBuilder.build("device", "camera-fleet", "list")
        assert fleet_key in fake_cache.store

        telemetry_res = db_client.post(
            "/api/v1/cameras/body-002/telemetry",
            json={
                "stream_status": "live",
                "mounted": True,
                "tamper_detected": False,
                "battery_level": 92,
                "location": {"lat": -25.7, "lon": 28.2, "accuracy_m": 3.0},
            },
            headers=_auth_headers("operator"),
        )
        assert telemetry_res.status_code == 200
        assert fleet_key not in fake_cache.store


def test_historical_analytics_is_cached_and_invalidated(db_client: TestClient) -> None:
    with _use_fake_cache() as fake_cache:
        for sensor_id, value in (("traffic-010", 12.5), ("traffic-011", 8.5)):
            response = db_client.post(
                "/api/v1/sensors",
                json={
                    "sensor_id": sensor_id,
                    "kind": "traffic",
                    "value": value,
                    "unit": "vehicles/min",
                    "metadata": {},
                },
                headers=_auth_headers("operator"),
            )
            assert response.status_code == 201

        first_history = db_client.get("/api/v1/events/history", headers=_auth_headers("viewer"))
        second_history = db_client.get("/api/v1/events/history", headers=_auth_headers("viewer"))

        assert first_history.status_code == 200
        assert second_history.status_code == 200
        history_key = CacheKeyBuilder.build("api", "historical-analytics", "history-20")
        assert history_key in fake_cache.store

        new_event = db_client.post(
            "/api/v1/sensors",
            json={
                "sensor_id": "traffic-012",
                "kind": "traffic",
                "value": 14.0,
                "unit": "vehicles/min",
                "metadata": {},
            },
            headers=_auth_headers("operator"),
        )
        assert new_event.status_code == 201
        assert history_key not in fake_cache.store


def test_ai_inference_results_are_cached(monkeypatch) -> None:
    FakeAIAsyncClient.calls.clear()
    with _use_fake_cache():
        import httpx

        monkeypatch.setattr(httpx, "AsyncClient", FakeAIAsyncClient)
        first = asyncio.run(ai_client.score_anomaly([1.0, 2.0, 3.0]))
        second = asyncio.run(ai_client.score_anomaly([1.0, 2.0, 3.0]))

        assert first == 0.91
        assert second == 0.91
        assert len(FakeAIAsyncClient.calls) == 1


def test_ai_object_detection_results_are_cached(monkeypatch) -> None:
    FakeAIAsyncClient.calls.clear()
    with _use_fake_cache():
        import httpx

        monkeypatch.setattr(httpx, "AsyncClient", FakeAIAsyncClient)
        first = asyncio.run(ai_client.detect_objects(image_b64="AA==", labels=["vehicle"], threshold=0.5))
        second = asyncio.run(ai_client.detect_objects(image_b64="AA==", labels=["vehicle"], threshold=0.5))

        assert first["detections"][0]["label"] == "vehicle"
        assert second["detections"][0]["confidence"] == 0.91
        assert len(FakeAIAsyncClient.calls) == 1