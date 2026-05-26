"""
================================================================================
 File: ai_models/inference.py
 Purpose:
   Minimal FastAPI inference service for SmartCito AI contributors.
================================================================================
"""

from __future__ import annotations

from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from ai_models.llama_stack import generate_text, list_models, load_llama_stack_settings
from ai_models.model import classify_alert, detect_objects, score_anomaly, summarize_event


load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

app = FastAPI(title="SmartCito AI Models")


class InferenceRequest(BaseModel):
    """Request payload for simple anomaly scoring."""

    features: list[float] = Field(default_factory=list)


class GenerateRequest(BaseModel):
    """Request payload for Llama-backed text generation."""

    prompt: str = Field(min_length=1)
    system_prompt: str | None = None
    model: str | None = None
    backend: str = Field(default="auto")
    adapter_path: str | None = None
    merge_lora: bool = False
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=512, ge=1, le=4096)


class AlertClassificationRequest(BaseModel):
    """Structured payload for alert classification."""

    message: str = Field(min_length=1)
    source: str | None = None
    tags: list[str] = Field(default_factory=list)
    anomaly_score: float | None = Field(default=None, ge=0.0, le=1.0)


class EventSummaryRequest(BaseModel):
    """Structured payload for command-center event summarization."""

    title: str | None = None
    classification: str | None = None
    severity: str | None = None
    location: str | None = None
    alerts: list[str] = Field(default_factory=list)
    sensor_readings: dict[str, float] = Field(default_factory=dict)
    max_sentences: int = Field(default=2, ge=1, le=4)


class ObjectDetectionRequest(BaseModel):
    """Image payload for SmartCito object detection."""

    image_b64: str = Field(min_length=1)
    backend: str = Field(default="auto")
    labels: list[str] = Field(default_factory=lambda: ["motion-object"])
    threshold: float = Field(default=0.6, ge=0.0, le=1.0)


@app.get("/health")
async def health() -> dict[str, str]:
    settings = load_llama_stack_settings()
    return {
        "status": "ok",
        "service": "ai-models",
        "llama_stack": "configured" if settings.configured else "not-configured",
    }


@app.get("/models")
async def models() -> dict[str, object]:
    return await list_models()


@app.post("/infer")
async def infer(request: InferenceRequest) -> dict[str, float]:
    return {"score": score_anomaly(request.features)}


@app.post("/generate")
async def generate(request: GenerateRequest) -> dict[str, object]:
    try:
        return await generate_text(
            request.prompt,
            system_prompt=request.system_prompt,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            backend=request.backend,
            adapter_path=request.adapter_path,
            merge_lora=request.merge_lora,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Llama Stack request failed: {exc}") from exc


@app.post("/classify_alert")
async def classify_alert_endpoint(request: AlertClassificationRequest) -> dict[str, object]:
    classification = classify_alert(
        request.message,
        source=request.source,
        tags=request.tags,
        anomaly_score=request.anomaly_score,
    )
    return {
        "category": classification.category,
        "severity": classification.severity,
        "confidence": classification.confidence,
        "recommended_action": classification.recommended_action,
        "requires_human_review": classification.requires_human_review,
    }


@app.post("/summarize_event")
async def summarize_event_endpoint(request: EventSummaryRequest) -> dict[str, str]:
    return {
        "summary": summarize_event(
            title=request.title,
            classification=request.classification,
            severity=request.severity,
            location=request.location,
            alerts=request.alerts,
            sensor_readings=request.sensor_readings,
            max_sentences=request.max_sentences,
        )
    }


@app.post("/detect_objects")
async def detect_objects_endpoint(request: ObjectDetectionRequest) -> dict[str, object]:
    try:
        detections, metadata = detect_objects(
            request.image_b64,
            backend=request.backend,
            labels=request.labels,
            threshold=request.threshold,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {
        "backend": metadata["backend"],
        "requested_backend": metadata["requested_backend"],
        "image_width": metadata["image_width"],
        "image_height": metadata["image_height"],
        "detections": [
            {
                "label": detection.label,
                "confidence": detection.confidence,
                "bbox": list(detection.bbox),
                "area_ratio": detection.area_ratio,
            }
            for detection in detections
        ],
    }
