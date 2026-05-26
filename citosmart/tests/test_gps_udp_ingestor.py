"""
================================================================================
 File: citosmart/tests/test_gps_udp_ingestor.py
 Purpose: Unit tests for UDP GPS ingestion payload handling.
================================================================================
"""

from __future__ import annotations

import pytest

from app.services.gps_udp_ingestor import GPSUDPIngestor


@pytest.mark.asyncio
async def test_udp_ingestor_persists_valid_payload() -> None:
    ingestor = GPSUDPIngestor()
    captured: list[dict[str, object]] = []

    async def fake_sink(point) -> None:  # type: ignore[no-untyped-def]
        captured.append(point.model_dump(mode="json"))

    ingestor._sink = fake_sink  # type: ignore[method-assign]

    payload = (
        b'{"device_id":"drone-udp-001","lat":-26.2041,"lon":28.0473,'
        b'"speed":8.2,"heading":91,"ts":"2026-05-26T15:30:12Z"}'
    )

    ok = await ingestor.handle_payload(payload, addr=("127.0.0.1", 55434))

    assert ok is True
    assert len(captured) == 1
    assert captured[0]["device_id"] == "drone-udp-001"
    assert captured[0]["lat"] == -26.2041


@pytest.mark.asyncio
async def test_udp_ingestor_rejects_invalid_payload() -> None:
    ingestor = GPSUDPIngestor()

    async def fake_sink(_point) -> None:  # type: ignore[no-untyped-def]
        raise AssertionError("sink should not be called for invalid payload")

    ingestor._sink = fake_sink  # type: ignore[method-assign]

    ok = await ingestor.handle_payload(
        b'{"device_id":"drone-udp-001","lat":-126.2041,"lon":28.0473,"ts":"2026-05-26T15:30:12Z"}'
    )

    assert ok is False