from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cli"))

cli_main_module = importlib.import_module("orca_cli.main")
from orca_cli.main import _run_admin, build_parser


class _FakeIdentity:
    def __init__(self, upi: str, role: str, dn: str) -> None:
        self.upi = upi
        self.role = role
        self.dn = dn
        self.component_type = "service"
        self.description = "ORCA gateway"
        self.registered_at = "2026-05-30T00:00:00+00:00"


class _FakeDirectory:
    def __init__(self) -> None:
        self.identity = _FakeIdentity(
            "orca:service:550e8400-e29b-41d4-a716-446655440000",
            "orca.service",
            "uid=orca:service:550e8400-e29b-41d4-a716-446655440000,ou=services,dc=orca,dc=internal",
        )

    def lookup_identity(self, upi: str):
        if upi != self.identity.upi:
            return None
        return self.identity

    def get_role_permissions(self, role: str) -> set[str]:
        if role == "orca.admin":
            return {"telemetry.write", "service.stop", "service.health"}
        return {"service.health", "process.write"}

    def verify_role_assignment(self, upi: str, *, expected_role: str | None = None, permission: str | None = None) -> bool:
        if upi != self.identity.upi:
            return False
        if expected_role is not None and self.identity.role != expected_role:
            return False
        if permission is not None and permission not in self.get_role_permissions(self.identity.role):
            return False
        return True

    def update_role_assignment(self, upi: str, role: str):
        if upi != self.identity.upi:
            raise ValueError("identity not found")
        self.identity.role = role
        return self.identity

    def register(self, *, upi: str, description: str, role: str):
        self.identity = _FakeIdentity(
            upi,
            role,
            f"uid={upi},ou=services,dc=orca,dc=internal",
        )
        self.identity.description = description
        return self.identity

    def ensure_role_seed(self):
        return [
            "ou=roles,dc=orca,dc=internal",
            "cn=orca.admin,ou=roles,dc=orca,dc=internal",
        ]


class _FailingDirectory:
    def __init__(self, message: str) -> None:
        self.message = message

    def lookup_identity(self, upi: str):
        _ = upi
        raise RuntimeError(self.message)


def test_admin_identity_parser_supports_verify_command() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "admin",
            "identity",
            "--bind-password",
            "secret",
            "verify",
            "orca:service:550e8400-e29b-41d4-a716-446655440000",
            "--expected-role",
            "orca.service",
            "--permission",
            "service.health",
        ]
    )

    assert args.command == "admin"
    assert args.admin_command == "identity"
    assert args.admin_identity_command == "verify"
    assert args.expected_role == "orca.service"
    assert args.permission == "service.health"


def test_admin_identity_parser_supports_list_role_permissions_command() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "admin",
            "identity",
            "--bind-password",
            "secret",
            "list-role-permissions",
            "orca.admin",
        ]
    )

    assert args.admin_identity_command == "list-role-permissions"
    assert args.role == "orca.admin"


def test_admin_identity_parser_supports_register_and_bootstrap_roles_commands() -> None:
    parser = build_parser()

    register_args = parser.parse_args(
        [
            "admin",
            "identity",
            "--bind-password",
            "secret",
            "register",
            "--component-type",
            "service",
            "--role",
            "orca.service",
            "--description",
            "ORCA gateway service",
        ]
    )
    bootstrap_args = parser.parse_args(
        [
            "admin",
            "identity",
            "--bind-password",
            "secret",
            "bootstrap-roles",
        ]
    )

    assert register_args.admin_identity_command == "register"
    assert register_args.component_type == "service"
    assert bootstrap_args.admin_identity_command == "bootstrap-roles"


def test_run_admin_identity_inspect_returns_live_permissions(monkeypatch: pytest.MonkeyPatch) -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "admin",
            "identity",
            "--bind-password",
            "secret",
            "inspect",
            "orca:service:550e8400-e29b-41d4-a716-446655440000",
        ]
    )
    monkeypatch.setattr(cli_main_module, "_build_ldap_identity_directory", lambda _args: _FakeDirectory())

    result = _run_admin(args)

    assert result["upi"].startswith("orca:service:")
    assert result["role"] == "orca.service"
    assert "service.health" in result["live_role_permissions"]
    assert result["ldap_verified"] is True


def test_run_admin_identity_update_role_returns_updated_assignment(monkeypatch: pytest.MonkeyPatch) -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "admin",
            "identity",
            "--bind-password",
            "secret",
            "update-role",
            "orca:service:550e8400-e29b-41d4-a716-446655440000",
            "orca.admin",
        ]
    )
    monkeypatch.setattr(cli_main_module, "_build_ldap_identity_directory", lambda _args: _FakeDirectory())

    result = _run_admin(args)

    assert result["previous_role"] == "orca.service"
    assert result["updated_role"] == "orca.admin"
    assert result["ldap_verified"] is True
    assert "telemetry.write" in result["live_role_permissions"]


