"""
================================================================================
 File: hardware/racks/test_power_distribution.py
 Purpose:
   CI smoke tests for rack power redundancy, thermal envelope, and UPS state.
================================================================================
"""

from __future__ import annotations

from hardware.test_support import HardwareSnapshot, assert_snapshot, collect_snapshot


def test_power_distribution() -> None:
    snapshot = collect_snapshot(
        component="rack-power",
        endpoint_env="SMARTCITO_RACK_ENDPOINT",
        defaults=HardwareSnapshot(
            component="rack-power",
            endpoint="simulation://racks",
            firmware_version="4.4.0",
            temperature_c=29.4,
            power_kw=6.7,
            throughput_mbps=2000,
            reachable=True,
            metadata={"feed_redundancy": "A+B", "ups_runtime_minutes": 42},
        ),
    )
    assert_snapshot(
        snapshot,
        minimum_firmware="4.2.0",
        maximum_temperature_c=37.0,
        minimum_throughput_mbps=500,
        minimum_power_kw=4.0,
    )
    assert snapshot.metadata["feed_redundancy"] == "A+B"
    assert snapshot.metadata["ups_runtime_minutes"] >= 30
