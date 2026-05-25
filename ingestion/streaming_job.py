"""Repo-owned Spark Structured Streaming job for SmartCito."""

from __future__ import annotations

import json
import logging
import os

from ingestion.storage_config import hbase_storage_target, hdfs_storage_target, postgres_storage_target


logger = logging.getLogger(__name__)


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


def _memcached_client():
    try:
        from pymemcache.client.hash import HashClient
    except ModuleNotFoundError:
        return None

    endpoints = []
    for endpoint in _env("MEMCACHED_SERVERS", "").split(","):
        host, _, port = endpoint.strip().partition(":")
        if host and port:
            endpoints.append((host, int(port)))

    if not endpoints:
        return None

    return HashClient(endpoints, connect_timeout=1.0, timeout=1.0, no_delay=True)


def _cache_batch_metadata(batch_df, batch_id: int) -> None:
    client = _memcached_client()
    if client is None:
        return

    metadata_ttl = int(_env("MEMCACHED_DEVICE_METADATA_TTL_SECONDS", "300"))
    api_ttl = int(_env("MEMCACHED_API_TTL_SECONDS", "60"))
    record_count = batch_df.count()
    identifiers = [
        row.entity_id
        for row in batch_df.select("entity_id").dropna().distinct().limit(200).collect()
        if row.entity_id
    ]

    client.set(
        f"data-platform:stream-batch:batch-{batch_id}",
        json.dumps({"batch_id": batch_id, "record_count": record_count}).encode("utf-8"),
        expire=api_ttl,
    )

    for identifier in identifiers:
        client.set(
            f"device:metadata:{identifier}",
            json.dumps(
                {
                    "device_id": identifier,
                    "source": "spark-streaming",
                    "last_processed_batch": batch_id,
                }
            ).encode("utf-8"),
            expire=metadata_ttl,
        )

    logger.info("cached batch=%s record_count=%s identifiers=%s", batch_id, record_count, len(identifiers))


def _write_to_postgres(batch_df, batch_id: int) -> None:
    postgres = postgres_storage_target()
    db_host = postgres["primary_host"]
    db_port = postgres["port"]
    db_name = postgres["database"]
    db_user = postgres["user"]
    db_password = _env("DB_PASSWORD", "change-me")

    (
        batch_df.write.mode("append")
        .format("jdbc")
        .option("url", f"jdbc:postgresql://{db_host}:{db_port}/{db_name}")
        .option("dbtable", "sensor_events")
        .option("user", db_user)
        .option("password", db_password)
        .save()
    )


def _write_to_hdfs(batch_df, batch_id: int) -> None:
    hdfs = hdfs_storage_target()
    if not hdfs["enabled"]:
        return

    raw_path = str(hdfs["raw_path"]).rstrip("/")
    target_path = f"hdfs://{hdfs['rpc_address']}{raw_path}"
    batch_df.write.mode("append").format("parquet").save(target_path)
    logger.info("persisted batch=%s to hdfs path=%s", batch_id, target_path)


def _write_to_hbase(batch_df, batch_id: int) -> None:
    hbase = hbase_storage_target()
    if not hbase["enabled"]:
        return

    thrift_address = str(hbase["thrift_address"])
    host, _, port = thrift_address.partition(":")
    if not host:
        logger.warning("HBase write skipped for batch=%s because HBASE_THRIFT_ADDRESS is unset", batch_id)
        return

    try:
        import happybase
    except ModuleNotFoundError:
        logger.warning("HBase write skipped for batch=%s because happybase is not installed", batch_id)
        return

    connection = happybase.Connection(host=host, port=int(port or "9090"), autoconnect=False)
    connection.open()
    table_name = str(hbase["sensor_table"])
    column_family = str(hbase["column_family"])
    existing_tables = {
        name.decode("utf-8") if isinstance(name, bytes) else str(name)
        for name in connection.tables()
    }
    if table_name not in existing_tables:
        connection.create_table(table_name, {column_family: dict()})

    table = connection.table(table_name)
    with table.batch(batch_size=500) as batch:
        for row in batch_df.select("entity_id", "payload", "processed_at").toLocalIterator():
            entity_id = str(row.entity_id or "unknown")
            processed_at = (
                row.processed_at.isoformat()
                if row.processed_at is not None and hasattr(row.processed_at, "isoformat")
                else f"batch-{batch_id}"
            )
            batch.put(
                f"{entity_id}#{processed_at}".encode("utf-8"),
                {
                    f"{column_family}:entity_id".encode("utf-8"): entity_id.encode("utf-8"),
                    f"{column_family}:payload".encode("utf-8"): str(row.payload).encode("utf-8"),
                    f"{column_family}:processed_at".encode("utf-8"): processed_at.encode("utf-8"),
                },
            )
    connection.close()
    logger.info("persisted batch=%s to hbase table=%s", batch_id, table_name)


def _persist_batch(batch_df, batch_id: int) -> None:
    cached_batch = batch_df.cache()
    _cache_batch_metadata(cached_batch, batch_id)
    _write_to_postgres(cached_batch, batch_id)
    _write_to_hdfs(cached_batch, batch_id)
    _write_to_hbase(cached_batch, batch_id)
    cached_batch.unpersist()


def main() -> None:
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import current_timestamp, expr

    kafka_bootstrap = _env("KAFKA_BROKER_URL", "kafka:9092")
    raw_topic = _env("KAFKA_RAW_EVENTS_TOPIC", "smartcito.sensors.raw")
    alerts_topic = _env("KAFKA_ALERTS_TOPIC", "smartcito.alerts")
    checkpoint_dir = _env("SPARK_CHECKPOINT_DIR", "/opt/spark/checkpoints")
    object_storage_path = _env("SPARK_OBJECT_STORAGE_PATH", "/opt/spark/object-store")
    spark_master = _env("SPARK_MASTER_URL", "local[*]")

    spark = (
        SparkSession.builder.appName("smartcito-streaming")
        .master(spark_master)
        .getOrCreate()
    )

    source = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", kafka_bootstrap)
        .option("subscribe", raw_topic)
        .option("startingOffsets", "latest")
        .load()
    )

    events = source.selectExpr(
        "CAST(key AS STRING) AS entity_id",
        "CAST(value AS STRING) AS payload",
    )
    enriched = events.withColumn("processed_at", current_timestamp())

    object_store_query = (
        enriched.writeStream.format("parquet")
        .option("checkpointLocation", f"{checkpoint_dir}/object-store")
        .option("path", object_storage_path)
        .outputMode("append")
        .start()
    )

    alerts_query = (
        enriched.filter(expr("payload LIKE '%alert%'"))
        .selectExpr("entity_id AS key", "payload AS value")
        .writeStream.format("kafka")
        .option("kafka.bootstrap.servers", kafka_bootstrap)
        .option("topic", alerts_topic)
        .option("checkpointLocation", f"{checkpoint_dir}/alerts")
        .start()
    )

    postgres_query = (
        enriched.writeStream.foreachBatch(_persist_batch)
        .option("checkpointLocation", f"{checkpoint_dir}/postgres")
        .start()
    )

    for query in (object_store_query, alerts_query, postgres_query):
        query.awaitTermination()


if __name__ == "__main__":
    main()