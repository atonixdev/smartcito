from __future__ import annotations

import argparse
import importlib.resources as importlib_resources
import json
import os
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
SDK_PYTHON_DIR = REPO_ROOT / "sdk" / "python"
if str(SDK_PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(SDK_PYTHON_DIR))

from orca_sdk import OrcaClient
from orca_shared.identity import LDAPIdentityDirectory, generate_upi, identity_posture


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Orca runtime manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Run the Orca DataStream ingestion service")
    ingest_parser.add_argument("--config", default="ingestion/config/datastream_sources.json")
    ingest_parser.add_argument("--output-dir", default="ai/orca_datasets")
    ingest_parser.add_argument("--limit", type=int, default=None)

    train_parser = subparsers.add_parser("train", help="Train a versioned Orca model from batch datasets")
    train_parser.add_argument("--batch-dir", default="ai/orca_datasets")
    train_parser.add_argument("--models-dir", default="ai/models")
    train_parser.add_argument("--version", default=None)
    train_parser.add_argument("--no-activate", action="store_true")

    deploy_parser = subparsers.add_parser("deploy", help="Deploy a specific Orca model version")
    deploy_parser.add_argument("--version", required=True)
    deploy_parser.add_argument("--models-dir", default="ai/models")

    dataset_parser = subparsers.add_parser("dataset", help="Dataset utilities")
    dataset_subparsers = dataset_parser.add_subparsers(dest="dataset_command", required=True)
    dataset_ingest_parser = dataset_subparsers.add_parser("ingest", help="Ingest external source data into ai/datasets")
    dataset_ingest_parser.add_argument("--source", choices=("space-weather", "satellite", "gps", "map"), required=True)
    dataset_ingest_parser.add_argument("--output-dir", default="ai/datasets")
    dataset_ingest_parser.add_argument("--input-file", default=None)
    dataset_ingest_parser.add_argument("--api-url", default=None)
    dataset_ingest_parser.add_argument("--region", default="global")
    dataset_ingest_parser.add_argument("--bbox", default="-26.25,27.98,-26.15,28.08")
    dataset_ingest_parser.add_argument("--k-index-url", default=None)
    dataset_ingest_parser.add_argument("--xray-url", default=None)
    dataset_ingest_parser.add_argument("--k-index-input-file", default=None)
    dataset_ingest_parser.add_argument("--xray-input-file", default=None)

    dataset_train_parser = dataset_subparsers.add_parser("train", help="Train a Orca runtime model from JSON datasets")
    dataset_train_parser.add_argument("--dataset-dir", default="ai/datasets")
    dataset_train_parser.add_argument("--models-dir", default="ai/models")
    dataset_train_parser.add_argument("--version", default=None)
    dataset_train_parser.add_argument("--no-activate", action="store_true")

    export_parser = dataset_subparsers.add_parser("export", help="Export sanitized Orca training data")
    export_parser.add_argument("--batch-dir", default="ai/orca_datasets")
    export_parser.add_argument("--output-path", required=True)
    export_parser.add_argument("--include-metadata", action="store_true")

    api_parser = subparsers.add_parser("api", help="Call supported Orca API surfaces through the bundled SDK")
    api_parser.add_argument("--base-url", default="http://localhost:8000")
    api_parser.add_argument("--token", default=None)
    api_subparsers = api_parser.add_subparsers(dest="api_command", required=True)

    health_parser = api_subparsers.add_parser("health", help="Query API health endpoints")
    health_parser.add_argument("endpoint", choices=("live", "ready", "status", "identity"), default="status", nargs="?")

    control_parser = api_subparsers.add_parser("control-plane", help="Query dashboard control-plane endpoints")
    control_parser.add_argument(
        "endpoint",
        choices=("overview", "map", "scene", "register-map-device", "update-control"),
    )
    control_parser.add_argument("--payload-file", default=None)
    control_parser.add_argument("--control-id", default=None)
    control_parser.add_argument("--desired-state", default=None)

    fleet_parser = api_subparsers.add_parser("fleet", help="Query GPS fleet endpoints")
    fleet_subparsers = fleet_parser.add_subparsers(dest="fleet_command", required=True)
    fleet_live_parser = fleet_subparsers.add_parser("live", help="Get the active live fleet")
    fleet_live_parser.add_argument("--active-within-minutes", type=int, default=15)
    fleet_last_parser = fleet_subparsers.add_parser("last-position", help="Get the last position for one device")
    fleet_last_parser.add_argument("device_id")
    fleet_ingest_parser = fleet_subparsers.add_parser("ingest", help="Send a GPS point to the write API")
    fleet_ingest_parser.add_argument("--payload-file", required=True)
    fleet_gateway_parser = fleet_subparsers.add_parser(
        "gateway-ingest",
        help="Send a GPS gateway payload to the write API",
    )
    fleet_gateway_parser.add_argument("--payload-file", required=True)

    camera_parser = api_subparsers.add_parser("cameras", help="Query camera registry endpoints")
    camera_parser.add_argument("endpoint", choices=("list", "register", "telemetry"))
    camera_parser.add_argument("--payload-file", default=None)
    camera_parser.add_argument("--device-id", default=None)

    admin_parser = subparsers.add_parser("admin", help="Administrative identity and directory operations")
    admin_subparsers = admin_parser.add_subparsers(dest="admin_command", required=True)

    identity_admin_parser = admin_subparsers.add_parser("identity", help="Inspect or update ORCA LDAP identity assignments")
    identity_admin_parser.add_argument(
        "--server",
        default=os.getenv("ORCA_LDAP_SERVER", "ldap://localhost:389"),
        help="LDAP server URI",
    )
    identity_admin_parser.add_argument(
        "--bind-dn",
        default=os.getenv("ORCA_LDAP_BIND_DN", "cn=admin,dc=orca,dc=internal"),
        help="LDAP bind DN",
    )
    identity_admin_parser.add_argument(
        "--bind-password",
        default=os.getenv("ORCA_LDAP_BIND_PASSWORD"),
        help="LDAP bind password",
    )
    identity_admin_parser.add_argument(
        "--base-dn",
        default=os.getenv("ORCA_LDAP_BASE_DN", "dc=orca,dc=internal"),
        help="LDAP base DN",
    )
    identity_admin_subparsers = identity_admin_parser.add_subparsers(
        dest="admin_identity_command",
        required=True,
    )

    identity_inspect_parser = identity_admin_subparsers.add_parser(
        "inspect",
        help="Inspect one ORCA identity and its live role permissions",
    )
    identity_inspect_parser.add_argument("upi")

    identity_update_role_parser = identity_admin_subparsers.add_parser(
        "update-role",
        help="Update the ORCA LDAP role assignment for one identity",
    )
    identity_update_role_parser.add_argument("upi")
    identity_update_role_parser.add_argument("role")

    identity_verify_parser = identity_admin_subparsers.add_parser(
        "verify",
        help="Verify one ORCA LDAP identity against an expected role and optional permission",
    )
    identity_verify_parser.add_argument("upi")
    identity_verify_parser.add_argument("--expected-role", default=None)
    identity_verify_parser.add_argument("--permission", default=None)

    identity_role_permissions_parser = identity_admin_subparsers.add_parser(
        "list-role-permissions",
        help="List the live LDAP permissions assigned to one ORCA role",
    )
    identity_role_permissions_parser.add_argument("role")

    identity_register_parser = identity_admin_subparsers.add_parser(
        "register",
        help="Create a new ORCA UPI and register the LDAP entry",
    )
    identity_register_parser.add_argument("--component-type", required=True)
    identity_register_parser.add_argument("--role", required=True)
    identity_register_parser.add_argument("--description", required=True)
    identity_register_parser.add_argument("--upi", default=None)

    identity_bootstrap_roles_parser = identity_admin_subparsers.add_parser(
        "bootstrap-roles",
        help="Seed the LDAP role entries and permission mappings",
    )

    workspace_parser = subparsers.add_parser("workspace", help="Inspect the top-level domain grouping layer")
    workspace_subparsers = workspace_parser.add_subparsers(dest="workspace_command", required=True)
    workspace_subparsers.add_parser("domains", help="List grouped domain manifests for the repository")
    workspace_subparsers.add_parser("templates", help="List bundled JSON payload templates for write commands")
    workspace_template_parser = workspace_subparsers.add_parser(
        "template",
        help="Print one bundled JSON payload template",
    )
    workspace_template_parser.add_argument("name")
    workspace_template_write_parser = workspace_subparsers.add_parser(
        "template-write",
        help="Write one bundled JSON payload template to a file",
    )
    workspace_template_write_parser.add_argument("name")
    workspace_template_write_parser.add_argument("--output", required=True)
    workspace_template_write_all_parser = workspace_subparsers.add_parser(
        "template-write-all",
        help="Write all bundled JSON payload templates to a directory",
    )
    workspace_template_write_all_parser.add_argument("--output-dir", required=True)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "ingest":
        result = _run_ingest(args)
    elif args.command == "train":
        result = _run_train(args)
    elif args.command == "deploy":
        result = _run_deploy(args)
    elif args.command == "dataset" and args.dataset_command == "ingest":
        result = _run_dataset_ingest(args)
    elif args.command == "dataset" and args.dataset_command == "train":
        result = _run_dataset_train(args)
    elif args.command == "dataset" and args.dataset_command == "export":
        result = _run_dataset_export(args)
    elif args.command == "api":
        result = _run_api(args)
    elif args.command == "admin":
        result = _run_admin(args)
    elif args.command == "workspace" and args.workspace_command == "domains":
        result = _load_domain_manifests()
    elif args.command == "workspace" and args.workspace_command == "templates":
        result = _load_payload_templates_index()
    elif args.command == "workspace" and args.workspace_command == "template":
        result = _load_payload_template(args.name)
    elif args.command == "workspace" and args.workspace_command == "template-write":
        result = _write_payload_template(args.name, args.output)
    elif args.command == "workspace" and args.workspace_command == "template-write-all":
        result = _write_all_payload_templates(args.output_dir)
    else:
        parser.print_help()
        return 1

    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def _build_sdk_client(args: argparse.Namespace) -> OrcaClient:
    return OrcaClient(base_url=args.base_url, token=args.token)


