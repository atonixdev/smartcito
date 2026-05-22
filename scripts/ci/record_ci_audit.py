"""
================================================================================
 File: scripts/ci/record_ci_audit.py
 Purpose:
   Append CI traceability metadata to logs/ci_audit.json, including Git
   metadata, contributor identity verification, and hardware artifact links.
================================================================================
"""

from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
AUDIT_LOG = ROOT / "logs" / "ci_audit.json"
HARDWARE_RESULTS = ROOT / "logs" / "hardware_results"


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _verify_actor(actor: str) -> dict[str, Any]:
    token = os.getenv("GITHUB_TOKEN")
    if not actor or not token:
        return {"verified": False, "reason": "missing actor or token"}

    request = Request(
        f"https://api.github.com/users/{actor}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # pragma: no cover - network dependent in CI
        return {"verified": False, "reason": str(exc)}

    return {
        "verified": payload.get("login") == actor,
        "id": payload.get("id"),
        "type": payload.get("type"),
        "profile": payload.get("html_url"),
    }


def _collect_hardware_artifacts() -> list[str]:
    if not HARDWARE_RESULTS.exists():
        return []
    return sorted(str(path.relative_to(ROOT)) for path in HARDWARE_RESULTS.glob("*.json"))


def main() -> int:
    stage = sys.argv[1] if len(sys.argv) > 1 else "ci"
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    if AUDIT_LOG.exists() and AUDIT_LOG.read_text().strip():
        entries = json.loads(AUDIT_LOG.read_text())
    else:
        entries = []

    actor = os.getenv("GITHUB_ACTOR", _git("log", "-1", "--pretty=%an"))
    entry = {
        "stage": stage,
        "timestamp": datetime.now(UTC).isoformat(),
        "author": _git("log", "-1", "--pretty=%an"),
        "branch": os.getenv("GITHUB_REF_NAME", _git("rev-parse", "--abbrev-ref", "HEAD")),
        "commit": os.getenv("GITHUB_SHA", _git("rev-parse", "HEAD")),
        "actor": actor,
        "repository": os.getenv("GITHUB_REPOSITORY", "local/smartcito"),
        "run_id": os.getenv("GITHUB_RUN_ID", "local-run"),
        "identity": _verify_actor(actor),
        "hardware_artifacts": _collect_hardware_artifacts(),
    }
    entries.append(entry)
    AUDIT_LOG.write_text(json.dumps(entries, indent=2))
    print(json.dumps(entry, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
