"""
================================================================================
 File: hardware/storage/test_storage_arrays.py
 Purpose:
   CI smoke tests for storage array health, throughput, and redundancy.
================================================================================
"""

from __future__ import annotations

from hardware.test_support import HardwareSnapshot, assert_snapshot, collect_snapshot


def test_storage_arrays() -> None:
    snapshot = collect_snapshot(
        component="storage-arrays",
        endpoint_env="SMARTCITO_STORAGE_ENDPOINT",
        defaults=HardwareSnapshot(
            component="storage-arrays",
            endpoint="simulation://storage",
            firmware_version="2.3.1",
            temperature_c=38.5,
            power_kw=3.4,
            throughput_mbps=18000,
            reachable=True,
            metadata={"raid_mode": "raid10", "snapshot_immutable": True},
        ),
    )
    assert_snapshot(
        snapshot,
        minimum_firmware="2.1.0",
        maximum_temperature_c=48.0,
        minimum_throughput_mbps=12000,
        minimum_power_kw=2.5,
    )
    assert snapshot.metadata["raid_mode"] == "raid10"
    assert snapshot.metadata["snapshot_immutable"] is True
