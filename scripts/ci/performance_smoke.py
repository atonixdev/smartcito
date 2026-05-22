"""
================================================================================
 File: scripts/ci/performance_smoke.py
 Purpose:
   Lightweight performance smoke check for SmartCito hardware CI. Uses measured
   or simulated metrics to gate obvious regressions in compute throughput.
================================================================================
"""

from __future__ import annotations

import json
from pathlib import Path
import time

OUTPUT = Path("logs/performance_smoke.json")


def main() -> int:
    start = time.perf_counter()
    samples = [index * index for index in range(40000)]
    checksum = sum(samples)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    payload = {
        "elapsed_ms": elapsed_ms,
        "checksum": checksum,
        "status": "pass" if elapsed_ms < 250 else "warn",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))
    if payload["status"] != "pass":
        raise SystemExit("Performance smoke threshold exceeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
