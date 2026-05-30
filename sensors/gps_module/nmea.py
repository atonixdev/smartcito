"""
================================================================================
 File: gps_module/nmea.py
 Purpose:
   Lightweight NMEA parsing helpers for Orca GPS contributors.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class GpsFix:
    """Normalized GPS fix parsed from a GPGGA sentence."""

    latitude: float
    longitude: float
    satellites: int
    quality: int


def _parse_coordinate(raw: str, hemisphere: str) -> float:
    degrees_len = 2 if hemisphere in {"N", "S"} else 3
    degrees = float(raw[:degrees_len])
    minutes = float(raw[degrees_len:])
    value = degrees + minutes / 60
    if hemisphere in {"S", "W"}:
        value *= -1
    return value


def parse_gpgga(sentence: str) -> GpsFix:
    """Parse a basic GPGGA sentence into a normalized fix."""
    parts = sentence.strip().split(",")
    if len(parts) < 8 or not parts[0].endswith("GGA"):
        raise ValueError("Unsupported NMEA sentence")
    return GpsFix(
        latitude=_parse_coordinate(parts[2], parts[3]),
        longitude=_parse_coordinate(parts[4], parts[5]),
        quality=int(parts[6]),
        satellites=int(parts[7]),
    )
