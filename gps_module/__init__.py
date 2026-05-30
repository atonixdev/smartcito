"""Compatibility shim for the migrated sensors.gps_module package."""

from __future__ import annotations

from pathlib import Path


_CURRENT_DIR = Path(__file__).resolve().parent
_MIGRATED_DIR = _CURRENT_DIR.parent / "sensors" / "gps_module"

__path__ = [str(_CURRENT_DIR), str(_MIGRATED_DIR)]
__all__ = []