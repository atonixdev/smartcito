"""
================================================================================
 File: orcaapi/app/core/config.py
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

from pydantic import AliasChoices, Field, computed_field
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
    app_name: str = "Orca"
    app_host: str = "0.0.0.0"  # noqa: S104  # nosec B104
    app_port: int = 8000
    log_level: str = "INFO"

    # ----- Security -----
    secret_key: str = Field(
        default="dev-only-change-me",
        validation_alias=AliasChoices("AUTH_JWT_SECRET", "SECRET_KEY"),
        description="HMAC key for JWT signing. MUST be overridden in production.",
    )
    auth_issuer: str = Field(
        default="orca.local",
        validation_alias=AliasChoices("AUTH_ISSUER"),
    )
    auth_audience: str = Field(
        default="orca-clients",
        validation_alias=AliasChoices("AUTH_AUDIENCE"),
    )
    jwt_algorithm: str = "HS256"
    jwt_private_key_pem: str | None = Field(
        default=None, validation_alias=AliasChoices("JWT_PRIVATE_KEY_PEM")
    )
    jwt_public_key_pem: str | None = Field(
        default=None, validation_alias=AliasChoices("JWT_PUBLIC_KEY_PEM")
    )
    jwt_access_token_expires_minutes: int = 60
    cors_allowed_origins: str = "http://localhost:5173"

    # ----- Database -----
    postgres_host: str = Field(
        default="postgres",
        validation_alias=AliasChoices("DB_HOST", "POSTGRES_HOST"),
    )
    postgres_port: int = Field(
        default=5432,
        validation_alias=AliasChoices("DB_PORT", "POSTGRES_PORT"),
    )
    postgres_db: str = Field(
        default="orca",
        validation_alias=AliasChoices("DB_NAME", "POSTGRES_DB"),
    )
    postgres_user: str = Field(
        default="orca",
        validation_alias=AliasChoices("DB_USER", "POSTGRES_USER"),
    )
    postgres_password: str = Field(
        default="orca",
        validation_alias=AliasChoices("DB_PASSWORD", "POSTGRES_PASSWORD"),
    )
    postgres_primary_host: str = Field(
        default="postgres-primary.database.svc.cluster.local",
        validation_alias=AliasChoices("POSTGRES_PRIMARY_HOST"),
    )
    postgres_replica_host: str = Field(
        default="postgres-replica.database.svc.cluster.local",
        validation_alias=AliasChoices("POSTGRES_REPLICA_HOST"),
    )

    # ----- Data lake / big-data storage -----
    hdfs_enabled: bool = False
    hdfs_namenode_rpc_address: str = ""
    hdfs_namenode_http_address: str = ""
    hdfs_raw_data_path: str = "/orca/raw"
    hdfs_archive_path: str = "/orca/archive"
    hdfs_ai_training_path: str = "/orca/ai/training"
    hbase_enabled: bool = False
    hbase_zookeeper_quorum: str = ""
    hbase_zookeeper_client_port: int = 2181
    hbase_master_address: str = ""
    hbase_thrift_address: str = ""
    hbase_sensor_table: str = "orca_sensor_events"
    hbase_column_family: str = "d"

    # ----- Cache -----
    redis_url: str = "redis://redis:6379/0"
    memcached_servers: str = "memcached-1:11211,memcached-2:11211,memcached-3:11211"
    memcached_default_ttl_seconds: int = 60
    memcached_api_ttl_seconds: int = 60
    memcached_dashboard_ttl_seconds: int = 45
    memcached_device_metadata_ttl_seconds: int = 300
    memcached_ai_ttl_seconds: int = 1800
    memcached_session_ttl_seconds: int = 3600

    # ----- Streaming (Kafka) -----
    kafka_bootstrap_servers: str = Field(
        default="kafka:9092",
        validation_alias=AliasChoices(
            "KAFKA_BROKER_URL",
            "MESSAGE_BUS_URL",
            "KAFKA_BOOTSTRAP_SERVERS",
        ),
    )
    kafka_sensor_topic: str = "orca.sensors.raw"
    kafka_raw_events_topic: str = "orca.events.raw"
    kafka_clean_events_topic: str = "orca.events.clean"
    kafka_alerts_topic: str = "orca.alerts"
    kafka_publisher_enabled: bool = False

    # ----- IoT ingestion (MQTT) -----
    mqtt_enabled: bool = False
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_topic: str = "orca/sensors/+"
    mqtt_client_id: str = "orca-api"
    gps_mqtt_enabled: bool = False
    gps_mqtt_topic: str = "orca/gps/+"
    gps_mqtt_client_id: str = "orca-gps-api"
    gps_udp_enabled: bool = False
    gps_udp_host: str = "0.0.0.0"  # nosec B104
    gps_udp_port: int = 9011

    # ----- Observability -----
    audit_log_enabled: bool = True
    otel_exporter_otlp_endpoint: str | None = None

    # ----- AI / object storage -----
    ai_models_url: str = "http://ai-service:8012"
    object_storage_endpoint: str = "file://./data/object_storage"
    object_storage_bucket: str = "orca-artifacts"

    # ----- Realtime / service aggregation -----
    drone_gateway_url: str = "http://drone-gateway:8020"
    mission_control_url: str = "http://mission-control:8025"
    drone_camera_url: str = "http://drone-camera-ingestion:8022"
    threat_detection_url: str = "http://threat-detection:8023"
    mapping_geospatial_url: str = "http://mapping-geospatial:8024"
    realtime_snapshot_interval_seconds: float = 2.0

    # ----- Infra / deploy -----
    openstack_auth_url: str | None = Field(
        default=None, validation_alias=AliasChoices("OPENSTACK_AUTH_URL")
    )
    openstack_project: str | None = Field(
        default=None, validation_alias=AliasChoices("OPENSTACK_PROJECT")
    )
    openstack_user: str | None = Field(
        default=None, validation_alias=AliasChoices("OPENSTACK_USER")
    )
    openstack_password: str | None = Field(
        default=None, validation_alias=AliasChoices("OPENSTACK_PASSWORD")
    )
    openstack_region: str | None = Field(
        default=None, validation_alias=AliasChoices("OPENSTACK_REGION")
    )

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
