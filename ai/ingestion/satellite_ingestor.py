from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from ai.ingestion.common import DEFAULT_DATASET_DIR, load_json_source, save_training_batch, stringify_fields
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from ai.ingestion.common import DEFAULT_DATASET_DIR, load_json_source, save_training_batch, stringify_fields


DEFAULT_SATELLITE_URL = "https://eonet.gsfc.nasa.gov/api/v3/events?limit=20&status=open"


def _normalize_events(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("events"), list):
        return [item for item in payload["events"] if isinstance(item, dict)]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _build_input(event: dict[str, Any], fallback_region: str) -> str:
    categories = ", ".join(category.get("title", "unknown") for category in event.get("categories", []) if isinstance(category, dict))
    geometries = event.get("geometry") if isinstance(event.get("geometry"), list) else []
    latest_geometry = geometries[-1] if geometries else {}
    coordinates = latest_geometry.get("coordinates") if isinstance(latest_geometry, dict) else None
    region = event.get("region") or event.get("title") or fallback_region
    fields = {
        "Observation": event.get("title") or "Satellite observation",
        "Region": region,
        "Categories": categories or event.get("type") or "general",
        "Cloud cover": event.get("cloud_cover") or event.get("cloudCover") or "unknown",
        "Terrain": event.get("terrain") or "unknown",
        "Temperature": event.get("temperature") or event.get("temp_c") or "unknown",
        "Storms": event.get("storm_index") or event.get("storms") or "none-reported",
        "Coordinates": coordinates,
    }
    return stringify_fields(fields)


def _build_output(event: dict[str, Any]) -> str:
    categories = {str(category.get("title", "")).lower() for category in event.get("categories", []) if isinstance(category, dict)}
    if {"wildfires", "severe storms", "volcanoes"} & categories:
        return "Elevated environmental activity detected. Increase monitoring, validate ground conditions, and prepare an operations response for the affected region."
    if "floods" in categories:
        return "Hydrologic risk detected from satellite observations. Review nearby assets, monitor water movement, and pre-stage route or field adjustments."
    return "Conditions appear stable from the available satellite observation metadata. Continue monitoring with no immediate operational escalation."


def build_training_records(payload: Any, *, region: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, event in enumerate(_normalize_events(payload), start=1):
        records.append(
            {
                "instruction": "Interpret satellite observation.",
                "input": _build_input(event, region),
                "output": _build_output(event),
                "metadata": {
                    "domain": "satellite-observation",
                    "source": "satellite-ingestor",
                    "record_id": f"satellite-{index:05d}",
                    "reviewed": False,
                },
            }
        )
    return records


def ingest_satellite(
    *,
    api_url: str = DEFAULT_SATELLITE_URL,
    input_file: str | None = None,
    region: str = "global",
    output_dir: str = str(DEFAULT_DATASET_DIR),
) -> dict[str, object]:
    payload = load_json_source(input_file=input_file, api_url=None if input_file else api_url)
    records = build_training_records(payload, region=region)
    output_path = save_training_batch(records, source="satellite", output_dir=output_dir)
    return {"output_path": str(output_path), "records": len(records), "source": "satellite"}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest satellite or earth-observation data into SmartCito training batches.")
    parser.add_argument("--api-url", default=DEFAULT_SATELLITE_URL)
    parser.add_argument("--input-file", default=None)
    parser.add_argument("--region", default="global")
    parser.add_argument("--output-dir", default=str(DEFAULT_DATASET_DIR))
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    result = ingest_satellite(
        api_url=args.api_url,
        input_file=args.input_file,
        region=args.region,
        output_dir=args.output_dir,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
