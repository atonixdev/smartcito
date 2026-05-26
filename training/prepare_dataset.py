from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_SYSTEM_PROMPT = (
    "You are SmartCito-LLaMA3-8B, a domain-specialized operations assistant for "
    "city safety, sensor fusion, drone missions, camera analytics, geographic "
    "reasoning, and infrastructure orchestration."
)


@dataclass(slots=True)
class SmartCitoTrainingRecord:
    instruction: str
    input: str
    output: str
    metadata: dict[str, Any]


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

    metadata.setdefault("record_id", f"smartcito-{index:05d}")
    metadata.setdefault("license", "contributor-provided")
    metadata.setdefault("reviewed", False)
    return metadata


def normalize_record(raw_record: dict[str, Any], index: int) -> SmartCitoTrainingRecord:
    instruction = str(raw_record.get("instruction", "")).strip()
    input_text = str(raw_record.get("input", "")).strip()
    output_text = str(raw_record.get("output", "")).strip()
    if not instruction:
        raise ValueError(f"Record {index} is missing an instruction.")
    if not output_text:
        raise ValueError(f"Record {index} is missing an output.")

    return SmartCitoTrainingRecord(
        instruction=instruction,
        input=input_text,
        output=output_text,
        metadata=_normalize_metadata(raw_record.get("metadata"), index),
    )


def load_records(input_path: str | Path) -> list[SmartCitoTrainingRecord]:
    path = Path(input_path)
    payload = _load_json_payload(path)
    if not isinstance(payload, list):
        raise ValueError("Training data must be a JSON array or JSONL sequence.")

    normalized: list[SmartCitoTrainingRecord] = []
    for index, raw_record in enumerate(payload, start=1):
        if not isinstance(raw_record, dict):
            raise ValueError(f"Record {index} must be a JSON object.")
        normalized.append(normalize_record(raw_record, index))
    return normalized


def build_chat_example(
    record: SmartCitoTrainingRecord,
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
) -> int:
    records = load_records(input_path)
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
    parser = argparse.ArgumentParser(description="Prepare SmartCito fine-tuning datasets.")
    parser.add_argument(
        "--input",
        default="datasets/sample_training_data.json",
        help="Path to raw SmartCito training data in JSON or JSONL format.",
    )
    parser.add_argument(
        "--output",
        default="datasets/prepared_smartcito_training_data.jsonl",
        help="Path to the prepared supervised fine-tuning dataset.",
    )
    parser.add_argument(
        "--system-prompt",
        default=DEFAULT_SYSTEM_PROMPT,
        help="System prompt prepended to each training example.",
    )
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    record_count = export_prepared_dataset(
        args.input,
        args.output,
        system_prompt=args.system_prompt,
    )
    print(f"Prepared {record_count} SmartCito training records at {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())