def _build_ldap_identity_directory(args: argparse.Namespace) -> LDAPIdentityDirectory:
    if not args.bind_password:
        raise ValueError("LDAP admin commands require --bind-password or ORCA_LDAP_BIND_PASSWORD")
    return LDAPIdentityDirectory(
        server_uri=args.server,
        bind_dn=args.bind_dn,
        bind_password=args.bind_password,
        ldap_base_dn=args.base_dn,
    )


def _run_admin(args: argparse.Namespace) -> Any:
    if args.admin_command != "identity":
        raise ValueError("unsupported admin command")

    directory = _build_ldap_identity_directory(args)
    if args.admin_identity_command == "inspect":
        identity = directory.lookup_identity(args.upi)
        if identity is None:
            raise ValueError(f"identity not found in LDAP: {args.upi}")
        posture = identity_posture(identity)
        posture["live_role_permissions"] = sorted(directory.get_role_permissions(identity.role))
        posture["ldap_verified"] = directory.verify_role_assignment(
            args.upi,
            expected_role=identity.role,
        )
        return posture

    if args.admin_identity_command == "update-role":
        previous_identity = directory.lookup_identity(args.upi)
        previous_role = previous_identity.role if previous_identity is not None else None
        updated_identity = directory.update_role_assignment(args.upi, args.role)
        return {
            "upi": updated_identity.upi,
            "previous_role": previous_role,
            "updated_role": updated_identity.role,
            "ldap_dn": updated_identity.dn,
            "live_role_permissions": sorted(directory.get_role_permissions(updated_identity.role)),
            "ldap_verified": directory.verify_role_assignment(
                args.upi,
                expected_role=updated_identity.role,
            ),
        }

    if args.admin_identity_command == "verify":
        verified = directory.verify_role_assignment(
            args.upi,
            expected_role=args.expected_role,
            permission=args.permission,
        )
        identity = directory.lookup_identity(args.upi)
        current_role = identity.role if identity is not None else None
        return {
            "upi": args.upi,
            "expected_role": args.expected_role,
            "permission": args.permission,
            "current_role": current_role,
            "verified": verified,
        }

    if args.admin_identity_command == "list-role-permissions":
        permissions = sorted(directory.get_role_permissions(args.role))
        return {
            "role": args.role,
            "permissions": permissions,
            "permission_count": len(permissions),
        }

    if args.admin_identity_command == "register":
        identity = directory.register(
            upi=args.upi or generate_upi(args.component_type),
            description=args.description,
            role=args.role,
        )
        posture = identity_posture(identity)
        posture["live_role_permissions"] = sorted(directory.get_role_permissions(identity.role))
        posture["ldap_verified"] = directory.verify_role_assignment(
            identity.upi,
            expected_role=identity.role,
        )
        return posture

    if args.admin_identity_command == "bootstrap-roles":
        created_dns = directory.ensure_role_seed()
        return {
            "ldap_base_dn": args.base_dn,
            "created_dns": created_dns,
            "seeded_roles": True,
        }

    raise ValueError("unsupported admin identity command")


