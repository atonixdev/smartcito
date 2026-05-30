"""
================================================================================
 File: app/core/topic_config.py
 Purpose:
   Load the shared event topic map from ingestion/config/topics.yml so backend
   consumers and producers use the same logical topics as ingestion services.
================================================================================
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml


def _candidate_topic_paths() -> list[Path]:
    current_file = Path(__file__).resolve()
    candidates: list[Path] = []

    for parent in current_file.parents:
        candidates.append(parent / "ingestion" / "config" / "topics.yml")

    candidates.extend(
        [
            Path("/app/ingestion/config/topics.yml"),
            Path("/ingestion/config/topics.yml"),
        ]
    )

    unique_candidates: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        unique_candidates.append(candidate)

    return unique_candidates


@lru_cache(maxsize=1)
def load_topics() -> dict[str, str]:
    config_path = next((path for path in _candidate_topic_paths() if path.is_file()), None)
    if config_path is None:
        searched = ", ".join(str(path) for path in _candidate_topic_paths())
        raise FileNotFoundError(f"Unable to locate ingestion/config/topics.yml. Checked: {searched}")

    payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    topics = payload.get("topics", {})
    if not isinstance(topics, dict):
        raise ValueError("ingestion/config/topics.yml must contain a 'topics' mapping")
    return {str(key): str(value) for key, value in topics.items()}
