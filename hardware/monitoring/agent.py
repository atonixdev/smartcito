"""
================================================================================
 File: hardware/monitoring/agent.py
 Purpose:
   Tiny hardware monitoring agent model for Orca deployments.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RackHealth:
    """Snapshot of one rack's basic environmental metrics."""

    rack_id: str
    temperature_c: float
    power_kw: float


def collect_sample(rack_id: str) -> RackHealth:
    """Return a deterministic demo sample for local integrations."""
    return RackHealth(rack_id=rack_id, temperature_c=23.5, power_kw=4.2)
