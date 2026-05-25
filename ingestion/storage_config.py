from __future__ import annotations

import os
from typing import Any


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def _env_bool(name: str, default: bool = False) -> bool:
    raw = _env(name, "true" if default else "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def postgres_storage_target() -> dict[str, str]:
    primary_host = _env("POSTGRES_PRIMARY_HOST") or _env("DB_HOST", "postgres")
    replica_host = _env("POSTGRES_REPLICA_HOST") or primary_host
    return {
        "primary_host": primary_host,
        "replica_host": replica_host,
        "port": _env("DB_PORT", "5432"),
        "database": _env("DB_NAME", "smartcito"),
        "user": _env("DB_USER", "smartcito"),
    }


def hdfs_storage_target() -> dict[str, Any]:
    rpc_address = _env("HDFS_NAMENODE_RPC_ADDRESS")
    http_address = _env("HDFS_NAMENODE_HTTP_ADDRESS")
    enabled = _env_bool("HDFS_ENABLED", default=bool(rpc_address)) and bool(rpc_address)
    return {
        "enabled": enabled,
        "rpc_address": rpc_address,
        "http_address": http_address,
        "raw_path": _env("HDFS_RAW_DATA_PATH", "/smartcito/raw"),
        "archive_path": _env("HDFS_ARCHIVE_PATH", "/smartcito/archive"),
        "ai_training_path": _env("HDFS_AI_TRAINING_PATH", "/smartcito/ai/training"),
    }


def hbase_storage_target() -> dict[str, Any]:
    thrift_address = _env("HBASE_THRIFT_ADDRESS")
    quorum = _env("HBASE_ZOOKEEPER_QUORUM")
    enabled = _env_bool("HBASE_ENABLED", default=bool(thrift_address or quorum)) and bool(
        thrift_address or quorum
    )
    return {
        "enabled": enabled,
        "zookeeper_quorum": quorum,
        "zookeeper_client_port": _env("HBASE_ZOOKEEPER_CLIENT_PORT", "2181"),
        "master_address": _env("HBASE_MASTER_ADDRESS"),
        "thrift_address": thrift_address,
        "sensor_table": _env("HBASE_SENSOR_TABLE", "smartcito_sensor_events"),
        "column_family": _env("HBASE_COLUMN_FAMILY", "d"),
    }


def storage_runtime_summary() -> dict[str, Any]:
    return {
        "postgres": postgres_storage_target(),
        "hdfs": hdfs_storage_target(),
        "hbase": hbase_storage_target(),
    }