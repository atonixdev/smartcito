"""
================================================================================
 File: hardware/networking/test_network_transmission.py
 Purpose:
   CI smoke tests for secure network throughput and quantum-ready transport.
================================================================================
"""

from __future__ import annotations

from hardware.test_support import HardwareSnapshot, assert_snapshot, collect_snapshot


def test_network_transmission() -> None:
    snapshot = collect_snapshot(
        component="network-transmission",
        endpoint_env="SMARTCITO_NETWORK_ENDPOINT",
        defaults=HardwareSnapshot(
            component="network-transmission",
            endpoint="simulation://network",
            firmware_version="3.0.2",
            temperature_c=33.1,
            power_kw=1.6,
            throughput_mbps=64000,
            reachable=True,
            quantum_ready=True,
            metadata={"latency_ms": 3.2, "segment": "ingest"},
        ),
    )
    assert_snapshot(
        snapshot,
        minimum_firmware="3.0.0",
        maximum_temperature_c=45.0,
        minimum_throughput_mbps=40000,
        minimum_power_kw=1.0,
        require_quantum_ready=True,
    )
    assert snapshot.metadata["latency_ms"] <= 10.0
