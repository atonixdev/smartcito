"""
================================================================================
 File: ai_models/inference.py
 Purpose:
   Minimal FastAPI inference service for SmartCito AI contributors.
================================================================================
"""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from ai_models.model import score_anomaly

app = FastAPI(title="SmartCito AI Models")


class InferenceRequest(BaseModel):
    """Request payload for simple anomaly scoring."""

    features: list[float] = Field(default_factory=list)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-models"}


@app.post("/infer")
async def infer(request: InferenceRequest) -> dict[str, float]:
    return {"score": score_anomaly(request.features)}
