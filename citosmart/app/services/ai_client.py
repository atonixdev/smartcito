"""
================================================================================
 File: app/services/ai_client.py
 Purpose:
   REST client for SmartCito AI inference services.
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


ai_client = AIClient()