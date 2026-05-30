"""
================================================================================
 File: orcaapi/app/services/gps_udp_ingestor.py
 Purpose:
   UDP GPS ingestion that persists valid payloads into the shared
   gps_tracking_service storage path.
================================================================================
"""

from __future__ import annotations

import asyncio
import json
import logging

from app.db.session import AsyncSessionLocal
from app.schemas.gps import GPSPointIn
from app.services.gps_tracking import gps_tracking_service

logger = logging.getLogger(__name__)


class GPSUDPProtocol(asyncio.DatagramProtocol):
    """Asyncio protocol that forwards UDP payloads to GPSUDPIngestor."""

    def __init__(self, ingestor: "GPSUDPIngestor") -> None:
        self._ingestor = ingestor

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        asyncio.create_task(self._ingestor.handle_payload(data, addr=addr))


class GPSUDPIngestor:
    """Receive JSON GPS packets over UDP and store validated points."""

    def __init__(self, host: str = "0.0.0.0", port: int = 9011) -> None:  # noqa: S104  # nosec B104
        self.host = host
        self.port = port

    async def handle_payload(self, payload: bytes, *, addr: tuple[str, int] | None = None) -> bool:
        """Validate one UDP payload and persist it. Returns True on success."""
        try:
            data = json.loads(payload.decode("utf-8"))
            point = GPSPointIn.model_validate(data)
        except (json.JSONDecodeError, ValueError) as exc:
            source = f" from {addr[0]}:{addr[1]}" if addr is not None else ""
            logger.warning("Dropping invalid GPS UDP payload%s: %s", source, exc)
            return False

        await self._sink(point)
        return True

    async def _sink(self, point: GPSPointIn) -> None:
        async with AsyncSessionLocal() as session:
            await gps_tracking_service.ingest(session, point)

    async def run(self) -> None:
        """Bind a UDP socket and ingest packets until cancelled."""
        loop = asyncio.get_running_loop()
        transport, _ = await loop.create_datagram_endpoint(
            lambda: GPSUDPProtocol(self),
            local_addr=(self.host, self.port),
        )
        logger.info("GPS UDP ingestor listening on %s:%s", self.host, self.port)
        try:
            await asyncio.Event().wait()
        finally:
            transport.close()
            logger.info("GPS UDP ingestor stopped")
