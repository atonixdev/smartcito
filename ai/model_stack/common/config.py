"""YAML configuration loading helpers."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_yaml_config(path: str | Path) -> dict[str, Any]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ValueError(f"Expected mapping in config file: {path}")
    return payload


def load_module_config(module_dir: str | Path, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    module_dir = Path(module_dir)
    config = load_yaml_config(module_dir / "config.yaml")
    if overrides:
        config = _deep_merge(config, overrides)
    return config