from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


AI_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_DIR = AI_ROOT / "datasets"
DEFAULT_TIMEOUT_SECONDS = 30


def _normalize_output_dir(output_dir: str | Path = DEFAULT_DATASET_DIR) -> Path:
    requested = Path(output_dir)
    destination = requested if requested.is_absolute() else (Path.cwd() / requested)
    destination = destination.resolve()
    allowed_root = DEFAULT_DATASET_DIR.resolve()
    if destination != allowed_root and allowed_root not in destination.parents:
        raise ValueError(f"Output path must stay inside {allowed_root}")
    destination.mkdir(parents=True, exist_ok=True)
    return destination


def fetch_json(url: str, *, timeout: int = DEFAULT_TIMEOUT_SECONDS, headers: dict[str, str] | None = None) -> Any:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Orca-Ingestion/1.0",
            **(headers or {}),
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"Unable to fetch JSON from {url}: {exc}") from exc


def post_json(url: str, payload: str, *, timeout: int = DEFAULT_TIMEOUT_SECONDS, headers: dict[str, str] | None = None) -> Any:
    body = payload.encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            "User-Agent": "Orca-Ingestion/1.0",
            **(headers or {}),
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"Unable to post JSON to {url}: {exc}") from exc


def load_json_source(*, input_file: str | Path | None = None, api_url: str | None = None) -> Any:
    if input_file:
        path = Path(input_file)
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".jsonl":
            return [json.loads(line) for line in text.splitlines() if line.strip()]
        return json.loads(text)
    if api_url:
        return fetch_json(api_url)
    raise ValueError("Provide either --input-file or an API URL.")


def stringify_fields(fields: dict[str, Any]) -> str:
    parts: list[str] = []
    for key, value in fields.items():
        if value is None or value == "":
            continue
        parts.append(f"{key}: {value}")
    return "; ".join(parts)


def save_training_batch(
    records: list[dict[str, Any]],
    *,
    source: str,
    output_dir: str | Path = DEFAULT_DATASET_DIR,
) -> Path:
    destination_dir = _normalize_output_dir(output_dir)
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
    destination = destination_dir / f"batch_{source}_{timestamp}.json"
    destination.write_text(json.dumps(records, indent=2), encoding="utf-8")
    return destination
