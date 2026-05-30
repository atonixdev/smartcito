"""
================================================================================
 File: orcaapi/tests/test_identity_admin_api.py
 Purpose:
   Focused regression coverage for identity admin endpoints used by desktop UI.
================================================================================
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.api.v1.endpoints.identity_admin import _get_ldap_admin_directory


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


client = TestClient(app)


def test_identity_admin_inspect_and_role_permissions(monkeypatch) -> None:
    _ = monkeypatch
    directory = _FakeDirectory()
    app.dependency_overrides[_get_ldap_admin_directory] = lambda: directory

    try:
        inspect_response = client.get("/api/v1/identity/admin/orca:service:550e8400-e29b-41d4-a716-446655440000")
        role_response = client.get("/api/v1/identity/admin/roles/orca.service")

        assert inspect_response.status_code == 200
        assert inspect_response.json()["upi"].startswith("orca:service:")
        assert role_response.status_code == 200
        assert "service.health" in role_response.json()["permissions"]
    finally:
        app.dependency_overrides.clear()


def test_identity_admin_register_update_verify_and_bootstrap(monkeypatch) -> None:
    _ = monkeypatch
    directory = _FakeDirectory()
    app.dependency_overrides[_get_ldap_admin_directory] = lambda: directory

    try:
        register_response = client.post(
            "/api/v1/identity/admin/register",
            json={
                "upi": "orca:service:550e8400-e29b-41d4-a716-446655440000",
                "component_type": "service",
                "role": "orca.service",
                "description": "ORCA gateway service",
            },
        )
        update_response = client.post(
            "/api/v1/identity/admin/orca:service:550e8400-e29b-41d4-a716-446655440000/role",
            json={"role": "orca.admin"},
        )
        verify_response = client.post(
            "/api/v1/identity/admin/orca:service:550e8400-e29b-41d4-a716-446655440000/verify",
            json={"expected_role": "orca.admin", "permission": "telemetry.write"},
        )
        bootstrap_response = client.post("/api/v1/identity/admin/bootstrap-roles")

        assert register_response.status_code == 201
        assert update_response.status_code == 200
        assert verify_response.status_code == 200
        assert verify_response.json()["verified"] is True
        assert bootstrap_response.status_code == 200
        assert bootstrap_response.json()["seeded_roles"] is True
    finally:
        app.dependency_overrides.clear()