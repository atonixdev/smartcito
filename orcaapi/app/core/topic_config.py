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


@lru_cache(maxsize=1)
def load_topics() -> dict[str, str]:
    repo_root = Path(__file__).resolve().parents[3]
    config_path = repo_root / "ingestion" / "config" / "topics.yml"
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    topics = payload.get("topics", {})
    if not isinstance(topics, dict):
        raise ValueError("ingestion/config/topics.yml must contain a 'topics' mapping")
    return {str(key): str(value) for key, value in topics.items()}
