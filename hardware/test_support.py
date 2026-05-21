"""
================================================================================
 File: hardware/test_support.py
 Purpose:
   Shared helpers for SmartCito hardware CI probes. Supports simulation-first
   validation in CI and optional live endpoint checks in hardware-backed runs.
================================================================================
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, UTC
import json
import os
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen


@dataclass(slots=True)
class HardwareSnapshot:
    """Normalized hardware observation used by CI tests."""

    component: str
    endpoint: str
    firmware_version: str
    temperature_c: float
    power_kw: float
    throughput_mbps: float
    reachable: bool
    quantum_ready: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


def _semver_tuple(value: str) -> tuple[int, ...]:
    cleaned = value.strip().lstrip("v")
    return tuple(int(part) for part in cleaned.split(".") if part.isdigit())


def collect_snapshot(
    component: str,
    endpoint_env: str,
    defaults: HardwareSnapshot,
) -> HardwareSnapshot:
    """Return live hardware data when configured, otherwise a simulation snapshot."""
    mode = os.getenv("SMARTCITO_HARDWARE_CI_MODE", "simulation")
    endpoint = os.getenv(endpoint_env, defaults.endpoint)

    if mode != "simulation" and endpoint:
        try:
            with urlopen(endpoint, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))
            snapshot = HardwareSnapshot(
                component=component,
                endpoint=endpoint,
                firmware_version=payload.get("firmware_version", defaults.firmware_version),
                temperature_c=float(payload.get("temperature_c", defaults.temperature_c)),
                power_kw=float(payload.get("power_kw", defaults.power_kw)),
                throughput_mbps=float(payload.get("throughput_mbps", defaults.throughput_mbps)),
                reachable=bool(payload.get("reachable", True)),
                quantum_ready=bool(payload.get("quantum_ready", defaults.quantum_ready)),
                metadata=payload.get("metadata", defaults.metadata),
            )
        except (URLError, TimeoutError, json.JSONDecodeError, ValueError):
            snapshot = defaults
    else:
        snapshot = defaults

    record_probe_result(snapshot)
    return snapshot


def assert_snapshot(
    snapshot: HardwareSnapshot,
    *,
    minimum_firmware: str,
    maximum_temperature_c: float,
    minimum_throughput_mbps: float,
    minimum_power_kw: float,
    require_quantum_ready: bool = False,
) -> None:
    """Assert that a snapshot satisfies the SmartCito CI baseline."""
    assert snapshot.reachable, f"{snapshot.component} endpoint is unreachable"
    assert _semver_tuple(snapshot.firmware_version) >= _semver_tuple(minimum_firmware)
    assert snapshot.temperature_c <= maximum_temperature_c
    assert snapshot.throughput_mbps >= minimum_throughput_mbps
    assert snapshot.power_kw >= minimum_power_kw
    if require_quantum_ready:
        assert snapshot.quantum_ready, f"{snapshot.component} is not quantum-ready"


def record_probe_result(snapshot: HardwareSnapshot) -> None:
    """Write a JSON artifact per hardware probe for CI collection."""
    result_dir = Path(os.getenv("SMARTCITO_HARDWARE_RESULTS_DIR", "logs/hardware_results"))
    result_dir.mkdir(parents=True, exist_ok=True)
    payload = asdict(snapshot)
    payload["captured_at"] = datetime.now(UTC).isoformat()
    path = result_dir / f"{snapshot.component.replace('/', '_')}.json"
    path.write_text(json.dumps(payload, indent=2))
