"""
================================================================================
 File: citosmart/app/schemas/api_response.py
 Purpose:
   Standard API response envelope with traceable request IDs.
================================================================================
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import Request
from pydantic import BaseModel, Field


class ApiMeta(BaseModel):
    version: str = "v1"
    source: str = "smartcito-backend"


class ApiEnvelope(BaseModel):
    status: str = Field(pattern="^(success|error)$")
    timestamp: str
    request_id: str
    data: Any
    meta: ApiMeta = Field(default_factory=ApiMeta)


def api_envelope(request: Request | None, data: Any, status: str = "success") -> dict[str, Any]:
    request_id = getattr(getattr(request, "state", None), "request_id", str(uuid4()))
    return ApiEnvelope(
        status=status,
        timestamp=datetime.now(UTC).isoformat(),
        request_id=request_id,
        data=data,
    ).model_dump()
