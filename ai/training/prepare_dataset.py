from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_SYSTEM_PROMPT = (
    "You are Orca Model, a domain-specialized operations assistant for "
    "city safety, sensor fusion, drone missions, camera analytics, geographic "
    "reasoning, and infrastructure orchestration."
)


@dataclass(slots=True)
class OrcaTrainingRecord:
    instruction: str
    input: str
    output: str
    metadata: dict[str, Any]


def _stringify_fields(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    for key, value in payload.items():
        if key == "metadata":
            continue
        parts.append(f"{key}: {value}")
    return "; ".join(parts)


def _load_json_payload(input_path: Path) -> Any:
    text = input_path.read_text(encoding="utf-8")
    if input_path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    return json.loads(text)


def _normalize_metadata(raw_metadata: Any, index: int) -> dict[str, Any]:
    if isinstance(raw_metadata, dict):
        metadata = dict(raw_metadata)
    else:
        metadata = {"source": str(raw_metadata) if raw_metadata is not None else "unknown"}

    metadata.setdefault("record_id", f"orca-{index:05d}")
    metadata.setdefault("license", "contributor-provided")
    metadata.setdefault("reviewed", False)
    return metadata


def normalize_record(raw_record: dict[str, Any], index: int) -> OrcaTrainingRecord:
    instruction = str(raw_record.get("instruction", "")).strip()
    input_text = str(raw_record.get("input", "")).strip()
    output_text = str(raw_record.get("output", "")).strip()
    if not instruction:
        raise ValueError(f"Record {index} is missing an instruction.")
    if not output_text:
        raise ValueError(f"Record {index} is missing an output.")

    return OrcaTrainingRecord(
        instruction=instruction,
        input=input_text,
        output=output_text,
        metadata=_normalize_metadata(raw_record.get("metadata"), index),
    )


def build_record_from_drone_log(raw_record: dict[str, Any], index: int) -> OrcaTrainingRecord:
    metadata = _normalize_metadata(raw_record.get("metadata"), index)
    metadata.setdefault("domain", "drone-operations")
    return OrcaTrainingRecord(
        instruction=str(raw_record.get("instruction") or "Plan a safe drone mission response."),
        input=str(raw_record.get("input") or _stringify_fields(raw_record)),
        output=str(raw_record.get("output") or "Recommend a safe flight path, altitude, and operator action based on the drone telemetry."),
        metadata=metadata,
    )


def build_record_from_robot_log(raw_record: dict[str, Any], index: int) -> OrcaTrainingRecord:
    metadata = _normalize_metadata(raw_record.get("metadata"), index)
    metadata.setdefault("domain", "robot-navigation")
    return OrcaTrainingRecord(
        instruction=str(raw_record.get("instruction") or "Summarize robot navigation risk and the next operator action."),
        input=str(raw_record.get("input") or _stringify_fields(raw_record)),
        output=str(raw_record.get("output") or "Describe the navigation issue, recommend a reroute, and state the speed or safety adjustment required."),
        metadata=metadata,
    )


def build_record_from_camera_log(raw_record: dict[str, Any], index: int) -> OrcaTrainingRecord:
    metadata = _normalize_metadata(raw_record.get("metadata"), index)
    metadata.setdefault("domain", "camera-analytics")
    return OrcaTrainingRecord(
        instruction=str(raw_record.get("instruction") or "Assess a city camera anomaly and recommend the next response step."),
        input=str(raw_record.get("input") or _stringify_fields(raw_record)),
        output=str(raw_record.get("output") or "Classify the event, state confidence, and recommend monitoring or escalation actions."),
        metadata=metadata,
    )


def build_record_from_sensor_log(raw_record: dict[str, Any], index: int) -> OrcaTrainingRecord:
    metadata = _normalize_metadata(raw_record.get("metadata"), index)
    metadata.setdefault("domain", "sensor-fusion")
    return OrcaTrainingRecord(
        instruction=str(raw_record.get("instruction") or "Fuse edge sensor readings into an operational assessment."),
        input=str(raw_record.get("input") or _stringify_fields(raw_record)),
        output=str(raw_record.get("output") or "Summarize the risk level, explain the correlated signals, and recommend the next city-operations action."),
        metadata=metadata,
    )


def build_record_from_geographic_log(raw_record: dict[str, Any], index: int) -> OrcaTrainingRecord:
    metadata = _normalize_metadata(raw_record.get("metadata"), index)
    metadata.setdefault("domain", "geographic-reasoning")
    return OrcaTrainingRecord(
        instruction=str(raw_record.get("instruction") or "Reason about a geographic deployment plan."),
        input=str(raw_record.get("input") or _stringify_fields(raw_record)),
        output=str(raw_record.get("output") or "Select the safest nearby assets, describe the route, and explain the geographic constraints."),
        metadata=metadata,
    )


def build_record_from_threat_log(raw_record: dict[str, Any], index: int) -> OrcaTrainingRecord:
    metadata = _normalize_metadata(raw_record.get("metadata"), index)
    metadata.setdefault("domain", "threat-reasoning")
    return OrcaTrainingRecord(
        instruction=str(raw_record.get("instruction") or "Assess a threat or incident and recommend the immediate response."),
        input=str(raw_record.get("input") or _stringify_fields(raw_record)),
        output=str(raw_record.get("output") or "State the threat level, justify it from the evidence, and recommend containment and notification actions."),
        metadata=metadata,
    )


def build_record_from_operator_log(raw_record: dict[str, Any], index: int) -> OrcaTrainingRecord:
    metadata = _normalize_metadata(raw_record.get("metadata"), index)
    metadata.setdefault("domain", "operator-workflows")
    return OrcaTrainingRecord(
        instruction=str(raw_record.get("instruction") or "Summarize the operator action and recommended follow-up."),
        input=str(raw_record.get("input") or _stringify_fields(raw_record)),
        output=str(raw_record.get("output") or "Describe the decision the operator made, the reason it was taken, and the next action the system should coordinate."),
        metadata=metadata,
    )


RAW_LOG_BUILDERS = {
    "orca": normalize_record,
    "drone": build_record_from_drone_log,
    "robot": build_record_from_robot_log,
    "camera": build_record_from_camera_log,
    "sensor": build_record_from_sensor_log,
    "geographic": build_record_from_geographic_log,
    "threat": build_record_from_threat_log,
    "operator": build_record_from_operator_log,
}


def load_records(input_path: str | Path, *, source_type: str = "orca") -> list[OrcaTrainingRecord]:
    path = Path(input_path)
    payload = _load_json_payload(path)
    if not isinstance(payload, list):
        raise ValueError("Training data must be a JSON array or JSONL sequence.")

    if source_type not in RAW_LOG_BUILDERS:
        raise ValueError(f"Unsupported source_type: {source_type}")

    builder = RAW_LOG_BUILDERS[source_type]

    normalized: list[OrcaTrainingRecord] = []
    for index, raw_record in enumerate(payload, start=1):
        if not isinstance(raw_record, dict):
            raise ValueError(f"Record {index} must be a JSON object.")
        normalized.append(builder(raw_record, index))
    return normalized


def build_chat_example(
    record: OrcaTrainingRecord,
    *,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
) -> dict[str, Any]:
    user_sections = [f"Instruction:\n{record.instruction}"]
    if record.input:
        user_sections.append(f"Input:\n{record.input}")

    text = (
        "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n"
        f"{system_prompt}\n"
        "<|eot_id|><|start_header_id|>user<|end_header_id|>\n"
        f"{'\n\n'.join(user_sections)}\n"
        "<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
        f"{record.output}\n"
        "<|eot_id|>"
    )

    return {
        "instruction": record.instruction,
        "input": record.input,
        "output": record.output,
        "metadata": record.metadata,
        "text": text,
    }


def export_prepared_dataset(
    input_path: str | Path,
    output_path: str | Path,
    *,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    source_type: str = "orca",
) -> int:
    records = load_records(input_path, source_type=source_type)
    prepared = [build_chat_example(record, system_prompt=system_prompt) for record in records]

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.suffix.lower() == ".jsonl":
        destination.write_text(
            "\n".join(json.dumps(item, ensure_ascii=False) for item in prepared) + "\n",
            encoding="utf-8",
        )
    else:
        destination.write_text(json.dumps(prepared, indent=2, ensure_ascii=False), encoding="utf-8")
    return len(prepared)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare Orca fine-tuning datasets.")
    parser.add_argument(
        "--input",
        default="ai/datasets/sample_training_data.json",
        help="Path to raw Orca training data in JSON or JSONL format.",
    )
    parser.add_argument(
        "--output",
        default="ai/datasets/prepared_orca_training_data.jsonl",
        help="Path to the prepared supervised fine-tuning dataset.",
    )
    parser.add_argument(
        "--system-prompt",
        default=DEFAULT_SYSTEM_PROMPT,
        help="System prompt prepended to each training example.",
    )
    parser.add_argument(
        "--source-type",
        choices=tuple(RAW_LOG_BUILDERS.keys()),
        default="orca",
        help="Interpret the input as an existing Orca dataset or normalize raw drone, robot, camera, sensor, geographic, or threat logs.",
    )
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    record_count = export_prepared_dataset(
        args.input,
        args.output,
        system_prompt=args.system_prompt,
        source_type=args.source_type,
    )
    print(f"Prepared {record_count} Orca training records at {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())