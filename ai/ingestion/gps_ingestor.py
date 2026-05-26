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


def _normalize_logs(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        return [item for item in payload["records"] if isinstance(item, dict)]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _movement_output(log: dict[str, Any]) -> str:
    speed = float(log.get("speed") or log.get("speed_kmh") or 0.0)
    heading = float(log.get("heading") or 0.0)
    if speed > 120:
        return "Movement is unusually fast for the tracked asset. Validate the GPS feed, confirm the asset type, and review for route deviation or telemetry error."
    if 0 < speed < 2:
        return "Movement is minimal. Treat the asset as stationary or in hold mode unless nearby operational context suggests otherwise."
    if 180 <= heading <= 220:
        return "Movement appears stable on a southbound heading. No immediate action is required unless geofence or route constraints change."
    return "Movement normal. No action required."


def build_training_records(payload: Any) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, log in enumerate(_normalize_logs(payload), start=1):
        records.append(
            {
                "instruction": "Analyze GPS movement.",
                "input": stringify_fields(
                    {
                        "Lat": log.get("latitude") or log.get("lat"),
                        "Lon": log.get("longitude") or log.get("lon"),
                        "Altitude": log.get("altitude") or log.get("alt"),
                        "Speed": log.get("speed") or log.get("speed_kmh"),
                        "Heading": log.get("heading"),
                        "Timestamp": log.get("timestamp") or log.get("time"),
                    }
                ),
                "output": _movement_output(log),
                "metadata": {
                    "domain": "gps-analytics",
                    "source": "gps-ingestor",
                    "record_id": f"gps-{index:05d}",
                    "reviewed": False,
                },
            }
        )
    return records


def ingest_gps(
    *,
    api_url: str | None = None,
    input_file: str | None = None,
    output_dir: str = str(DEFAULT_DATASET_DIR),
) -> dict[str, object]:
    payload = load_json_source(input_file=input_file, api_url=api_url)
    records = build_training_records(payload)
    output_path = save_training_batch(records, source="gps", output_dir=output_dir)
    return {"output_path": str(output_path), "records": len(records), "source": "gps"}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest GPS or GNSS data into SmartCito training batches.")
    parser.add_argument("--api-url", default=None, help="Optional API endpoint for JSON GPS/GNSS logs.")
    parser.add_argument("--input-file", default=None, help="Optional JSON or JSONL file containing GPS/GNSS logs.")
    parser.add_argument("--output-dir", default=str(DEFAULT_DATASET_DIR))
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    result = ingest_gps(api_url=args.api_url, input_file=args.input_file, output_dir=args.output_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
