from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate Orca LoRA adapters before submission.")
    parser.add_argument("--dataset", default="datasets/sample_evaluation_data.json")
    parser.add_argument("--base-model", default=os.getenv("ORCA_BASE_MODEL_ID", ""))
    parser.add_argument("--adapter-path", default="output/orca-lora")
    parser.add_argument("--backend", default="merged-local")
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--max-tokens", type=int, default=180)
    parser.add_argument("--output", default="output/orca-lora/evaluation_summary.json")
    parser.add_argument(
        "--markdown-report",
        default="output/orca-lora/evaluation_report.md",
        help="Path for a PR-ready Markdown evaluation report.",
    )
    parser.add_argument(
        "--pass-threshold",
        type=float,
        default=0.65,
        help="Minimum per-example overall score required to pass.",
    )
    parser.add_argument(
        "--predictions-file",
        default=None,
        help="Optional JSON file with precomputed predictions so scoring can run without live inference.",
    )
    return parser


def _tokenize(text: str) -> set[str]:
    return set(TOKEN_PATTERN.findall(text.lower()))


def _coverage_score(expected: str, actual: str) -> float:
    expected_tokens = _tokenize(expected)
    if not expected_tokens:
        return 1.0
    actual_tokens = _tokenize(actual)
    return round(len(expected_tokens & actual_tokens) / len(expected_tokens), 4)


def _precision_score(expected: str, actual: str) -> float:
    actual_tokens = _tokenize(actual)
    if not actual_tokens:
        return 0.0
    expected_tokens = _tokenize(expected)
    return round(len(expected_tokens & actual_tokens) / len(actual_tokens), 4)


def _f1_score(recall: float, precision: float) -> float:
    if recall == 0.0 and precision == 0.0:
        return 0.0
    return round((2 * recall * precision) / (recall + precision), 4)


def _list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _term_coverage_score(terms: list[str], actual: str) -> float:
    if not terms:
        return 1.0
    actual_tokens = _tokenize(actual)
    normalized_terms = [_tokenize(term) for term in terms]
    matched = 0
    for term_tokens in normalized_terms:
        if term_tokens and term_tokens.issubset(actual_tokens):
            matched += 1
    return round(matched / len(normalized_terms), 4)


def _violating_terms(terms: list[str], actual: str) -> list[str]:
    actual_tokens = _tokenize(actual)
    violations: list[str] = []
    for term in terms:
        term_tokens = _tokenize(term)
        if term_tokens and term_tokens.issubset(actual_tokens):
            violations.append(term)
    return violations


def _load_records(dataset_path: str | Path) -> list[dict[str, Any]]:
    payload = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Evaluation dataset must be a JSON array.")
    return payload


def _load_predictions(predictions_path: str | Path | None) -> dict[str, str]:
    if not predictions_path:
        return {}

    payload = json.loads(Path(predictions_path).read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return {str(key): str(value) for key, value in payload.items()}
    if not isinstance(payload, list):
        raise ValueError("Predictions file must be a JSON object or JSON array.")

    predictions: dict[str, str] = {}
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Prediction entries must be JSON objects.")
        record_id = str(item.get("id", "")).strip()
        output = str(item.get("actual_output") or item.get("prediction") or item.get("output") or "").strip()
        if record_id and output:
            predictions[record_id] = output
    return predictions


def _load_generate_text():
    try:
        from ai_models.llama_stack import generate_text
        return generate_text
    except ModuleNotFoundError:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from ai_models.llama_stack import generate_text
        return generate_text


def _resolve_base_model_id(args: argparse.Namespace) -> str:
    base_model = str(args.base_model or "").strip()
    if base_model:
        return base_model
    raise ValueError(
        "A base model id is required for live evaluation. Set ORCA_BASE_MODEL_ID or pass --base-model with a compatible model from an official provider source."
    )


def _score_record(record: dict[str, Any], actual: str, pass_threshold: float) -> dict[str, Any]:
    expected = str(record.get("expected_output") or record.get("output") or "").strip()
    recall = _coverage_score(expected, actual)
    precision = _precision_score(expected, actual)
    f1_score = _f1_score(recall, precision)
    required_terms = _list_of_strings(record.get("required_terms"))
    banned_terms = _list_of_strings(record.get("banned_terms"))
    rubric_terms = _list_of_strings(record.get("rubric_keywords"))
    required_term_score = _term_coverage_score(required_terms, actual)
    rubric_score = _term_coverage_score(rubric_terms, actual)
    banned_violations = _violating_terms(banned_terms, actual)
    overall_score = round(
        (recall * 0.35)
        + (precision * 0.20)
        + (f1_score * 0.25)
        + (required_term_score * 0.10)
        + (rubric_score * 0.10),
        4,
    )
    passed = overall_score >= pass_threshold and not banned_violations
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}

    return {
        "id": record.get("id"),
        "domain": metadata.get("domain", "general"),
        "expected_output": expected,
        "actual_output": actual,
        "metrics": {
            "recall": recall,
            "precision": precision,
            "f1": f1_score,
            "required_term_score": required_term_score,
            "rubric_score": rubric_score,
            "overall_score": overall_score,
        },
        "required_terms": required_terms,
        "rubric_keywords": rubric_terms,
        "banned_term_violations": banned_violations,
        "passed": passed,
    }


