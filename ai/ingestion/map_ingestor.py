from __future__ import annotations

import argparse
import json
from collections import Counter
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

try:
    from ai.ingestion.common import DEFAULT_DATASET_DIR, load_json_source, post_json, save_training_batch, stringify_fields
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from ai.ingestion.common import DEFAULT_DATASET_DIR, load_json_source, post_json, save_training_batch, stringify_fields


DEFAULT_OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def fetch_map_payload(*, api_url: str, bbox: str) -> Any:
    south, west, north, east = [part.strip() for part in bbox.split(",", maxsplit=3)]
    query = """
data=[out:json][timeout:25];
(
  way["highway"]({south},{west},{north},{east});
  way["building"]({south},{west},{north},{east});
  relation["boundary"="administrative"]({south},{west},{north},{east});
);
out tags qt;
""".strip().format(south=south, west=west, north=north, east=east)
    return post_json(api_url, urlencode({"data": query}))


def _normalize_elements(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("elements"), list):
        return [item for item in payload["elements"] if isinstance(item, dict)]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def build_training_records(payload: Any, *, bbox: str) -> list[dict[str, Any]]:
    roads: Counter[str] = Counter()
    buildings = 0
    boundaries = 0
    for element in _normalize_elements(payload):
        tags = dict(element.get("tags") or {})
        if "highway" in tags:
            roads[tags.get("name") or tags["highway"]] += 1
        if "building" in tags:
            buildings += 1
        if tags.get("boundary") == "administrative":
            boundaries += 1

    top_roads = ", ".join(name for name, _ in roads.most_common(3)) or "none-detected"
    traffic_state = "heavy" if sum(roads.values()) > 20 else "moderate" if sum(roads.values()) > 5 else "light"
    record = {
        "instruction": "Analyze map context.",
        "input": stringify_fields(
            {
                "Roads": top_roads,
                "Traffic": traffic_state,
                "Buildings": buildings,
                "Boundaries": boundaries,
                "Area": bbox,
            }
        ),
        "output": (
            "Map context indicates dense road and structure coverage. Recommend route adjustments that avoid the busiest corridors and keep operations aligned with the mapped boundaries."
            if roads
            else "Map context is limited for this area. Continue with normal routing and request more geographic detail if the mission risk changes."
        ),
        "metadata": {
            "domain": "map-context",
            "source": "map-ingestor",
            "bbox": bbox,
            "reviewed": False,
        },
    }
    return [record]


def ingest_map(
    *,
    api_url: str = DEFAULT_OVERPASS_URL,
    input_file: str | None = None,
    bbox: str = "-26.25,27.98,-26.15,28.08",
    output_dir: str = str(DEFAULT_DATASET_DIR),
) -> dict[str, object]:
    if input_file:
        payload = load_json_source(input_file=input_file, api_url=None)
    else:
        payload = fetch_map_payload(api_url=api_url, bbox=bbox)
    records = build_training_records(payload, bbox=bbox)
    output_path = save_training_batch(records, source="map", output_dir=output_dir)
    return {"output_path": str(output_path), "records": len(records), "source": "map"}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest map or geographic context into SmartCito training batches.")
    parser.add_argument("--api-url", default=DEFAULT_OVERPASS_URL)
    parser.add_argument("--input-file", default=None)
    parser.add_argument("--bbox", default="-26.25,27.98,-26.15,28.08", help="south,west,north,east")
    parser.add_argument("--output-dir", default=str(DEFAULT_DATASET_DIR))
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    result = ingest_map(api_url=args.api_url, input_file=args.input_file, bbox=args.bbox, output_dir=args.output_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