def _run_api(args: argparse.Namespace) -> Any:
    client = _build_sdk_client(args)
    if args.api_command == "health":
        if args.endpoint == "live":
            return client.health_live()
        if args.endpoint == "ready":
            return client.health_ready()
        if args.endpoint == "identity":
            return client.health_identity()
        return client.health_status()
    if args.api_command == "control-plane":
        if args.endpoint == "overview":
            return client.control_plane_overview()
        if args.endpoint == "map":
            return client.map_overview()
        if args.endpoint == "scene":
            return client.scene_overview()
        if args.endpoint == "register-map-device":
            return client.register_map_device(_load_json_payload(args.payload_file))
        if args.endpoint == "update-control":
            if args.payload_file is not None:
                payload = _load_json_payload(args.payload_file)
                control_id = args.control_id or payload.get("control_id")
                desired_state = args.desired_state or payload.get("desired_state")
            else:
                control_id = args.control_id
                desired_state = args.desired_state
            if control_id is None or desired_state is None:
                raise ValueError("update-control requires --control-id and --desired-state, or a payload file with those keys")
            return client.update_operator_control(control_id, desired_state)
        raise ValueError("unsupported control-plane endpoint")
    if args.api_command == "fleet" and args.fleet_command == "live":
        return client.live_fleet(active_within_minutes=args.active_within_minutes)
    if args.api_command == "fleet" and args.fleet_command == "last-position":
        return client.get_last_position(args.device_id)
    if args.api_command == "fleet" and args.fleet_command == "ingest":
        return client.ingest_gps_point(_load_json_payload(args.payload_file))
    if args.api_command == "fleet" and args.fleet_command == "gateway-ingest":
        return client.ingest_gps_gateway_payload(_load_json_payload(args.payload_file))
    if args.api_command == "cameras" and args.endpoint == "list":
        return client.list_cameras()
    if args.api_command == "cameras" and args.endpoint == "register":
        return client.register_camera(_load_json_payload(args.payload_file))
    if args.api_command == "cameras" and args.endpoint == "telemetry":
        if args.device_id is None:
            raise ValueError("camera telemetry requires --device-id")
        return client.update_camera_telemetry(args.device_id, _load_json_payload(args.payload_file))
    raise ValueError("unsupported api command")


