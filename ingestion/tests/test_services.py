from fastapi.testclient import TestClient

from ingestion.kafka_producer_service import app as kafka_app
from ingestion.spark_service import app as spark_app


kafka_client = TestClient(kafka_app)
spark_client = TestClient(spark_app)


def test_kafka_health() -> None:
    response = kafka_client.get("/health")

    assert response.status_code == 200
    assert response.json()["service"] == "ingestion-kafka-producer"


def test_kafka_ready_defaults() -> None:
    response = kafka_client.get("/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["bootstrap_servers"] == "kafka:9092"
    assert payload["topic"] == "smartcito.sensors.raw"
    assert payload["storage"]["postgres"]["primary_host"] == "postgres"
    assert payload["storage"]["hdfs"]["enabled"] is False
    assert payload["storage"]["hbase"]["enabled"] is False


def test_spark_pipeline_shape() -> None:
    response = spark_client.get("/pipeline")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "kafka"
    assert "validate-schema" in payload["transformations"]


def test_spark_ready_reports_storage_contract() -> None:
    response = spark_client.get("/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["storage"]["postgres"]["primary_host"] == "postgres"
    assert payload["storage"]["hdfs"]["raw_path"] == "/smartcito/raw"
    assert payload["storage"]["hbase"]["sensor_table"] == "smartcito_sensor_events"