"""
================================================================================
 File: app/services/gps_realtime_gateway.py
 Purpose:
   In-memory + Redis-assisted realtime GPS fanout for dashboard WebSockets.
================================================================================
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from typing import Any

from redis.asyncio import Redis

from app.core.config import get_settings

VALID_GPS_CHANNELS = {"global", "drone", "robot", "city", "mission", "individualization"}


class GPSRealtimeGatewayService:
    """Publishes GPS updates to per-dashboard channels and caches latest state."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._subscribers: dict[str, set[asyncio.Queue[dict[str, Any]]]] = {
            channel: set() for channel in VALID_GPS_CHANNELS
        }
        self._latest: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        self._redis: Redis | None = None

    def normalize_channel(self, value: str | None) -> str:
        channel = (value or "global").strip().lower()
        return channel if channel in VALID_GPS_CHANNELS else "global"

    def channel_for_device_type(self, device_type: str | None) -> str:
        lowered = (device_type or "unknown").strip().lower()
        if lowered in {"drone", "uav"}:
            return "drone"
        if lowered in {"robot", "ugv"}:
            return "robot"
        if lowered in {"camera", "sensor", "iot", "vehicle"}:
            return "city"
        return "global"

    async def subscribe(self, channel: str) -> asyncio.Queue[dict[str, Any]]:
        normalized = self.normalize_channel(channel)
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=4096)
        async with self._lock:
            self._subscribers[normalized].add(queue)
        return queue

    async def unsubscribe(self, channel: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
        normalized = self.normalize_channel(channel)
        async with self._lock:
            self._subscribers[normalized].discard(queue)

    async def publish(self, payload: dict[str, Any]) -> None:
        channel = self.normalize_channel(str(payload.get("channel", "global")))
        payload["channel"] = channel

        async with self._lock:
            self._latest[str(payload["device_id"])] = payload

        await self._cache_latest(payload)

        await self._fanout(channel, payload)
        if channel != "global":
            await self._fanout("global", payload)

    async def snapshot(self, channel: str) -> list[dict[str, Any]]:
        normalized = self.normalize_channel(channel)

        redis_rows = await self._snapshot_from_redis()
        rows = redis_rows if redis_rows else list(self._latest.values())

        if normalized == "global":
            return rows
        return [row for row in rows if row.get("channel") == normalized]

    async def _fanout(self, channel: str, payload: dict[str, Any]) -> None:
        async with self._lock:
            queues = list(self._subscribers[self.normalize_channel(channel)])

        for queue in queues:
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                try:
                    _ = queue.get_nowait()
                    queue.put_nowait(payload)
                except Exception:  # nosec B112
                    continue

    async def _redis_client(self) -> Redis | None:
        if self._redis is not None:
            return self._redis

        try:
            self._redis = Redis.from_url(
                self._settings.redis_url, encoding="utf-8", decode_responses=True
            )
            await self._redis.ping()
            return self._redis
        except Exception:
            self._redis = None
            return None

    async def _cache_latest(self, payload: dict[str, Any]) -> None:
        redis = await self._redis_client()
        if redis is None:
            return

        try:
            device_id = str(payload["device_id"])
            await redis.hset(
                "orca:gps:live", device_id, json.dumps(payload, separators=(",", ":"), default=str)
            )
            await redis.expire("orca:gps:live", 24 * 60 * 60)
        except Exception:
            return

    async def _snapshot_from_redis(self) -> list[dict[str, Any]]:
        redis = await self._redis_client()
        if redis is None:
            return []

        try:
            rows = await redis.hgetall("orca:gps:live")
        except Exception:
            return []

        parsed: list[dict[str, Any]] = []
        for value in rows.values():
            try:
                parsed.append(json.loads(value))
            except Exception:  # nosec B112
                continue
        return parsed


def now_utc_iso() -> str:
    return datetime.now(UTC).isoformat()


gps_realtime_gateway_service = GPSRealtimeGatewayService()
