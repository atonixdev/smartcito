from __future__ import annotations

import os

import httpx


class SurveillanceAIClient:
    def __init__(self) -> None:
        self._base_url = os.getenv("ORCA_AI_MODELS_URL", "http://ai-service:8012").rstrip("/")

    async def detect_objects(
        self,
        *,
        image_b64: str,
        backend: str = "auto",
        labels: list[str] | None = None,
        threshold: float = 0.6,
    ) -> dict[str, object]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self._base_url}/detect_objects",
                json={
                    "image_b64": image_b64,
                    "backend": backend,
                    "labels": labels or ["motion-object"],
                    "threshold": threshold,
                },
            )
            response.raise_for_status()
            return response.json()


ai_client = SurveillanceAIClient()