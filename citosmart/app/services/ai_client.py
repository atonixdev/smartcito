"""
================================================================================
 File: app/services/ai_client.py
 Purpose:
   REST client for Orca AI inference services.
================================================================================
"""

from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.services.cache import CacheKeyBuilder, cache_service


class AIClient:
    def __init__(self) -> None:
        self._base_url = get_settings().ai_models_url.rstrip("/")

    async def score_anomaly(self, features: list[float]) -> float:
        cache_key = CacheKeyBuilder.build(
            "ai",
            "prediction",
            CacheKeyBuilder.hashed_identifier("features", features),
        )
        cached = cache_service.get_json(cache_key)
        if cached is not None and "score" in cached:
            return float(cached["score"])

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(f"{self._base_url}/infer", json={"features": features})
            response.raise_for_status()
            payload = response.json()
            score = float(payload.get("score", 0.0))
            cache_service.set_json(cache_key, {"score": score}, cache_service.policies.ai)
            return score

    async def classify_alert(
        self,
        *,
        message: str,
        source: str | None = None,
        tags: list[str] | None = None,
        anomaly_score: float | None = None,
    ) -> dict[str, object]:
        payload = {
            "message": message,
            "source": source,
            "tags": tags or [],
            "anomaly_score": anomaly_score,
        }
        cache_key = CacheKeyBuilder.build(
            "ai",
            "alert-classification",
            CacheKeyBuilder.hashed_identifier("alert", payload),
        )
        cached = cache_service.get_json(cache_key)
        if cached is not None:
            return cached

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(f"{self._base_url}/classify_alert", json=payload)
            response.raise_for_status()
            classification = response.json()
            cache_service.set_json(cache_key, classification, cache_service.policies.ai)
            return classification

    async def summarize_event(
        self,
        *,
        title: str | None = None,
        classification: str | None = None,
        severity: str | None = None,
        location: str | None = None,
        alerts: list[str] | None = None,
        sensor_readings: dict[str, float] | None = None,
        max_sentences: int = 2,
    ) -> str:
        payload = {
            "title": title,
            "classification": classification,
            "severity": severity,
            "location": location,
            "alerts": alerts or [],
            "sensor_readings": sensor_readings or {},
            "max_sentences": max_sentences,
        }
        cache_key = CacheKeyBuilder.build(
            "ai",
            "event-summary",
            CacheKeyBuilder.hashed_identifier("summary", payload),
        )
        cached = cache_service.get_json(cache_key)
        if cached is not None and "summary" in cached:
            return str(cached["summary"])

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(f"{self._base_url}/summarize_event", json=payload)
            response.raise_for_status()
            summary_payload = response.json()
            cache_service.set_json(cache_key, summary_payload, cache_service.policies.ai)
            return str(summary_payload.get("summary", ""))

    async def detect_objects(
        self,
        *,
        image_b64: str,
        backend: str = "auto",
        labels: list[str] | None = None,
        threshold: float = 0.6,
    ) -> dict[str, object]:
        payload = {
            "image_b64": image_b64,
            "backend": backend,
            "labels": labels or ["motion-object"],
            "threshold": threshold,
        }
        cache_key = CacheKeyBuilder.build(
            "ai",
            "object-detection",
            CacheKeyBuilder.hashed_identifier("detect", payload),
        )
        cached = cache_service.get_json(cache_key)
        if cached is not None:
            return cached

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{self._base_url}/detect_objects", json=payload)
            response.raise_for_status()
            detections = response.json()
            cache_service.set_json(cache_key, detections, cache_service.policies.ai)
            return detections


ai_client = AIClient()