def _load_json_payload(payload_file: str | None) -> dict[str, Any]:
    if payload_file is None:
        raise ValueError("this command requires --payload-file")
    return json.loads(Path(payload_file).read_text(encoding="utf-8"))


def _load_domain_manifests() -> dict[str, list[dict[str, Any]]]:
    manifests: list[dict[str, Any]] = []
    repo_manifests = sorted((REPO_ROOT / "domains").glob("*/manifest.json"))
    if repo_manifests:
        for manifest_path in repo_manifests:
            manifests.append(json.loads(manifest_path.read_text(encoding="utf-8")))
    else:
        resource_root = importlib_resources.files("orca_cli") / "domain_manifests"
        for manifest_resource in sorted(resource_root.iterdir(), key=lambda item: item.name):
            if manifest_resource.name.endswith(".json"):
                manifests.append(json.loads(manifest_resource.read_text(encoding="utf-8")))
    return {"domains": manifests}


def _load_payload_templates_index() -> dict[str, list[dict[str, Any]]]:
    template_index = _read_package_json("templates/index.json")
    return {"templates": template_index["templates"]}


def _load_payload_template(name: str) -> dict[str, Any]:
    template_index = _read_package_json("templates/index.json")
    for template in template_index["templates"]:
        if template["name"] == name:
            payload = _read_package_json(f"templates/{template['file']}")
            return {
                "name": template["name"],
                "description": template["description"],
                "payload": payload,
            }
    raise ValueError(f"unknown template {name!r}")


