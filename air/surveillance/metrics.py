"""
================================================================================
 File: surveillance/metrics.py
 Purpose:
   Minimal process-local metrics for Drone Gateway observability. Kubernetes and
   Prometheus can scrape the text endpoint without requiring extra dependencies.
================================================================================
"""

from __future__ import annotations

from collections import Counter


class GatewayMetrics:
    def __init__(self) -> None:
        self._counters: Counter[str] = Counter()

    def increment(self, name: str, amount: int = 1) -> None:
        self._counters[name] += amount

    def snapshot(self) -> dict[str, int]:
        return dict(self._counters)

    def prometheus_text(self) -> str:
        lines = [
            "# HELP orca_drone_gateway_events_total Drone gateway event counters.",
            "# TYPE orca_drone_gateway_events_total counter",
        ]
        for name, value in sorted(self._counters.items()):
            lines.append(f'orca_drone_gateway_events_total{{event="{name}"}} {value}')
        return "\n".join(lines) + "\n"


metrics = GatewayMetrics()
