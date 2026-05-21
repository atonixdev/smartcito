"""
================================================================================
 File: scripts/ci/validate_repo_structure.py
 Purpose:
   Enforce SmartCito's hardware CI repository standards for documentation,
   manifests, and test coverage.
================================================================================
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIRED_DIRS = [
    ROOT / "hardware" / "compute",
    ROOT / "hardware" / "storage",
    ROOT / "hardware" / "networking",
    ROOT / "hardware" / "security",
    ROOT / "hardware" / "racks",
]


def main() -> int:
    missing: list[str] = []
    for folder in REQUIRED_DIRS:
        requirements = [
            folder / "README.md",
            folder / "ci_manifest.yaml",
        ]
        test_files = list(folder.glob("test_*.py"))
        for required in requirements:
            if not required.exists():
                missing.append(str(required.relative_to(ROOT)))
        if not test_files:
            missing.append(f"{folder.relative_to(ROOT)}/test_*.py")

    if missing:
        raise SystemExit("Missing required hardware CI assets:\n- " + "\n- ".join(missing))

    print("Hardware repository structure validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
