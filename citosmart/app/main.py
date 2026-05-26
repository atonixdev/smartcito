"""
================================================================================
 File: citosmart/app/main.py
 Purpose:
   ASGI entrypoint for the SmartCito Urban Data Backbone API.

   This module wires together:
     - Application configuration (env-driven, see app.core.config).
     - Structured logging.
     - CORS for the React webapp.
     - The versioned API router (/api/v1).
     - Liveness and readiness probes (/health/*).
     - Prometheus metrics endpoint (/metrics).

 Run locally:
     uvicorn app.main:app --reload

 Design notes:
   - All cross-cutting middleware lives here so it is easy to audit.
   - Business logic NEVER lives in this file. Endpoints go in
     `app.api.v1.endpoints.*`, and reusable logic in `app.services.*`.
================================================================================
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.graphql.schema import graphql_router
from app.services.gps_mqtt_ingestor import GPSMqttIngestor
from app.services.gps_udp_ingestor import GPSUDPIngestor
from app.services.ingestion import ingestion_service
from app.services.kafka_stream import KafkaPublisher
from app.services.mqtt_ingestor import MqttIngestor
from app.schemas.sensor import SensorReadingIn

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup / shutdown hook.

    Wires optional background services based on env flags:
      - KAFKA_PUBLISHER_ENABLED → boots an aiokafka producer and stores it
        on `app.state.kafka` for endpoints to use.
      - MQTT_ENABLED            → boots a paho-mqtt bridge that forwards
        incoming messages into the ingestion service (and Kafka if enabled).

    Both services are best-effort: a failure to connect is logged but does
    not crash the API. This keeps the dev experience friendly.
    """
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("Starting %s in %s mode", settings.app_name, settings.app_env)

    app.state.kafka = None
    app.state.mqtt_task = None
    app.state.gps_mqtt_task = None
    app.state.gps_udp_task = None

    # ---- Kafka publisher ---------------------------------------------------
    if settings.kafka_publisher_enabled:
        publisher = KafkaPublisher()
        try:
            await publisher.start()
            app.state.kafka = publisher
        except Exception as exc:  # noqa: BLE001 — best-effort startup
            logger.warning("Kafka publisher disabled (start failed): %s", exc)

    # ---- MQTT bridge -------------------------------------------------------
    if settings.mqtt_enabled:
        kafka_ref = app.state.kafka

        class _BridgingIngestor(MqttIngestor):
            """MQTT ingestor that ALSO publishes to Kafka when enabled."""

            async def _sink(self, reading: SensorReadingIn) -> None:
                ingestion_service.ingest(reading)
                if kafka_ref is not None:
                    try:
                        await kafka_ref.publish_reading(reading)
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Kafka publish failed: %s", exc)

        ingestor = _BridgingIngestor(
            host=settings.mqtt_host,
            port=settings.mqtt_port,
            topic=settings.mqtt_topic,
            client_id=settings.mqtt_client_id,
        )
        app.state.mqtt_task = asyncio.create_task(ingestor.run(), name="mqtt-ingestor")
        logger.info("MQTT bridge started → %s:%s [%s]",
                    settings.mqtt_host, settings.mqtt_port, settings.mqtt_topic)

    # ---- GPS MQTT bridge ---------------------------------------------------
    if settings.gps_mqtt_enabled:
        gps_ingestor = GPSMqttIngestor(
            host=settings.mqtt_host,
            port=settings.mqtt_port,
            topic=settings.gps_mqtt_topic,
            client_id=settings.gps_mqtt_client_id,
        )
        app.state.gps_mqtt_task = asyncio.create_task(gps_ingestor.run(), name="gps-mqtt-ingestor")
        logger.info(
            "GPS MQTT bridge started → %s:%s [%s]",
            settings.mqtt_host,
            settings.mqtt_port,
            settings.gps_mqtt_topic,
        )

    # ---- GPS UDP bridge ----------------------------------------------------
    if settings.gps_udp_enabled:
        gps_udp_ingestor = GPSUDPIngestor(
            host=settings.gps_udp_host,
            port=settings.gps_udp_port,
        )
        app.state.gps_udp_task = asyncio.create_task(gps_udp_ingestor.run(), name="gps-udp-ingestor")
        logger.info(
            "GPS UDP ingestor started → %s:%s",
            settings.gps_udp_host,
            settings.gps_udp_port,
        )

    try:
        yield
    finally:
        logger.info("Shutting down %s", settings.app_name)

        if app.state.mqtt_task is not None:
            app.state.mqtt_task.cancel()
            try:
                await app.state.mqtt_task
            except (asyncio.CancelledError, Exception):  # noqa: BLE001
                pass

        if app.state.gps_mqtt_task is not None:
            app.state.gps_mqtt_task.cancel()
            try:
                await app.state.gps_mqtt_task
            except (asyncio.CancelledError, Exception):  # noqa: BLE001
                pass

        if app.state.gps_udp_task is not None:
            app.state.gps_udp_task.cancel()
            try:
                await app.state.gps_udp_task
            except (asyncio.CancelledError, Exception):  # noqa: BLE001
                pass

        if app.state.kafka is not None:
            try:
                await app.state.kafka.stop()
            except Exception as exc:  # noqa: BLE001
                logger.warning("Kafka shutdown error: %s", exc)


def create_app() -> FastAPI:
    """Application factory.

    A factory (instead of a module-level singleton) makes the app trivially
    testable: tests can construct independent app instances with overridden
    settings or dependencies.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description=(
            "SmartCito — Urban Data Backbone. A secure, open API gateway for "
            "smart-city IoT, traffic, utilities, and citizen services."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS — restrict to known webapps in production.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Versioned API router.
    app.include_router(api_router, prefix="/api/v1")
    app.include_router(graphql_router, prefix="/api/v1/graphql")

    # Prometheus metrics — scraped by the observability stack.
    app.mount("/metrics", make_asgi_app())

    return app


# Uvicorn / Gunicorn entry point.
app = create_app()
