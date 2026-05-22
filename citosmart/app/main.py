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
import os
from contextlib import asynccontextmanager
from time import monotonic
from typing import AsyncIterator
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
from starlette.responses import JSONResponse, HTMLResponse

from app.api.v1.endpoints.platform import router as platform_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.services.ingestion import ingestion_service
from app.services.kafka_stream import KafkaPublisher
from app.services.mqtt_ingestor import MqttIngestor
from app.schemas.sensor import SensorReadingIn
from app.schemas.api_response import api_envelope

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

    rate_buckets: dict[str, list[float]] = {}

    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        request.state.request_id = request.headers.get("x-request-id", str(uuid4()))

        allowed_ips = {ip.strip() for ip in os.getenv("SMARTCITO_ALLOWED_IPS", "").split(",") if ip.strip()}
        client_ip = request.client.host if request.client else "unknown"
        if allowed_ips and client_ip not in allowed_ips:
            return JSONResponse(
                api_envelope(request, {"error": "IP not allowed"}, status="error"),
                status_code=403,
            )

        window_seconds = int(os.getenv("SMARTCITO_RATE_WINDOW_SECONDS", "60"))
        max_requests = int(os.getenv("SMARTCITO_RATE_LIMIT", "240"))
        now = monotonic()
        bucket = [stamp for stamp in rate_buckets.get(client_ip, []) if now - stamp < window_seconds]
        if len(bucket) >= max_requests:
            return JSONResponse(
                api_envelope(request, {"error": "Rate limit exceeded"}, status="error"),
                status_code=429,
            )
        bucket.append(now)
        rate_buckets[client_ip] = bucket

        response = await call_next(request)
        response.headers["x-request-id"] = request.state.request_id
        return response

    # Versioned API router.
    app.include_router(api_router, prefix="/api/v1")
    app.include_router(platform_router, prefix="/api/v1")

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def backend_landing() -> str:
        return f"""
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <title>{settings.app_name} · Backend</title>
            <style>
              :root {{
                --bg: #0a0f1f;
                --panel: #111827;
                --panel-2: #0f243a;
                --text: #ffffff;
                --muted: #aab2c5;
                --blue: #3fa9f5;
                --green: #67d5a5;
                --border: rgba(255,255,255,0.08);
                font-family: "IBM Plex Sans", Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
              }}
              * {{ box-sizing: border-box; }}
              body {{
                margin: 0;
                min-height: 100vh;
                color: var(--text);
                background:
                  radial-gradient(circle at top right, rgba(63,169,245,0.18), transparent 34%),
                  linear-gradient(135deg, #0a0f1f, #08141f 55%, #06111b);
              }}
              main {{
                width: min(1120px, calc(100% - 48px));
                margin: 0 auto;
                padding: 64px 0;
              }}
              .hero {{
                display: grid;
                gap: 24px;
                padding: 40px;
                border: 1px solid var(--border);
                border-radius: 16px;
                background: rgba(17,24,39,0.76);
                backdrop-filter: blur(12px);
              }}
              .brand {{
                display: inline-flex;
                align-items: center;
                gap: 16px;
                color: var(--text);
                font-weight: 700;
                letter-spacing: 1.5px;
              }}
              .logo {{
                width: 40px;
                height: 40px;
              }}
              h1 {{
                margin: 0;
                max-width: 760px;
                font-size: clamp(32px, 5vw, 56px);
                line-height: 1;
              }}
              p {{
                margin: 0;
                max-width: 760px;
                color: var(--muted);
                font-size: 16px;
              }}
              .status {{
                display: flex;
                flex-wrap: wrap;
                gap: 12px;
              }}
              .pill {{
                border: 1px solid rgba(103,213,165,0.32);
                border-radius: 999px;
                color: var(--green);
                padding: 8px 12px;
                font-size: 14px;
                font-weight: 600;
              }}
              .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 24px;
                margin-top: 24px;
              }}
              a.card {{
                display: grid;
                gap: 8px;
                min-height: 132px;
                padding: 24px;
                border: 1px solid var(--border);
                border-radius: 12px;
                background: var(--panel);
                color: var(--text);
                text-decoration: none;
                transition: transform 160ms ease, border-color 160ms ease, background 160ms ease;
              }}
              a.card:hover {{
                transform: translateY(-2px);
                border-color: rgba(63,169,245,0.5);
                background: var(--panel-2);
              }}
              .card strong {{
                font-size: 18px;
              }}
              .card span {{
                color: var(--muted);
                font-size: 14px;
              }}
              footer {{
                margin-top: 32px;
                color: var(--muted);
                font-size: 14px;
              }}
            </style>
          </head>
          <body>
            <main>
              <section class="hero">
                <div class="brand">
                  <svg class="logo" viewBox="0 0 32 32" aria-hidden="true">
                    <rect x="2.5" y="2.5" width="27" height="27" rx="6" fill="#0A0F1F" stroke="#fff" stroke-width="3"/>
                    <path d="M11 6v20M21 6v20M6 11h20M6 21h20" stroke="#AAB2C5" stroke-width="2" stroke-linecap="round"/>
                    <path d="M16 6v6M16 20v6M6 16h6M20 16h6" stroke="#3FA9F5" stroke-width="2" stroke-linecap="round"/>
                    <circle cx="16" cy="16" r="4" fill="#3FA9F5"/>
                  </svg>
                  <span>Smart<span style="color: var(--blue)">Cito</span></span>
                </div>

                <h1>Urban Data Backbone API</h1>
                <p>
                  Versioned, secure, traceable backend gateway for devices, cameras,
                  GPS, events, maps, sensors, traffic, and SmartCito dashboard data.
                </p>

                <div class="status">
                  <span class="pill">API v1</span>
                  <span class="pill">JWT + RBAC</span>
                  <span class="pill">Request tracing</span>
                  <span class="pill">Dashboard-ready</span>
                </div>
              </section>

              <section class="grid" aria-label="Backend links">
                <a class="card" href="/docs">
                  <strong>Swagger UI</strong>
                  <span>Interactive OpenAPI documentation.</span>
                </a>
                <a class="card" href="/redoc">
                  <strong>ReDoc</strong>
                  <span>Readable API reference.</span>
                </a>
                <a class="card" href="/openapi.json">
                  <strong>OpenAPI JSON</strong>
                  <span>Machine-readable API contract.</span>
                </a>
                <a class="card" href="/api/v1/health/live">
                  <strong>Health Check</strong>
                  <span>Liveness probe for the backend.</span>
                </a>
                <a class="card" href="/api/v1/devices">
                  <strong>Devices</strong>
                  <span>Registered device resource API.</span>
                </a>
                <a class="card" href="/api/v1/events">
                  <strong>Events</strong>
                  <span>Operational logs and alert stream.</span>
                </a>
              </section>

              <footer>
                SmartCito backend running at <strong>http://localhost:8000</strong>
              </footer>
            </main>
          </body>
        </html>
        """

    # Prometheus metrics — scraped by the observability stack.
    app.mount("/metrics", make_asgi_app())

    return app


# Uvicorn / Gunicorn entry point.
app = create_app()
