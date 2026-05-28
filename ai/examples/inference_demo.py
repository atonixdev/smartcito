from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any


SYSTEM_PROMPT = (
    "You are Orca Model, a domain-specialized operations assistant for city safety, "
    "sensor fusion, drone missions, camera analytics, robot navigation, and geographic reasoning."
)

DEMO_TASKS: list[dict[str, str]] = [
    {
        "task": "drone_mission_planning",
        "prompt": (
            "Plan a drone response for a warehouse fire alarm. "
            "Drone bravo is 1.2 km away, wind is moving west to east, and the nearest camera mast is 400 m away."
        ),
    },
    {
        "task": "robot_navigation",
        "prompt": (
            "Summarize a robot navigation issue. LiDAR confidence is 0.48, wheel slip is 0.31, "
            "and the south corridor is blocked."
        ),
    },
    {
        "task": "city_camera_analytics",
        "prompt": (
            "Interpret a city camera event where two perimeter cameras detect motion and heat at North Gate "
            "with no matching badge scan at 23:42 local time."
        ),
    },
    {
        "task": "sensor_fusion",
        "prompt": (
            "Fuse environmental sensor alerts for a river district with high water levels, heavy rainfall, "
            "degraded pumps, and rising traffic congestion."
        ),
    },
    {
        "task": "threat_detection",
        "prompt": (
            "Assess a probable intrusion event near a restricted depot using camera motion, thermal change, "
            "and missing access-control confirmation."
        ),
    },
]


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Orca Model inference demos.")
    parser.add_argument("--mode", choices=("api", "local"), default="api")
    parser.add_argument("--api-base-url", default="http://localhost:8012")
    parser.add_argument("--backend", default="merged-local")
    parser.add_argument("--model", default=None, help="Optional base model id override.")
    parser.add_argument("--adapter-path", default=None, help="Optional LoRA adapter path override.")
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--max-tokens", type=int, default=180)
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser


async def _run_api_demo(args: argparse.Namespace) -> list[dict[str, Any]]:
    import httpx

    results: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=120.0) as client:
        for item in DEMO_TASKS:
            response = await client.post(
                f"{args.api_base_url.rstrip('/')}/generate",
                json={
                    "prompt": item["prompt"],
                    "system_prompt": SYSTEM_PROMPT,
                    "backend": args.backend,
                    "model": args.model,
                    "adapter_path": args.adapter_path,
                    "merge_lora": args.backend == "merged-local",
                    "temperature": args.temperature,
                    "max_tokens": args.max_tokens,
                },
            )
            response.raise_for_status()
            payload = response.json()
            results.append(
                {
                    "task": item["task"],
                    "mode": "api",
                    "provider": payload.get("provider"),
                    "model": payload.get("model"),
                    "response": payload.get("text"),
                }
            )
    return results


async def _run_local_demo(args: argparse.Namespace) -> list[dict[str, Any]]:
    from ai.ai_models.llama_stack import generate_text

    results: list[dict[str, Any]] = []
    for item in DEMO_TASKS:
        payload = await generate_text(
            item["prompt"],
            system_prompt=SYSTEM_PROMPT,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            backend=args.backend,
            adapter_path=args.adapter_path,
            merge_lora=args.backend == "merged-local",
        )
        results.append(
            {
                "task": item["task"],
                "mode": "local",
                "provider": payload.get("provider"),
                "model": payload.get("model"),
                "response": payload.get("text"),
            }
        )
    return results


async def main_async() -> int:
    args = build_arg_parser().parse_args()

    if args.mode == "api":
        results = await _run_api_demo(args)
    else:
        results = await _run_local_demo(args)

    output = {
        "demo": "Orca Model inference demo",
        "tasks": [item["task"] for item in DEMO_TASKS],
        "results": results,
    }
    print(json.dumps(output, indent=2 if args.pretty else None))
    return 0


def main() -> int:
    return asyncio.run(main_async())


if __name__ == "__main__":
    raise SystemExit(main())
