"""
================================================================================
 File: app/services/object_storage.py
 Purpose:
   Minimal object storage abstraction for large blobs referenced by processed
   events. Uses a filesystem-backed file:// endpoint for local development.
================================================================================
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from app.core.config import get_settings


class ObjectStorageService:
    def __init__(self) -> None:
        settings = get_settings()
        endpoint = settings.object_storage_endpoint.removeprefix("file://")
        self._root = Path(endpoint).expanduser().resolve() / settings.object_storage_bucket
        self._root.mkdir(parents=True, exist_ok=True)

    async def store_blob(self, *, data: bytes, suffix: str = ".bin") -> str:
        blob_path = self._root / f"{uuid4()}{suffix}"
        blob_path.write_bytes(data)
        return blob_path.as_uri()


object_storage_service = ObjectStorageService()
