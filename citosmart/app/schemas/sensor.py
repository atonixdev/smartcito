"""
================================================================================
 File: backend/app/schemas/sensor.py
 Purpose:
   Pydantic models that define the JSON contract for sensor data flowing
   between IoT producers, the SmartCito API, and dashboard consumers.

 Why separate schemas from ORM models?
   - Schemas describe the *wire* format and validation rules.
   - ORM models describe storage. Decoupling them lets us evolve either
     without breaking the other.
================================================================================
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


class SensorKind(str, Enum):
    """Supported sensor categories for the pilot phase."""

    TRAFFIC = "traffic"
    AIR_QUALITY = "air_quality"
    WATER = "water"
    ENERGY = "energy"
    CCTV = "cctv"
    OTHER = "other"


class SensorReadingIn(BaseModel):
    """Incoming reading from an IoT device or city system."""

    model_config = ConfigDict(extra="forbid")

    sensor_id: str = Field(..., min_length=1, max_length=128, examples=["traffic-001"])
    kind: SensorKind
    value: float = Field(..., description="Numeric measurement (units depend on kind)")
    unit: str = Field(..., max_length=32, examples=["vehicles/min", "µg/m³"])
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    observed_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    metadata: dict[str, str] = Field(default_factory=dict)


class SensorReadingOut(SensorReadingIn):
    """Reading as returned to API consumers, with a server-assigned id."""

    id: UUID = Field(default_factory=uuid4)
    received_at: datetime = Field(default_factory=lambda: datetime.utcnow())
