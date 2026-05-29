#!/usr/bin/env python3
"""Unified workflow runner for SmartCito/Orca.

This script provides one place to run the project workflow end-to-end:
- preflight checks
- focused integration tests
- local multi-service startup (without Docker)
- Docker Compose startup
- HTTP health and readiness smoke checks
"""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

ROOT_DIR = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ServiceSpec:
    name: str
    app: str
    port: int
    health_path: str


LOCAL_SERVICES: tuple[ServiceSpec, ...] = (
    ServiceSpec("ai-service", "ai_models.inference:app", 8012, "/health"),
    ServiceSpec("gpuops-service", "gpuops.service:app", 8015, "/health"),
    ServiceSpec("robot-service", "robot.service:app", 8016, "/health"),
    ServiceSpec("drone-gateway", "surveillance.drone_gateway_service:app", 8020, "/ready"),
    ServiceSpec("sensor-gateway", "surveillance.sensor_gateway_service:app", 8021, "/ready"),
    ServiceSpec("drone-camera-ingestion", "surveillance.drone_camera_service:app", 8022, "/ready"),
    ServiceSpec("threat-detection", "surveillance.threat_detection_service:app", 8023, "/ready"),
    ServiceSpec("mapping-geospatial", "surveillance.mapping_service:app", 8024, "/ready"),
    ServiceSpec("mission-control", "surveillance.mission_control_service:app", 8025, "/ready"),
)

FOCUSED_TESTS: tuple[str, ...] = (
    "tests/test_surveillance_automation_integration.py",
    "tests/test_surveillance_pipeline_execution.py",
    "ai_models/tests/test_inference.py",
    "tests/robot/test_robot_ai_model.py",
)

LOCAL_RUNTIME_DEPENDENCIES: tuple[tuple[str, str], ...] = (
    ("shapely", "shapely"),
    ("pyproj", "pyproj"),
    ("networkx", "networkx"),
)


class WorkflowError(RuntimeError):
    pass


def _log(message: str) -> None:
    print(f"[workflow] {message}")


def _run_command(command: list[str], *, env: dict[str, str] | None = None, cwd: Path = ROOT_DIR) -> None:
    _log(f"Running: {' '.join(command)}")
    result = subprocess.run(command, cwd=str(cwd), env=env, check=False)
    if result.returncode != 0:
        raise WorkflowError(f"Command failed with exit code {result.returncode}: {' '.join(command)}")


def _probe(url: str, timeout_seconds: float = 2.0) -> bool:
    try:
        with urlopen(url, timeout=timeout_seconds) as response:  # nosec B310 - local development URL checks only
            return 200 <= int(response.status) < 500
    except (URLError, TimeoutError, ValueError):
        return False


def _wait_for_url(url: str, *, timeout_seconds: int = 90) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if _probe(url):
            return
        time.sleep(1)
    raise WorkflowError(f"Timed out waiting for service URL: {url}")


def _ensure_env_file() -> None:
    env_file = ROOT_DIR / ".env"
    env_example = ROOT_DIR / ".env.example"
    if env_file.exists():
        return
    if env_example.exists():
        shutil.copy2(env_example, env_file)
        _log("Created .env from .env.example")
        return
    _log(".env not found and .env.example is missing; continuing without auto-generated env file")


def run_preflight() -> None:
    _log("Starting preflight checks")

    if sys.version_info < (3, 11):
        raise WorkflowError("Python 3.11 or newer is required")

    required_paths = (
        ROOT_DIR / "docker-compose.yml",
        ROOT_DIR / "docker-compose.services.yml",
        ROOT_DIR / "ai_models" / "inference.py",
        ROOT_DIR / "surveillance" / "drone_gateway_service.py",
        ROOT_DIR / "gpuops" / "service.py",
        ROOT_DIR / "robot" / "service.py",
    )
    for path in required_paths:
        if not path.exists():
            raise WorkflowError(f"Missing required project file: {path}")

    _ensure_env_file()

    _log("Preflight checks passed")


def _python_for_tests() -> str:
    venv_python = ROOT_DIR / "ai_models" / "venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def _python_for_runtime() -> str:
    return _python_for_tests()


def _assert_runtime_has_uvicorn() -> None:
    runtime_python = _python_for_runtime()
    command = [runtime_python, "-c", "import uvicorn"]
    result = subprocess.run(command, cwd=str(ROOT_DIR), check=False)
    if result.returncode != 0:
        raise WorkflowError(
            "Runtime Python is missing uvicorn. Install dependencies in ai_models/venv or set up a compatible environment."
        )


def _module_available(runtime_python: str, module_name: str) -> bool:
    result = subprocess.run(
        [runtime_python, "-c", f"import {module_name}"],
        cwd=str(ROOT_DIR),
        check=False,
    )
    return result.returncode == 0


def _ensure_local_runtime_dependencies() -> None:
    runtime_python = _python_for_runtime()
    missing = [
        package_name
        for module_name, package_name in LOCAL_RUNTIME_DEPENDENCIES
        if not _module_available(runtime_python, module_name)
    ]
    if not missing:
        return

    _log(f"Installing missing runtime dependencies: {', '.join(missing)}")
    _run_command([runtime_python, "-m", "pip", "install", *missing])


def run_tests() -> None:
    _log("Running focused workflow tests")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT_DIR)
    command = [_python_for_tests(), "-m", "pytest", *FOCUSED_TESTS, "-q"]
    _run_command(command, env=env)
    _log("Focused workflow tests passed")


def _local_service_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT_DIR)
    env.setdefault("ORCA_KAFKA_ENABLED", "0")
    env.setdefault("DRONE_REGISTRY_ENABLED", "0")
    env.setdefault("PYTHONUNBUFFERED", "1")
    return env


