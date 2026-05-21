"""
================================================================================
 File: hardware/security/test_hsm_integrity.py
 Purpose:
   CI smoke tests for HSM integrity, tamper state, and PQC readiness.
================================================================================
"""

from __future__ import annotations

from hardware.test_support import HardwareSnapshot, assert_snapshot, collect_snapshot


def test_hsm_integrity() -> None:
    snapshot = collect_snapshot(
        component="security-hsm",
        endpoint_env="SMARTCITO_HSM_ENDPOINT",
        defaults=HardwareSnapshot(
            component="security-hsm",
            endpoint="simulation://security",
            firmware_version="5.1.0",
            temperature_c=28.0,
            power_kw=0.8,
            throughput_mbps=5000,
            reachable=True,
            quantum_ready=True,
            metadata={"tamper_state": "sealed", "slot_count": 4},
        ),
    )
    assert_snapshot(
        snapshot,
        minimum_firmware="5.0.0",
        maximum_temperature_c=40.0,
        minimum_throughput_mbps=1000,
        minimum_power_kw=0.5,
        require_quantum_ready=True,
    )
    assert snapshot.metadata["tamper_state"] == "sealed"
    assert snapshot.metadata["slot_count"] >= 2