def _summarize_domains(item_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in item_results:
        grouped.setdefault(str(item.get("domain", "general")), []).append(item)

    summary: list[dict[str, Any]] = []
    for domain, items in sorted(grouped.items()):
        average_score = round(
            sum(entry["metrics"]["overall_score"] for entry in items) / len(items),
            4,
        )
        passed = sum(1 for entry in items if entry["passed"])
        summary.append(
            {
                "domain": domain,
                "records": len(items),
                "average_overall_score": average_score,
                "pass_rate": round(passed / len(items), 4),
            }
        )
    return summary


def _render_markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Orca Adapter Evaluation Report",
        "",
        f"- Model: {summary['model_name']}",
        f"- Base model: {summary['base_model']}",
        f"- Backend: {summary['backend']}",
        f"- Dataset: {summary['dataset']}",
        f"- Adapter path: {summary['adapter_path']}",
        f"- Average overall score: {summary['average_overall_score']:.4f}",
        f"- Pass rate: {summary['pass_rate']:.4f}",
        f"- Records: {summary['records']}",
        "",
        "## Domain Summary",
        "",
        "| Domain | Records | Avg Score | Pass Rate |",
        "| ------ | ------- | --------- | --------- |",
    ]
    for domain in summary["domains"]:
        lines.append(
            f"| {domain['domain']} | {domain['records']} | {domain['average_overall_score']:.4f} | {domain['pass_rate']:.4f} |"
        )

    lines.extend([
        "",
        "## Per-Example Results",
        "",
        "| ID | Domain | Overall | Recall | Precision | F1 | Required | Rubric | Passed | Violations |",
        "| -- | ------ | ------- | ------ | --------- | -- | -------- | ------ | ------ | ---------- |",
    ])
    for item in summary["results"]:
        metrics = item["metrics"]
        violations = ", ".join(item["banned_term_violations"]) or "none"
        lines.append(
            f"| {item['id']} | {item['domain']} | {metrics['overall_score']:.4f} | {metrics['recall']:.4f} | {metrics['precision']:.4f} | {metrics['f1']:.4f} | {metrics['required_term_score']:.4f} | {metrics['rubric_score']:.4f} | {'yes' if item['passed'] else 'no'} | {violations} |"
        )
    return "\n".join(lines) + "\n"


async def _evaluate_async(args: argparse.Namespace) -> dict[str, Any]:
    records = _load_records(args.dataset)
    predictions = _load_predictions(args.predictions_file)
    generate_text = None
    item_results: list[dict[str, Any]] = []
    base_model_id = str(args.base_model or "").strip()

    for index, record in enumerate(records, start=1):
        record_id = str(record.get("id", f"eval-{index:03d}"))
        instruction = str(record.get("instruction", "")).strip()
        input_text = str(record.get("input", "")).strip()
        expected = str(record.get("expected_output") or record.get("output") or "").strip()
        if not instruction or not expected:
            raise ValueError(f"Evaluation record {index} must include instruction and expected_output/output.")

        actual = predictions.get(record_id, "")
        if not actual:
            if generate_text is None:
                generate_text = _load_generate_text()
                base_model_id = _resolve_base_model_id(args)
            prompt = instruction if not input_text else f"{instruction}\n\nInput:\n{input_text}"
            response = await generate_text(
                prompt,
                system_prompt="You are a Orca evaluation assistant.",
                model=base_model_id,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
                backend=args.backend,
                adapter_path=args.adapter_path,
                merge_lora=args.backend == "merged-local",
            )
            actual = str(response.get("text", "")).strip()

        scored = _score_record(record, actual, args.pass_threshold)
        scored["id"] = record_id
        scored["instruction"] = instruction
        item_results.append(scored)

    average_overall_score = round(
        sum(item["metrics"]["overall_score"] for item in item_results) / len(item_results),
        4,
    ) if item_results else 0.0
    pass_rate = round(
        sum(1 for item in item_results if item["passed"]) / len(item_results),
        4,
    ) if item_results else 0.0
    domain_summary = _summarize_domains(item_results)

    return {
        "model_name": "Orca Model",
        "base_model": base_model_id or None,
        "adapter_path": args.adapter_path,
        "backend": args.backend,
        "dataset": args.dataset,
        "predictions_file": args.predictions_file,
        "average_overall_score": average_overall_score,
        "pass_rate": pass_rate,
        "pass_threshold": args.pass_threshold,
        "records": len(item_results),
        "domains": domain_summary,
        "results": item_results,
    }


def main() -> int:
    import asyncio

    args = build_arg_parser().parse_args()
    summary = asyncio.run(_evaluate_async(args))
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report_path = Path(args.markdown_report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_render_markdown_report(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())