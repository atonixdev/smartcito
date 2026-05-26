from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ai.training.prepare_dataset import RAW_LOG_BUILDERS


DEFAULT_CONFIG = Path("ingestion/config/datastream_sources.json")
DEFAULT_OUTPUT_DIR = Path("ai/smartcito_datasets")


@dataclass(slots=True)
class DataSourceConfig:
    name: str
    backend: str
    source_type: str
    connection: str
    table_or_collection: str
    id_field: str = "id"
    processed_field: str = "processed"
    batch_size: int = 100


class BaseDataSourceClient:
    def fetch_unprocessed(self, config: DataSourceConfig, *, limit: int | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError

    def mark_processed(self, config: DataSourceConfig, record_ids: list[str]) -> int:
        raise NotImplementedError


class SQLiteDataSourceClient(BaseDataSourceClient):
    def __init__(self, database_path: str) -> None:
        self.database_path = database_path

    def fetch_unprocessed(self, config: DataSourceConfig, *, limit: int | None = None) -> list[dict[str, Any]]:
        batch_size = limit or config.batch_size
        query = (
            f"SELECT * FROM {config.table_or_collection} "
            f"WHERE COALESCE({config.processed_field}, 0) = 0 ORDER BY {config.id_field} LIMIT ?"
        )
        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(query, (batch_size,)).fetchall()
        return [dict(row) for row in rows]

    def mark_processed(self, config: DataSourceConfig, record_ids: list[str]) -> int:
        if not record_ids:
            return 0
        placeholders = ", ".join("?" for _ in record_ids)
        query = (
            f"UPDATE {config.table_or_collection} SET {config.processed_field} = 1 "
            f"WHERE {config.id_field} IN ({placeholders})"
        )
        with sqlite3.connect(self.database_path) as connection:
            cursor = connection.execute(query, tuple(record_ids))
            connection.commit()
            return int(cursor.rowcount)


class PostgresDataSourceClient(BaseDataSourceClient):
    def __init__(self, dsn: str) -> None:
        try:
            import psycopg
        except ModuleNotFoundError as exc:
            raise RuntimeError("Postgres ingestion requires the psycopg package.") from exc
        self._psycopg = psycopg
        self.dsn = dsn

    def fetch_unprocessed(self, config: DataSourceConfig, *, limit: int | None = None) -> list[dict[str, Any]]:
        batch_size = limit or config.batch_size
        query = (
            f"SELECT * FROM {config.table_or_collection} "
            f"WHERE COALESCE({config.processed_field}, FALSE) = FALSE ORDER BY {config.id_field} LIMIT %s"
        )
        with self._psycopg.connect(self.dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (batch_size,))
                column_names = [description.name for description in cursor.description]
                return [dict(zip(column_names, row, strict=False)) for row in cursor.fetchall()]

    def mark_processed(self, config: DataSourceConfig, record_ids: list[str]) -> int:
        if not record_ids:
            return 0
        query = (
            f"UPDATE {config.table_or_collection} SET {config.processed_field} = TRUE "
            f"WHERE {config.id_field} = ANY(%s)"
        )
        with self._psycopg.connect(self.dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (record_ids,))
                updated = int(cursor.rowcount)
            connection.commit()
        return updated


class MongoDataSourceClient(BaseDataSourceClient):
    def __init__(self, uri: str) -> None:
        try:
            from pymongo import MongoClient
        except ModuleNotFoundError as exc:
            raise RuntimeError("Mongo ingestion requires the pymongo package.") from exc
        self._client = MongoClient(uri)

    def _split_namespace(self, table_or_collection: str) -> tuple[str, str]:
        database, _, collection = table_or_collection.partition(".")
        if not database or not collection:
            raise ValueError("Mongo table_or_collection must be in the form database.collection")
        return database, collection

    def fetch_unprocessed(self, config: DataSourceConfig, *, limit: int | None = None) -> list[dict[str, Any]]:
        database, collection = self._split_namespace(config.table_or_collection)
        batch_size = limit or config.batch_size
        cursor = (
            self._client[database][collection]
            .find({config.processed_field: {"$ne": True}})
            .sort(config.id_field, 1)
            .limit(batch_size)
        )
        return [dict(item) for item in cursor]

    def mark_processed(self, config: DataSourceConfig, record_ids: list[str]) -> int:
        if not record_ids:
            return 0
        database, collection = self._split_namespace(config.table_or_collection)
        result = self._client[database][collection].update_many(
            {config.id_field: {"$in": record_ids}},
            {"$set": {config.processed_field: True}},
        )
        return int(result.modified_count)


def _load_configs(config_path: str | Path = DEFAULT_CONFIG) -> list[DataSourceConfig]:
    path = Path(config_path)
    payload = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"sources": []}
    sources = payload.get("sources", [])
    if not isinstance(sources, list):
        raise ValueError("ingestion config must contain a 'sources' list")
    return [DataSourceConfig(**dict(item)) for item in sources]


def _client_for_backend(config: DataSourceConfig) -> BaseDataSourceClient:
    backend = config.backend.strip().lower()
    if backend == "sqlite":
        return SQLiteDataSourceClient(config.connection)
    if backend == "postgres":
        return PostgresDataSourceClient(config.connection)
    if backend == "mongodb":
        return MongoDataSourceClient(config.connection)
    raise ValueError(f"Unsupported ingestion backend: {config.backend}")


def _to_training_record(source_name: str, source_type: str, event: dict[str, Any], index: int) -> dict[str, Any]:
    builder = RAW_LOG_BUILDERS[source_type]
    payload = dict(event)
    raw_metadata = payload.get("metadata")
    if isinstance(raw_metadata, str):
        try:
            parsed_metadata = json.loads(raw_metadata)
        except json.JSONDecodeError:
            parsed_metadata = {"raw_metadata": raw_metadata}
    else:
        parsed_metadata = raw_metadata
    metadata = dict(parsed_metadata or {})
    metadata.setdefault("source", source_name)
    metadata.setdefault("ingested_at", datetime.now(UTC).isoformat())
    payload["metadata"] = metadata
    record = builder(payload, index)
    return {
        "instruction": record.instruction,
        "input": record.input,
        "output": record.output,
        "metadata": record.metadata,
    }


def write_training_batch(records: list[dict[str, Any]], *, output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> Path | None:
    if not records:
        return None
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    batch_name = datetime.now(UTC).strftime("batch_%Y%m%d_%H%M%S.json")
    destination = directory / batch_name
    destination.write_text(json.dumps(records, indent=2), encoding="utf-8")
    return destination


def run_datastream(
    *,
    config_path: str | Path = DEFAULT_CONFIG,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    limit: int | None = None,
) -> dict[str, Any]:
    configs = _load_configs(config_path)
    written_records: list[dict[str, Any]] = []
    source_summaries: list[dict[str, Any]] = []

    for config in configs:
        client = _client_for_backend(config)
        events = client.fetch_unprocessed(config, limit=limit)
        records = [
            _to_training_record(config.name, config.source_type, event, index)
            for index, event in enumerate(events, start=1)
        ]
        record_ids = [str(event[config.id_field]) for event in events if config.id_field in event]
        updated = client.mark_processed(config, record_ids)
        written_records.extend(records)
        source_summaries.append(
            {
                "source": config.name,
                "backend": config.backend,
                "events_fetched": len(events),
                "records_written": len(records),
                "events_marked_processed": updated,
            }
        )

    batch_path = write_training_batch(written_records, output_dir=output_dir)
    return {
        "batch_path": str(batch_path) if batch_path else None,
        "records_written": len(written_records),
        "sources": source_summaries,
    }
