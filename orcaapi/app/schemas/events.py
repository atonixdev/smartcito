"""
================================================================================
 File: app/schemas/events.py
 Purpose:
   API schemas for normalized events, alerts, and historical analytics.
================================================================================
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class NormalizedEvent(BaseModel):
    event_id: str
    source: str
    entity_id: str
    event_type: str
    occurred_at: datetime
    received_at: datetime
    payload: dict[str, object] = Field(default_factory=dict)
    metadata: dict[str, object] = Field(default_factory=dict)


class AlertEvent(BaseModel):
    id: str
    severity: str
    title: str
    message: str
    created_at: datetime
    payload: dict[str, object] = Field(default_factory=dict)


class HistoricalAnalyticsPoint(BaseModel):
    sensor_id: str
    samples: int
    average_value: float
    latest_observed_at: datetime
