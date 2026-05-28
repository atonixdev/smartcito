from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
DEFAULT_MODELS_DIR = Path("models")
ACTIVE_MODEL_POINTER = DEFAULT_MODELS_DIR / "active_model.json"


@dataclass(slots=True)
class OrcaTrainingRecord:
    instruction: str
    input: str
    output: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def domain(self) -> str:
        return str(self.metadata.get("domain", "general")).strip() or "general"

    @property
    def task_type(self) -> str:
        return str(self.metadata.get("task_type", self.domain)).strip() or self.domain


@dataclass(slots=True)
class OrcaTrainingMetrics:
    version: str
    records: int
    domains: dict[str, int]
    average_instruction_tokens: float
    vocabulary_size: int
    task_types: dict[str, int]


@dataclass(slots=True)
class OrcaPrediction:
    model_version: str
    task_type: str
    domain: str
    confidence: float
    decision: str
    rationale: str
    supporting_examples: list[dict[str, Any]]


@dataclass(slots=True)
class _PrototypeExample:
    instruction: str
    input: str
    output: str
    metadata: dict[str, Any]
    token_counts: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "instruction": self.instruction,
            "input": self.input,
            "output": self.output,
            "metadata": self.metadata,
            "token_counts": self.token_counts,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> _PrototypeExample:
        return cls(
            instruction=str(payload.get("instruction", "")),
            input=str(payload.get("input", "")),
            output=str(payload.get("output", "")),
            metadata=dict(payload.get("metadata") or {}),
            token_counts={str(key): int(value) for key, value in dict(payload.get("token_counts") or {}).items()},
        )


