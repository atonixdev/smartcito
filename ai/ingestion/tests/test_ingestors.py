from __future__ import annotations

import json
from pathlib import Path

from ai.ingestion import common
from ai.ingestion.gps_ingestor import ingest_gps
from ai.ingestion.map_ingestor import ingest_map
from ai.ingestion.satellite_ingestor import ingest_satellite
from ai.ingestion.space_weather_ingestor import ingest_space_weather


FIXTURES_DIR = Path(__file__).resolve().parents[2] / "datasets" / "fixtures"


def test_space_weather_ingestor_writes_batch(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(common, "DEFAULT_DATASET_DIR", tmp_path)

    result = ingest_space_weather(
        region="Johannesburg",
        k_index_input_file=str(FIXTURES_DIR / "space_weather_k_index.json"),
        xray_input_file=str(FIXTURES_DIR / "space_weather_xray.json"),
        output_dir=str(tmp_path),
    )

    output_path = Path(str(result["output_path"]))
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert output_path.name.startswith("batch_space_weather_")
    assert payload[0]["instruction"] == "Analyze space weather impact."
    assert payload[0]["metadata"]["domain"] == "space-weather"


def test_satellite_ingestor_writes_batch(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(common, "DEFAULT_DATASET_DIR", tmp_path)

    result = ingest_satellite(
        input_file=str(FIXTURES_DIR / "satellite_events.json"),
        region="Johannesburg",
        output_dir=str(tmp_path),
    )

    payload = json.loads(Path(str(result["output_path"])).read_text(encoding="utf-8"))
    assert payload[0]["instruction"] == "Interpret satellite observation."
    assert payload[0]["metadata"]["domain"] == "satellite-observation"


def test_gps_ingestor_writes_batch(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(common, "DEFAULT_DATASET_DIR", tmp_path)

    result = ingest_gps(
        input_file=str(FIXTURES_DIR / "gps_logs.json"),
        output_dir=str(tmp_path),
    )

    payload = json.loads(Path(str(result["output_path"])).read_text(encoding="utf-8"))
    assert payload[0]["instruction"] == "Analyze GPS movement."
    assert "Lat:" in payload[0]["input"]
    assert payload[0]["metadata"]["domain"] == "gps-analytics"


def test_map_ingestor_writes_batch(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(common, "DEFAULT_DATASET_DIR", tmp_path)

    result = ingest_map(
        input_file=str(FIXTURES_DIR / "map_overpass.json"),
        bbox="-26.25,27.98,-26.15,28.08",
        output_dir=str(tmp_path),
    )

    payload = json.loads(Path(str(result["output_path"])).read_text(encoding="utf-8"))
    assert payload[0]["instruction"] == "Analyze map context."
    assert "M1 North" in payload[0]["input"]
    assert payload[0]["metadata"]["domain"] == "map-context"