def _write_payload_template(name: str, output_path: str) -> dict[str, Any]:
    template = _load_payload_template(name)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(template["payload"], indent=2) + "\n", encoding="utf-8")
    return {
        "name": template["name"],
        "description": template["description"],
        "output": str(destination),
    }


def _write_all_payload_templates(output_dir: str) -> dict[str, Any]:
    template_index = _load_payload_templates_index()
    destination_dir = Path(output_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)
    written: list[dict[str, str]] = []
    for template in template_index["templates"]:
        destination = destination_dir / template["file"]
        _write_payload_template(template["name"], str(destination))
        written.append({"name": template["name"], "output": str(destination)})
    return {"output_dir": str(destination_dir), "templates": written}


def _read_package_json(relative_path: str) -> dict[str, Any]:
    resource = importlib_resources.files(__package__ or "orca_cli") / relative_path
    return json.loads(resource.read_text(encoding="utf-8"))


def _run_ingest(args: argparse.Namespace) -> Any:
    from ingestion.datastream import run_datastream

    return run_datastream(config_path=args.config, output_dir=args.output_dir, limit=args.limit)


def _run_train(args: argparse.Namespace) -> Any:
    from ai.training.orca_model_pipeline import train_from_batches

    return train_from_batches(
        batch_dir=args.batch_dir,
        models_dir=args.models_dir,
        version=args.version,
        activate=not args.no_activate,
    )


def _run_deploy(args: argparse.Namespace) -> Any:
    from ai.training.orca_model_pipeline import deploy_model

    return deploy_model(version=args.version, models_dir=args.models_dir)


def _run_dataset_ingest(args: argparse.Namespace) -> Any:
    if args.source == "space-weather":
        from ai.ingestion.space_weather_ingestor import ingest_space_weather

        return ingest_space_weather(
            region=args.region,
            k_index_url=args.k_index_url or "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json",
            xray_url=args.xray_url or "https://services.swpc.noaa.gov/json/goes/primary/xrays-1-day.json",
            k_index_input_file=args.k_index_input_file,
            xray_input_file=args.xray_input_file,
            output_dir=args.output_dir,
        )
    if args.source == "satellite":
        from ai.ingestion.satellite_ingestor import ingest_satellite

        return ingest_satellite(
            api_url=args.api_url or "https://eonet.gsfc.nasa.gov/api/v3/events?limit=20&status=open",
            input_file=args.input_file,
            region=args.region,
            output_dir=args.output_dir,
        )
    if args.source == "gps":
        from ai.ingestion.gps_ingestor import ingest_gps

        return ingest_gps(api_url=args.api_url, input_file=args.input_file, output_dir=args.output_dir)

    from ai.ingestion.map_ingestor import ingest_map

    return ingest_map(
        api_url=args.api_url or "https://overpass-api.de/api/interpreter",
        input_file=args.input_file,
        bbox=args.bbox,
        output_dir=args.output_dir,
    )


def _run_dataset_train(args: argparse.Namespace) -> Any:
    from ai.training.train import train_from_dataset_dir

    return train_from_dataset_dir(
        dataset_dir=args.dataset_dir,
        models_dir=args.models_dir,
        version=args.version,
        activate=not args.no_activate,
    )


def _run_dataset_export(args: argparse.Namespace) -> Any:
    from ai.training.orca_model_pipeline import export_dataset

    return export_dataset(
        batch_dir=args.batch_dir,
        output_path=args.output_path,
        include_metadata=args.include_metadata,
    )