@dataclass(slots=True)
class OrcaModel:
    version: str
    created_from: str
    domain_profiles: dict[str, dict[str, int]]
    task_profiles: dict[str, dict[str, int]]
    prototypes: list[_PrototypeExample]
    metrics: OrcaTrainingMetrics

    def predict(
        self,
        *,
        task_type: str,
        instruction: str,
        input_text: str,
        context: dict[str, Any] | None = None,
        top_k: int = 2,
    ) -> OrcaPrediction:
        query_text = "\n".join(part for part in [instruction.strip(), input_text.strip()] if part)
        query_tokens = _token_counts(query_text)
        selected_domain = _infer_best_label(query_tokens, self.domain_profiles)
        selected_task = task_type.strip() or _infer_best_label(query_tokens, self.task_profiles)
        ranked_examples = _rank_examples(query_tokens, self.prototypes, domain=selected_domain, task_type=selected_task)
        supporting_examples = [
            {
                "instruction": example.instruction,
                "output": example.output,
                "metadata": example.metadata,
                "score": round(score, 4),
            }
            for score, example in ranked_examples[:top_k]
        ]

        best_output = supporting_examples[0]["output"] if supporting_examples else "No learned response available."
        confidence = ranked_examples[0][0] if ranked_examples else 0.0
        rationale_parts = [
            f"task={selected_task or 'general'}",
            f"domain={selected_domain}",
            f"matched_examples={len(supporting_examples)}",
        ]
        if context:
            rationale_parts.append(f"context_keys={','.join(sorted(str(key) for key in context.keys()))}")

        return OrcaPrediction(
            model_version=self.version,
            task_type=selected_task or "general",
            domain=selected_domain,
            confidence=round(confidence, 4),
            decision=_compose_decision(best_output, context=context),
            rationale="; ".join(rationale_parts),
            supporting_examples=supporting_examples,
        )

    def save(self, model_dir: str | Path) -> Path:
        destination = Path(model_dir)
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "model.json").write_text(
            json.dumps(
                {
                    "version": self.version,
                    "created_from": self.created_from,
                    "domain_profiles": self.domain_profiles,
                    "task_profiles": self.task_profiles,
                    "prototypes": [prototype.to_dict() for prototype in self.prototypes],
                    "metrics": asdict(self.metrics),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        (destination / "metrics.json").write_text(json.dumps(asdict(self.metrics), indent=2), encoding="utf-8")
        return destination

    @classmethod
    def load(cls, model_dir: str | Path) -> OrcaModel:
        payload = json.loads((Path(model_dir) / "model.json").read_text(encoding="utf-8"))
        return cls(
            version=str(payload["version"]),
            created_from=str(payload.get("created_from", "unknown")),
            domain_profiles={
                str(label): {str(token): int(count) for token, count in counts.items()}
                for label, counts in dict(payload.get("domain_profiles") or {}).items()
            },
            task_profiles={
                str(label): {str(token): int(count) for token, count in counts.items()}
                for label, counts in dict(payload.get("task_profiles") or {}).items()
            },
            prototypes=[_PrototypeExample.from_dict(item) for item in list(payload.get("prototypes") or [])],
            metrics=OrcaTrainingMetrics(**dict(payload.get("metrics") or {})),
        )


def _token_counts(text: str) -> dict[str, int]:
    return dict(Counter(TOKEN_PATTERN.findall(text.lower())))


def _cosine_similarity(left: dict[str, int], right: dict[str, int]) -> float:
    if not left or not right:
        return 0.0
    shared = set(left) & set(right)
    numerator = sum(left[token] * right[token] for token in shared)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def _infer_best_label(query_tokens: dict[str, int], profiles: dict[str, dict[str, int]]) -> str:
    best_label = "general"
    best_score = -1.0
    for label, profile in profiles.items():
        score = _cosine_similarity(query_tokens, profile)
        if score > best_score:
            best_label = label
            best_score = score
    return best_label


def _rank_examples(
    query_tokens: dict[str, int],
    prototypes: list[_PrototypeExample],
    *,
    domain: str,
    task_type: str,
) -> list[tuple[float, _PrototypeExample]]:
    ranked: list[tuple[float, _PrototypeExample]] = []
    for prototype in prototypes:
        score = _cosine_similarity(query_tokens, prototype.token_counts)
        if prototype.metadata.get("domain") == domain:
            score += 0.05
        if prototype.metadata.get("task_type", prototype.metadata.get("domain")) == task_type:
            score += 0.05
        ranked.append((score, prototype))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked


def _compose_decision(best_output: str, *, context: dict[str, Any] | None) -> str:
    if not context:
        return best_output
    context_suffix = "; ".join(f"{key}={value}" for key, value in sorted(context.items()))
    return f"{best_output} Context: {context_suffix}."


def train_model(
    records: list[OrcaTrainingRecord],
    *,
    version: str,
    created_from: str,
) -> OrcaModel:
    domain_profiles: dict[str, Counter[str]] = defaultdict(Counter)
    task_profiles: dict[str, Counter[str]] = defaultdict(Counter)
    vocabulary: set[str] = set()
    instruction_token_counts: list[int] = []
    prototypes: list[_PrototypeExample] = []
    task_counts: Counter[str] = Counter()
    domain_counts: Counter[str] = Counter()

    for record in records:
        token_counts = _token_counts(f"{record.instruction}\n{record.input}\n{record.output}")
        domain_profiles[record.domain].update(token_counts)
        task_profiles[record.task_type].update(token_counts)
        vocabulary.update(token_counts)
        instruction_token_counts.append(sum(_token_counts(record.instruction).values()))
        task_counts[record.task_type] += 1
        domain_counts[record.domain] += 1
        prototypes.append(
            _PrototypeExample(
                instruction=record.instruction,
                input=record.input,
                output=record.output,
                metadata=record.metadata,
                token_counts=token_counts,
            )
        )

    metrics = OrcaTrainingMetrics(
        version=version,
        records=len(records),
        domains=dict(domain_counts),
        average_instruction_tokens=round(sum(instruction_token_counts) / len(instruction_token_counts), 4) if instruction_token_counts else 0.0,
        vocabulary_size=len(vocabulary),
        task_types=dict(task_counts),
    )

    return OrcaModel(
        version=version,
        created_from=created_from,
        domain_profiles={label: dict(counter) for label, counter in domain_profiles.items()},
        task_profiles={label: dict(counter) for label, counter in task_profiles.items()},
        prototypes=prototypes,
        metrics=metrics,
    )


def _version_sort_key(path: Path) -> int:
    stem = path.name.rsplit("_v", 1)[-1]
    try:
        return int(stem)
    except ValueError:
        return 0


def next_model_version(models_dir: str | Path = DEFAULT_MODELS_DIR) -> str:
    directory = Path(models_dir)
    existing = sorted((path for path in directory.glob("orca_model_v*") if path.is_dir()), key=_version_sort_key)
    next_version = _version_sort_key(existing[-1]) + 1 if existing else 1
    return f"orca_model_v{next_version}"


def set_active_model(model_dir: str | Path, *, models_dir: str | Path = DEFAULT_MODELS_DIR) -> Path:
    directory = Path(models_dir)
    directory.mkdir(parents=True, exist_ok=True)
    pointer = directory / ACTIVE_MODEL_POINTER.name
    payload = {"active_model_dir": str(Path(model_dir))}
    pointer.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return pointer


def load_active_model(*, models_dir: str | Path = DEFAULT_MODELS_DIR) -> OrcaModel:
    pointer = Path(models_dir) / ACTIVE_MODEL_POINTER.name
    payload = json.loads(pointer.read_text(encoding="utf-8"))
    return OrcaModel.load(payload["active_model_dir"])
