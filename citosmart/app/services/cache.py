"""Shared Memcached-backed cache helpers for Orca services."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Any

from prometheus_client import Counter
from pymemcache.client.hash import HashClient
from pymemcache.exceptions import MemcacheError

from app.core.config import get_settings

logger = logging.getLogger(__name__)

CACHE_HITS = Counter("orca_cache_hits_total", "Total Orca cache hits", ["purpose"])
CACHE_MISSES = Counter("orca_cache_misses_total", "Total Orca cache misses", ["purpose"])
CACHE_STORES = Counter("orca_cache_stores_total", "Total Orca cache writes", ["purpose"])
CACHE_INVALIDATIONS = Counter(
    "orca_cache_invalidations_total",
    "Total Orca cache invalidations",
    ["purpose"],
)
CACHE_ERRORS = Counter("orca_cache_errors_total", "Total Orca cache errors", ["operation"])


@dataclass(frozen=True)
class CachePolicy:
    ttl_seconds: int
    purpose: str


class CachePolicies:
    def __init__(self) -> None:
        settings = get_settings()
        self.default = CachePolicy(settings.memcached_default_ttl_seconds, "general")
        self.api = CachePolicy(settings.memcached_api_ttl_seconds, "api-response")
        self.dashboard = CachePolicy(settings.memcached_dashboard_ttl_seconds, "dashboard-summary")
        self.device_metadata = CachePolicy(settings.memcached_device_metadata_ttl_seconds, "device-metadata")
        self.ai = CachePolicy(settings.memcached_ai_ttl_seconds, "ai-inference")
        self.session = CachePolicy(settings.memcached_session_ttl_seconds, "session-token")


class CacheKeyBuilder:
    @staticmethod
    def build(service: str, domain: str, identifier: str) -> str:
        return f"{service}:{domain}:{identifier}"

    @staticmethod
    def hashed_identifier(prefix: str, payload: Any) -> str:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        digest = hashlib.sha256(encoded).hexdigest()[:16]
        return f"{prefix}-{digest}"


class MemcachedCacheService:
    def __init__(self) -> None:
        settings = get_settings()
        self._enabled = bool(settings.memcached_servers.strip())
        self._policies = CachePolicies()
        self._client: HashClient | None = None

        if self._enabled:
            servers = []
            for endpoint in settings.memcached_servers.split(","):
                host, _, port = endpoint.strip().partition(":")
                if host and port:
                    servers.append((host, int(port)))

            if servers:
                self._client = HashClient(servers, connect_timeout=1.0, timeout=1.0, no_delay=True)
            else:
                self._enabled = False

    @property
    def policies(self) -> CachePolicies:
        return self._policies

    def is_enabled(self) -> bool:
        return self._enabled and self._client is not None

    def get_json(self, key: str) -> Any | None:
        if not self.is_enabled():
            return None

        purpose = self._purpose_for_key(key)

        try:
            raw = self._client.get(key)  # type: ignore[union-attr]
        except (MemcacheError, OSError) as exc:
            self._record_cache_error("get", key, exc)
            return None

        if raw is None:
            CACHE_MISSES.labels(purpose=purpose).inc()
            logger.info("cache miss key=%s", key)
            return None

        CACHE_HITS.labels(purpose=purpose).inc()
        logger.info("cache hit key=%s", key)
        return json.loads(raw.decode("utf-8"))

    def set_json(self, key: str, value: Any, policy: CachePolicy | None = None) -> None:
        if not self.is_enabled():
            return

        effective_policy = policy or self._policies.default
        try:
            payload = json.dumps(value, separators=(",", ":")).encode("utf-8")
            self._client.set(key, payload, expire=effective_policy.ttl_seconds)  # type: ignore[union-attr]
            CACHE_STORES.labels(purpose=effective_policy.purpose).inc()
            logger.info(
                "cache store key=%s ttl=%s purpose=%s",
                key,
                effective_policy.ttl_seconds,
                effective_policy.purpose,
            )
        except (MemcacheError, OSError, TypeError, ValueError) as exc:
            if isinstance(exc, (TypeError, ValueError)):
                CACHE_ERRORS.labels(operation="set").inc()
                logger.warning("Memcached set failed for %s: %s", key, exc)
                return
            self._record_cache_error("set", key, exc)

    def delete(self, key: str) -> None:
        if not self.is_enabled():
            return

        purpose = self._purpose_for_key(key)

        try:
            self._client.delete(key)  # type: ignore[union-attr]
            CACHE_INVALIDATIONS.labels(purpose=purpose).inc()
            logger.info("cache invalidate key=%s", key)
        except (MemcacheError, OSError) as exc:
            self._record_cache_error("delete", key, exc)

    def delete_many(self, keys: list[str]) -> None:
        for key in keys:
            self.delete(key)

    def _purpose_for_key(self, key: str) -> str:
        if ":session:" in key:
            return self._policies.session.purpose
        if key.startswith("ai:"):
            return self._policies.ai.purpose
        if key.startswith("device:"):
            return self._policies.device_metadata.purpose
        if key.startswith("dashboard:") or "dashboard-summary" in key:
            return self._policies.dashboard.purpose
        return self._policies.api.purpose

    def _record_cache_error(self, operation: str, key: str, exc: Exception) -> None:
        CACHE_ERRORS.labels(operation=operation).inc()
        logger.warning("Memcached %s failed for %s: %s", operation, key, exc)
        self._enabled = False
        self._client = None


cache_service = MemcachedCacheService()