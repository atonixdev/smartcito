from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WRAPPER = ROOT / "scripts" / "ai.sh"
DIST_DIR = ROOT / "dist" / "smartcito_ai_kaggle"
OUTPUT_DIR = ROOT / "output" / "smartcito-lora"


def _run(command: list[str], *, extra_env: dict[str, str] | None = None) -> None:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def main() -> int:
    shutil.rmtree(DIST_DIR, ignore_errors=True)
    shutil.rmtree(OUTPUT_DIR, ignore_errors=True)

    _run(["chmod", "+x", str(WRAPPER)])
    _run([str(WRAPPER), "help"])
    _run([str(WRAPPER), "package"])
    _run(
        [str(WRAPPER), "evaluate"],
        extra_env={"PREDICTIONS_FILE": "datasets/sample_predictions.json"},
    )

    manifest = DIST_DIR / "kaggle_bundle_manifest.json"
    summary = OUTPUT_DIR / "evaluation_summary.json"
    report = OUTPUT_DIR / "evaluation_report.md"

    missing = [str(path.relative_to(ROOT)) for path in (manifest, summary, report) if not path.exists()]
    if missing:
        raise SystemExit(f"AI offline validation missing outputs: {', '.join(missing)}")

    print("smartcito ai offline validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())