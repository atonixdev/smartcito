"""
================================================================================
 File: orcaapi/app/services/frame_parser.py
 Purpose:
   Pure-Python implementation of the Orca binary sensor frame parser.
   This is the reference implementation; the C extension in `native/`
   produces identical output and is selected automatically when available.

 Wire format: see `native/orca_fast.c` for the layout diagram.
================================================================================
"""

from __future__ import annotations

import struct
from typing import TypedDict

FRAME_SIZE = 17
FRAME_VERSION = 0x01

# < = little-endian; B=u8, H=u16, Q=u64, f=f32, x=pad
_STRUCT = struct.Struct("<BBHQf")  # 1+1+2+8+4 = 16 bytes (checksum read separately)


class ParsedFrame(TypedDict):
    version: int
    kind: int
    sensor_id: int
    timestamp_ms: int
    value: float


def _xor_checksum(buf: bytes) -> int:
    c = 0
    for b in buf:
        c ^= b
    return c


def _parse_frame_python(buf: bytes) -> ParsedFrame:
    """Parse a 17-byte Orca sensor frame.

    Raises:
        ValueError: on wrong length, unsupported version, or bad checksum.
    """
    if len(buf) != FRAME_SIZE:
        raise ValueError(f"expected {FRAME_SIZE} bytes, got {len(buf)}")

    if _xor_checksum(buf[:-1]) != buf[-1]:
        raise ValueError("frame checksum mismatch")

    version, kind, sensor_id, timestamp_ms, value = _STRUCT.unpack(buf[:16])
    if version != FRAME_VERSION:
        raise ValueError(f"unsupported frame version: {version}")

    return ParsedFrame(
        version=version,
        kind=kind,
        sensor_id=sensor_id,
        timestamp_ms=timestamp_ms,
        value=float(value),
    )


parse_frame = _parse_frame_python


# Prefer the C accelerator when it's been compiled and installed.
try:  # pragma: no cover - import side-effect
    from orca_fast import parse_frame as _fast_parse_frame  # type: ignore[import-not-found]

    parse_frame = _fast_parse_frame  # type: ignore[assignment]
except ImportError:
    pass