def _start_local_services() -> list[tuple[ServiceSpec, subprocess.Popen[str]]]:
    env = _local_service_env()
    processes: list[tuple[ServiceSpec, subprocess.Popen[str]]] = []
    runtime_python = _python_for_runtime()
    for service in LOCAL_SERVICES:
        command = [
            runtime_python,
            "-m",
            "uvicorn",
            service.app,
            "--host",
            "127.0.0.1",
            "--port",
            str(service.port),
            "--log-level",
            "warning",
        ]
        process = subprocess.Popen(command, cwd=str(ROOT_DIR), env=env)  # noqa: S603
        processes.append((service, process))
        _log(f"Started {service.name} on :{service.port}")

    return processes


def _stop_local_services(processes: list[tuple[ServiceSpec, subprocess.Popen[str]]]) -> None:
    for service, process in reversed(processes):
        if process.poll() is None:
            process.send_signal(signal.SIGTERM)
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=4)
        _log(f"Stopped {service.name}")


def run_local_stack(*, smoke_only: bool, hold_seconds: int) -> None:
    _log("Starting local workflow stack")
    _assert_runtime_has_uvicorn()
    _ensure_local_runtime_dependencies()
    processes: list[tuple[ServiceSpec, subprocess.Popen[str]]] = []
    try:
        processes = _start_local_services()

        for service, process in processes:
            if process.poll() is not None:
                raise WorkflowError(f"Service exited early: {service.name}")
            url = f"http://127.0.0.1:{service.port}{service.health_path}"
            _wait_for_url(url, timeout_seconds=90)
            _log(f"Service ready: {service.name} ({url})")

        _smoke_endpoints(local=True)

        if not smoke_only and hold_seconds > 0:
            _log(f"All local services running; holding for {hold_seconds}s")
            time.sleep(hold_seconds)
    finally:
        _stop_local_services(processes)


def _compose_base_command(compose_file: str) -> list[str]:
    docker_bin = shutil.which("docker")
    if not docker_bin:
        raise WorkflowError("Docker is not available in PATH")
    return [docker_bin, "compose", "-f", compose_file]


def run_docker_stack(*, compose_file: str, build: bool, keep_running: bool) -> None:
    compose = _compose_base_command(compose_file)
    up_command = [*compose, "up", "-d"]
    if build:
        up_command.append("--build")

    _run_command(up_command)

    try:
        _smoke_endpoints(local=False)
        _log("Docker workflow stack is healthy")
    finally:
        if not keep_running:
            _run_command([*compose, "down"])


def _smoke_endpoints(*, local: bool) -> None:
    # Local and Docker use the same host ports by convention.
    smoke_urls = (
        "http://127.0.0.1:8012/health",
        "http://127.0.0.1:8015/health",
        "http://127.0.0.1:8016/health",
        "http://127.0.0.1:8020/ready",
        "http://127.0.0.1:8021/ready",
        "http://127.0.0.1:8022/ready",
        "http://127.0.0.1:8023/ready",
        "http://127.0.0.1:8024/ready",
        "http://127.0.0.1:8025/ready",
        "http://127.0.0.1:8012/robot/model",
        "http://127.0.0.1:8016/robot/ai/model",
    )

    label = "local" if local else "docker"
    _log(f"Running {label} endpoint smoke checks")
    for url in smoke_urls:
        _wait_for_url(url, timeout_seconds=90)
        _log(f"OK {url}")


def run_full(*, mode: str, compose_file: str, build: bool, keep_running: bool) -> None:
    run_preflight()
    run_tests()
    if mode == "local":
        run_local_stack(smoke_only=True, hold_seconds=0)
    else:
        run_docker_stack(compose_file=compose_file, build=build, keep_running=keep_running)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SmartCito unified workflow runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("preflight", help="Run prerequisite checks")
    subparsers.add_parser("test", help="Run focused workflow tests")

    local_parser = subparsers.add_parser("local", help="Run local multi-service stack and smoke checks")
    local_parser.add_argument("--hold-seconds", type=int, default=0, help="Keep services running for N seconds before shutdown")
    local_parser.add_argument("--smoke-only", action="store_true", help="Start services, run smoke checks, then stop")

    docker_parser = subparsers.add_parser("docker", help="Run Docker Compose stack and smoke checks")
    docker_parser.add_argument("--compose-file", default="docker-compose.services.yml", help="Compose file path")
    docker_parser.add_argument("--build", action="store_true", help="Build images before starting")
    docker_parser.add_argument("--keep-running", action="store_true", help="Leave compose stack running after smoke checks")

    full_parser = subparsers.add_parser("full", help="Run full workflow (preflight + tests + stack + smoke)")
    full_parser.add_argument("--mode", choices=("local", "docker"), default="local", help="Execution mode")
    full_parser.add_argument("--compose-file", default="docker-compose.services.yml", help="Compose file path for docker mode")
    full_parser.add_argument("--build", action="store_true", help="Build images in docker mode")
    full_parser.add_argument("--keep-running", action="store_true", help="Leave docker stack running in docker mode")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "preflight":
            run_preflight()
        elif args.command == "test":
            run_tests()
        elif args.command == "local":
            run_local_stack(smoke_only=args.smoke_only, hold_seconds=args.hold_seconds)
        elif args.command == "docker":
            run_docker_stack(
                compose_file=args.compose_file,
                build=args.build,
                keep_running=args.keep_running,
            )
        elif args.command == "full":
            run_full(
                mode=args.mode,
                compose_file=args.compose_file,
                build=args.build,
                keep_running=args.keep_running,
            )
        else:
            parser.error("Unknown command")
    except WorkflowError as exc:
        _log(f"ERROR: {exc}")
        return 1
    except KeyboardInterrupt:
        _log("Interrupted by user")
        return 130

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
