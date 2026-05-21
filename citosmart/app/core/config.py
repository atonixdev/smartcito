"""
================================================================================
 File: backend/app/core/config.py
 Purpose:
   Centralized, type-safe configuration loaded from environment variables
   (and an optional .env file) via pydantic-settings.

 Why a single Settings class?
   - One source of truth for env vars; no scattered os.getenv() calls.
   - Validated at import time → fast failure on misconfiguration.
   - Easy to override in tests via dependency injection.

 Usage:
     from app.core.config import get_settings
     settings = get_settings()
     print(settings.database_url)
================================================================================
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ----- Core -----
    app_env: Literal["development", "staging", "production"] = "development"
    app_name: str = "SmartCito"
    app_host: str = "0.0.0.0"  # noqa: S104  binding intentional for container
    app_port: int = 8000
    log_level: str = "INFO"

    # ----- Security -----
    secret_key: str = Field(
        default="dev-only-change-me",
        description="HMAC key for JWT signing. MUST be overridden in production.",
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expires_minutes: int = 60
    cors_allowed_origins: str = "http://localhost:5173"

    # ----- Database -----
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "smartcito"
    postgres_user: str = "smartcito"
    postgres_password: str = "smartcito"

    # ----- Cache -----
    redis_url: str = "redis://redis:6379/0"

    # ----- Streaming (Kafka) -----
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_sensor_topic: str = "smartcito.sensors.raw"
    kafka_publisher_enabled: bool = False

    # ----- IoT ingestion (MQTT) -----
    mqtt_enabled: bool = False
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_topic: str = "smartcito/sensors/+"
    mqtt_client_id: str = "smartcito-api"

    # ----- Observability -----
    audit_log_enabled: bool = True
    otel_exporter_otlp_endpoint: str | None = None

    # ---------- Computed / convenience helpers ----------

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        """Async SQLAlchemy DSN for PostgreSQL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_allowed_origins_list(self) -> list[str]:
        """Parse the comma-separated CORS_ALLOWED_ORIGINS env var."""
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Cached via lru_cache so it is constructed once per process. Tests can
    clear the cache (`get_settings.cache_clear()`) to inject overrides.
    """
    return Settings()
