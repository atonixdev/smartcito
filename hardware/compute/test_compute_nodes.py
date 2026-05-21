"""
================================================================================
 File: hardware/compute/test_compute_nodes.py
 Purpose:
   CI smoke tests for controller and compute node baselines.
================================================================================
"""

from __future__ import annotations

from hardware.test_support import HardwareSnapshot, assert_snapshot, collect_snapshot


def test_compute_nodes() -> None:
    snapshot = collect_snapshot(
        component="compute-nodes",
        endpoint_env="SMARTCITO_COMPUTE_ENDPOINT",
        defaults=HardwareSnapshot(
            component="compute-nodes",
            endpoint="simulation://compute",
            firmware_version="1.6.0",
            temperature_c=54.2,
            power_kw=2.8,
            throughput_mbps=51000,
            reachable=True,
            quantum_ready=True,
            metadata={"gpu_model": "nvidia-h100", "controller_nodes": 3},
        ),
    )
    assert_snapshot(
        snapshot,
        minimum_firmware="1.4.0",
        maximum_temperature_c=72.0,
        minimum_throughput_mbps=25000,
        minimum_power_kw=2.0,
        require_quantum_ready=True,
    )
    assert snapshot.metadata["controller_nodes"] >= 2
