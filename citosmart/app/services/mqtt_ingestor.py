"""
================================================================================
 File: backend/app/services/mqtt_ingestor.py
 Purpose:
   Bridge MQTT-published sensor messages into the SmartCito ingestion
   pipeline. Subscribes to a topic, parses each JSON payload into a
   `SensorReadingIn`, and forwards it to either:

     - the in-memory ingestion service (dev), or
     - the Kafka producer (production).

 Why MQTT?
   - De-facto standard for constrained IoT devices.
   - Tiny on-the-wire overhead; QoS levels for reliability.

 Running as a standalone worker:
     python -m app.services.mqtt_ingestor

 Concurrency model:
   - paho-mqtt's loop runs in its own thread; we hand events to asyncio via
     `asyncio.run_coroutine_threadsafe` so async sinks (Kafka, DB) work.
================================================================================
"""

from __future__ import annotations

import asyncio
import json
import logging
import signal
from typing import Any

import paho.mqtt.client as mqtt

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.schemas.sensor import SensorReadingIn
from app.services.ingestion import ingestion_service

logger = logging.getLogger(__name__)

# Override via env var MQTT_TOPIC if desired.
DEFAULT_TOPIC = "smartcito/sensors/+"   # `+` = single-level wildcard


class MqttIngestor:
    """Thin wrapper around paho-mqtt that ingests JSON sensor messages."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 1883,
        topic: str = DEFAULT_TOPIC,
        client_id: str = "smartcito-ingestor",
    ) -> None:
        self.host = host
        self.port = port
        self.topic = topic
        self._loop: asyncio.AbstractEventLoop | None = None
        self._client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
        )
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

    # ---- paho callbacks ----------------------------------------------------

    def _on_connect(
        self,
        client: mqtt.Client,
        _userdata: Any,
        _flags: dict[str, Any],
        reason_code: Any,
        _props: Any = None,
    ) -> None:
        if reason_code == 0:
            logger.info("MQTT connected; subscribing to %s", self.topic)
            client.subscribe(self.topic, qos=1)
        else:
            logger.error("MQTT connection failed: %s", reason_code)

    def _on_message(
        self,
        _client: mqtt.Client,
        _userdata: Any,
        msg: mqtt.MQTTMessage,
    ) -> None:
        """Parse and forward a single MQTT message."""
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            reading = SensorReadingIn.model_validate(payload)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Dropping invalid MQTT payload on %s: %s", msg.topic, exc)
            return

        if self._loop is None:
            # Fallback: synchronous in-memory ingest.
            ingestion_service.ingest(reading)
            return

        # Hand to asyncio sink (e.g. Kafka producer).
        asyncio.run_coroutine_threadsafe(self._sink(reading), self._loop)

    async def _sink(self, reading: SensorReadingIn) -> None:
        """Default async sink. Override in subclasses to publish to Kafka."""
        ingestion_service.ingest(reading)

    # ---- public API --------------------------------------------------------

    async def run(self) -> None:
        """Run the ingestor inside the current asyncio loop until cancelled."""
        self._loop = asyncio.get_running_loop()
        self._client.connect_async(self.host, self.port, keepalive=30)
        self._client.loop_start()
        try:
            await asyncio.Event().wait()  # block until cancelled
        finally:
            self._client.loop_stop()
            self._client.disconnect()
            logger.info("MQTT ingestor stopped")


# --------------------------------------------------------------------------- #
# Standalone entrypoint                                                       #
# --------------------------------------------------------------------------- #

async def _main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    ingestor = MqttIngestor()

    loop = asyncio.get_running_loop()
    stop = asyncio.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    task = asyncio.create_task(ingestor.run())
    await stop.wait()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    asyncio.run(_main())
