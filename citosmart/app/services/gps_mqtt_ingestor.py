"""
================================================================================
 File: citosmart/app/services/gps_mqtt_ingestor.py
 Purpose:
   Bridge MQTT-published GPS messages into the DB-backed GPS tracking service.
================================================================================
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import paho.mqtt.client as mqtt

from app.db.session import AsyncSessionLocal
from app.schemas.gps import GPSPointIn
from app.services.gps_tracking import gps_tracking_service

logger = logging.getLogger(__name__)

DEFAULT_TOPIC = "orca/gps/+"


class GPSMqttIngestor:
    """Thin wrapper around paho-mqtt for GPS payload ingestion."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 1883,
        topic: str = DEFAULT_TOPIC,
        client_id: str = "orca-gps-ingestor",
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

    def _on_connect(
        self,
        client: mqtt.Client,
        _userdata: Any,
        _flags: dict[str, Any],
        reason_code: Any,
        _props: Any = None,
    ) -> None:
        if reason_code == 0:
            logger.info("GPS MQTT connected; subscribing to %s", self.topic)
            client.subscribe(self.topic, qos=1)
        else:
            logger.error("GPS MQTT connection failed: %s", reason_code)

    def _on_message(
        self,
        _client: mqtt.Client,
        _userdata: Any,
        msg: mqtt.MQTTMessage,
    ) -> None:
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            point = GPSPointIn.model_validate(payload)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Dropping invalid GPS MQTT payload on %s: %s", msg.topic, exc)
            return

        if self._loop is None:
            logger.warning("GPS MQTT loop not ready; dropping message for %s", point.device_id)
            return

        asyncio.run_coroutine_threadsafe(self._sink(point), self._loop)

    async def _sink(self, point: GPSPointIn) -> None:
        async with AsyncSessionLocal() as session:
            await gps_tracking_service.ingest(session, point)

    async def run(self) -> None:
        self._loop = asyncio.get_running_loop()
        self._client.connect_async(self.host, self.port, keepalive=30)
        self._client.loop_start()
        try:
            await asyncio.Event().wait()
        finally:
            self._client.loop_stop()
            self._client.disconnect()
            logger.info("GPS MQTT ingestor stopped")