def test_run_admin_identity_verify_checks_expected_role_and_permission(monkeypatch: pytest.MonkeyPatch) -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "admin",
            "identity",
            "--bind-password",
            "secret",
            "verify",
            "orca:service:550e8400-e29b-41d4-a716-446655440000",
            "--expected-role",
            "orca.service",
            "--permission",
            "service.health",
        ]
    )
    monkeypatch.setattr(cli_main_module, "_build_ldap_identity_directory", lambda _args: _FakeDirectory())

    result = _run_admin(args)

    assert result == {
        "upi": "orca:service:550e8400-e29b-41d4-a716-446655440000",
        "expected_role": "orca.service",
        "permission": "service.health",
        "current_role": "orca.service",
        "verified": True,
    }


def test_run_admin_identity_list_role_permissions_returns_live_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "admin",
            "identity",
            "--bind-password",
            "secret",
            "list-role-permissions",
            "orca.admin",
        ]
    )
    monkeypatch.setattr(cli_main_module, "_build_ldap_identity_directory", lambda _args: _FakeDirectory())

    result = _run_admin(args)

    assert result == {
        "role": "orca.admin",
        "permissions": ["service.health", "service.stop", "telemetry.write"],
        "permission_count": 3,
    }


def test_run_admin_identity_inspect_raises_for_missing_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "admin",
            "identity",
            "--bind-password",
            "secret",
            "inspect",
            "orca:service:00000000-0000-4000-8000-000000000000",
        ]
    )
    monkeypatch.setattr(cli_main_module, "_build_ldap_identity_directory", lambda _args: _FakeDirectory())

    with pytest.raises(ValueError, match="identity not found in LDAP"):
        _run_admin(args)


def test_build_ldap_identity_directory_requires_bind_password() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "admin",
            "identity",
            "inspect",
            "orca:service:550e8400-e29b-41d4-a716-446655440000",
        ]
    )

    from orca_cli.main import _build_ldap_identity_directory

    with pytest.raises(ValueError, match="LDAP admin commands require --bind-password"):
        _build_ldap_identity_directory(args)


def test_run_admin_identity_verify_returns_false_on_failed_verification(monkeypatch: pytest.MonkeyPatch) -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "admin",
            "identity",
            "--bind-password",
            "secret",
            "verify",
            "orca:service:550e8400-e29b-41d4-a716-446655440000",
            "--expected-role",
            "orca.admin",
            "--permission",
            "telemetry.write",
        ]
    )
    monkeypatch.setattr(cli_main_module, "_build_ldap_identity_directory", lambda _args: _FakeDirectory())

    result = _run_admin(args)

    assert result == {
        "upi": "orca:service:550e8400-e29b-41d4-a716-446655440000",
        "expected_role": "orca.admin",
        "permission": "telemetry.write",
        "current_role": "orca.service",
        "verified": False,
    }


def test_run_admin_identity_surfaces_bad_bind_password_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "admin",
            "identity",
            "--bind-password",
            "wrong-secret",
            "inspect",
            "orca:service:550e8400-e29b-41d4-a716-446655440000",
        ]
    )
    monkeypatch.setattr(
        cli_main_module,
        "_build_ldap_identity_directory",
        lambda _args: _FailingDirectory("invalidCredentials: bind failed"),
    )

    with pytest.raises(RuntimeError, match="invalidCredentials: bind failed"):
        _run_admin(args)


def test_run_admin_identity_register_creates_identity_and_verifies_assignment(monkeypatch: pytest.MonkeyPatch) -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "admin",
            "identity",
            "--bind-password",
            "secret",
            "register",
            "--component-type",
            "service",
            "--role",
            "orca.service",
            "--description",
            "ORCA gateway service",
            "--upi",
            "orca:service:550e8400-e29b-41d4-a716-446655440000",
        ]
    )
    monkeypatch.setattr(cli_main_module, "_build_ldap_identity_directory", lambda _args: _FakeDirectory())

    result = _run_admin(args)

    assert result["upi"] == "orca:service:550e8400-e29b-41d4-a716-446655440000"
    assert result["role"] == "orca.service"
    assert result["ldap_verified"] is True


def test_run_admin_identity_bootstrap_roles_reports_seeded_dns(monkeypatch: pytest.MonkeyPatch) -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "admin",
            "identity",
            "--bind-password",
            "secret",
            "bootstrap-roles",
        ]
    )
    monkeypatch.setattr(cli_main_module, "_build_ldap_identity_directory", lambda _args: _FakeDirectory())

    result = _run_admin(args)

    assert result == {
        "ldap_base_dn": "dc=orca,dc=internal",
        "created_dns": [
            "ou=roles,dc=orca,dc=internal",
            "cn=orca.admin,ou=roles,dc=orca,dc=internal",
        ],
        "seeded_roles": True,
    }