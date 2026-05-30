"""Compatibility shim for the migrated edge.hardware package."""

from __future__ import annotations

from pathlib import Path


_CURRENT_DIR = Path(__file__).resolve().parent
_MIGRATED_DIR = _CURRENT_DIR.parent / "edge" / "hardware"

__path__ = [str(_CURRENT_DIR), str(_MIGRATED_DIR)]
__all__ = []