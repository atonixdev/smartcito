"""
================================================================================
 File: orca_shared/identity.py
 Purpose:
   Shared ORCA identity primitives for UPI generation, LDAP registration,
   RBAC role mapping, and process bootstrap.

 Notes:
   - UPI is mandatory and always follows `orca:<component-type>:<uuidv4>`.
   - LDAP registration is modeled locally and can be backed by ldap3.
   - RBAC permissions are defined centrally so services share one policy.
================================================================================
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any
from uuid import UUID, uuid4

DEFAULT_LDAP_BASE_DN = "dc=orca,dc=internal"
REQUIRED_LDAP_OUS = ("services", "devices", "agents", "processes", "roles")
UPI_PATTERN = re.compile(
    r"^orca:(?P<component_type>[a-z][a-z0-9-]*):"
    r"(?P<component_id>[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})$"
)

SUPPORTED_COMPONENT_TYPES = frozenset(
    {
        "service",
        "device",
        "agent",
        "process",
        "cli",
        "tui",
        "drone",
        "robot",
        "firmware",
        "openstack",
        "pod",
        "pipeline",
        "job",
        "os-process",
    }
)

COMPONENT_OU = {
    "service": "services",
    "openstack": "services",
    "device": "devices",
    "drone": "devices",
    "robot": "devices",
    "agent": "agents",
    "process": "processes",
    "cli": "processes",
    "tui": "processes",
    "firmware": "processes",
    "pod": "processes",
    "pipeline": "processes",
    "job": "processes",
    "os-process": "processes",
}

ROLE_ORCA_ADMIN = "orca.admin"
ROLE_ORCA_SERVICE = "orca.service"
ROLE_ORCA_DEVICE = "orca.device"
ROLE_ORCA_AGENT = "orca.agent"
ROLE_ORCA_OPERATOR = "orca.operator"
ROLE_ORCA_VIEWER = "orca.viewer"

DEFAULT_ROLE_PERMISSIONS: dict[str, set[str]] = {
    ROLE_ORCA_ADMIN: {
        "process.read",
        "process.write",
        "device.register",
        "device.update",
        "service.start",
        "service.stop",
        "service.health",
        "telemetry.read",
        "telemetry.write",
    },
    ROLE_ORCA_SERVICE: {
        "process.read",
        "process.write",
        "service.start",
        "service.stop",
        "service.health",
        "telemetry.read",
        "telemetry.write",
    },
    ROLE_ORCA_DEVICE: {
        "device.register",
        "device.update",
        "telemetry.read",
        "telemetry.write",
    },
    ROLE_ORCA_AGENT: {
        "process.read",
        "process.write",
        "device.update",
        "service.health",
        "telemetry.read",
        "telemetry.write",
    },
    ROLE_ORCA_OPERATOR: {
        "process.read",
        "device.register",
        "device.update",
        "service.start",
        "service.stop",
        "service.health",
        "telemetry.read",
        "telemetry.write",
    },
    ROLE_ORCA_VIEWER: {
        "process.read",
        "service.health",
        "telemetry.read",
    },
}

ROLE_DESCRIPTIONS: dict[str, str] = {
    ROLE_ORCA_ADMIN: "Full ORCA administrative control across services, devices, and processes",
    ROLE_ORCA_SERVICE: "Service runtime role for backend and worker processes",
    ROLE_ORCA_DEVICE: "Registered device role for drones, robots, and sensors",
    ROLE_ORCA_AGENT: "Agent runtime role for local hardware and orchestration agents",
    ROLE_ORCA_OPERATOR: "Operator role for mission control and interactive tooling",
    ROLE_ORCA_VIEWER: "Read-only monitoring role for dashboards and observers",
}

API_ROLE_BRIDGE = {
    ROLE_ORCA_ADMIN: "admin",
    ROLE_ORCA_OPERATOR: "operator",
    ROLE_ORCA_VIEWER: "viewer",
    ROLE_ORCA_SERVICE: "operator",
    ROLE_ORCA_DEVICE: "operator",
    ROLE_ORCA_AGENT: "operator",
}


@dataclass(frozen=True)
class ProcessIdentity:
    upi: str
    component_type: str
    role: str
    dn: str
    description: str
    registered_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass(frozen=True)
class LDAPEntry:
    dn: str
    object_classes: tuple[str, ...]
    attributes: dict[str, Any]


def _optional_import_ldap3() -> Any | None:
    try:
        import ldap3  # type: ignore
    except ImportError:
        return None
    return ldap3


def _optional_import_fortress() -> Any | None:
    try:
        import py_fortress as fortress  # type: ignore
    except ImportError:
        try:
            import fortress  # type: ignore
        except ImportError:
            return None
    return fortress


def generate_upi(component_type: str, component_uuid: UUID | str | None = None) -> str:
    normalized = component_type.strip().lower()
    if normalized not in SUPPORTED_COMPONENT_TYPES:
        raise ValueError(f"Unsupported ORCA component type: {component_type}")
    if component_uuid is None:
        component_id = uuid4()
    elif isinstance(component_uuid, UUID):
        component_id = component_uuid
    else:
        component_id = UUID(str(component_uuid))
    return f"orca:{normalized}:{component_id}"


def is_valid_upi(value: str) -> bool:
    if UPI_PATTERN.match(value) is None:
        return False
    component_type = parse_upi(value)["component_type"]
    return component_type in SUPPORTED_COMPONENT_TYPES


def parse_upi(value: str) -> dict[str, str]:
    match = UPI_PATTERN.match(value)
    if match is None:
        raise ValueError(f"Invalid ORCA UPI: {value}")
    return match.groupdict()


def build_upi_dn(upi: str, *, ldap_base_dn: str = DEFAULT_LDAP_BASE_DN) -> str:
    parts = parse_upi(upi)
    component_type = parts["component_type"]
    ou = COMPONENT_OU.get(component_type)
    if ou is None:
        raise ValueError(f"No LDAP OU mapping for component type: {component_type}")
    return f"uid={upi},ou={ou},{ldap_base_dn}"


def build_ldap_entry(
    upi: str,
    *,
    description: str,
    role: str,
    ldap_base_dn: str = DEFAULT_LDAP_BASE_DN,
) -> LDAPEntry:
    return LDAPEntry(
        dn=build_upi_dn(upi, ldap_base_dn=ldap_base_dn),
        object_classes=("top", "device", "extensibleObject"),
        attributes={
            "uid": upi,
            "description": description,
            "orcaRole": role,
            "cn": upi,
        },
    )


def build_ldap_ou_entries(*, ldap_base_dn: str = DEFAULT_LDAP_BASE_DN) -> list[LDAPEntry]:
    return [
        LDAPEntry(
            dn=f"ou={ou_name},{ldap_base_dn}",
            object_classes=("top", "organizationalUnit"),
            attributes={"ou": ou_name},
        )
        for ou_name in REQUIRED_LDAP_OUS
    ]


def build_role_ldap_entries(*, ldap_base_dn: str = DEFAULT_LDAP_BASE_DN) -> list[LDAPEntry]:
    role_base_dn = f"ou=roles,{ldap_base_dn}"
    entries: list[LDAPEntry] = []
    for role_name, permissions in sorted(DEFAULT_ROLE_PERMISSIONS.items()):
        entries.append(
            LDAPEntry(
                dn=f"cn={role_name},{role_base_dn}",
                object_classes=("top", "organizationalRole", "extensibleObject"),
                attributes={
                    "cn": role_name,
                    "description": ROLE_DESCRIPTIONS.get(role_name, role_name),
                    "orcaPermission": sorted(permissions),
                },
            )
        )
    return entries


def render_ldif(entries: list[LDAPEntry]) -> str:
    rendered_blocks: list[str] = []
    for entry in entries:
        lines = [f"dn: {entry.dn}"]
        for object_class in entry.object_classes:
            lines.append(f"objectClass: {object_class}")
        for key, value in entry.attributes.items():
            if isinstance(value, (list, tuple, set)):
                for item in value:
                    lines.append(f"{key}: {item}")
            else:
                lines.append(f"{key}: {value}")
        rendered_blocks.append("\n".join(lines))
    return "\n\n".join(rendered_blocks) + "\n"


def identity_role_to_api_role(role: str) -> str:
    return API_ROLE_BRIDGE.get(role, "viewer")


def role_has_permission(role: str, permission: str) -> bool:
    return permission in DEFAULT_ROLE_PERMISSIONS.get(role, set())


def build_audit_event(
    upi: str,
    *,
    action: str,
    result: str = "allowed",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "identity": upi,
        "action": action,
        "result": result,
        "timestamp": datetime.now(UTC).isoformat(),
        "details": details or {},
    }


class InMemoryIdentityDirectory:
    def __init__(self) -> None:
        self._entries: dict[str, LDAPEntry] = {}
        self._roles: dict[str, set[str]] = {}

    def register(self, *, upi: str, description: str, role: str, ldap_base_dn: str = DEFAULT_LDAP_BASE_DN) -> ProcessIdentity:
        entry = build_ldap_entry(upi, description=description, role=role, ldap_base_dn=ldap_base_dn)
        self._entries[upi] = entry
        self._roles.setdefault(upi, set()).add(role)
        parsed = parse_upi(upi)
        return ProcessIdentity(
            upi=upi,
            component_type=parsed["component_type"],
            role=role,
            dn=entry.dn,
            description=description,
        )

    def authenticate(self, upi: str) -> bool:
        return upi in self._entries

    def authorize(self, upi: str, permission: str) -> bool:
        return any(role_has_permission(role, permission) for role in self._roles.get(upi, set()))

    def get_entry(self, upi: str) -> LDAPEntry | None:
        return self._entries.get(upi)


class LDAPIdentityDirectory:
    def __init__(
        self,
        *,
        server_uri: str,
        bind_dn: str,
        bind_password: str,
        ldap_base_dn: str = DEFAULT_LDAP_BASE_DN,
    ) -> None:
        self.server_uri = server_uri
        self.bind_dn = bind_dn
        self.bind_password = bind_password
        self.ldap_base_dn = ldap_base_dn

    def _connect(self) -> tuple[Any, Any]:
        ldap3 = _optional_import_ldap3()
        if ldap3 is None:
            raise RuntimeError("ldap3 is required for live LDAP operations")
        server = ldap3.Server(self.server_uri, get_info=ldap3.NONE)
        connection = ldap3.Connection(
            server,
            user=self.bind_dn,
            password=self.bind_password,
            auto_bind=True,
        )
        return ldap3, connection

    @staticmethod
    def _entry_value(entry: Any, attribute: str) -> Any:
        if hasattr(entry, "entry_attributes_as_dict"):
            values = entry.entry_attributes_as_dict.get(attribute)
            if isinstance(values, list) and len(values) == 1:
                return values[0]
            return values
        value = getattr(entry, attribute, None)
        if hasattr(value, "value"):
            return value.value
        return value

    def lookup_identity(self, upi: str) -> ProcessIdentity | None:
        ldap3, connection = self._connect()
        try:
            found = connection.search(
                search_base=build_upi_dn(upi, ldap_base_dn=self.ldap_base_dn),
                search_filter="(uid=*)",
                search_scope=ldap3.BASE,
                attributes=["uid", "orcaRole", "description"],
            )
            if not found or not connection.entries:
                return None
            entry = connection.entries[0]
            description = self._entry_value(entry, "description") or "ORCA directory identity"
            role = self._entry_value(entry, "orcaRole") or ROLE_ORCA_VIEWER
            parsed = parse_upi(upi)
            return ProcessIdentity(
                upi=upi,
                component_type=parsed["component_type"],
                role=str(role),
                dn=build_upi_dn(upi, ldap_base_dn=self.ldap_base_dn),
                description=str(description),
            )
        finally:
            connection.unbind()

    def get_role_permissions(self, role: str) -> set[str]:
        ldap3, connection = self._connect()
        try:
            found = connection.search(
                search_base=f"cn={role},ou=roles,{self.ldap_base_dn}",
                search_filter="(cn=*)",
                search_scope=ldap3.BASE,
                attributes=["orcaPermission"],
            )
            if not found or not connection.entries:
                return set(DEFAULT_ROLE_PERMISSIONS.get(role, set()))
            permissions = self._entry_value(connection.entries[0], "orcaPermission") or []
            if isinstance(permissions, str):
                return {permissions}
            return {str(permission) for permission in permissions}
        finally:
            connection.unbind()

    def ensure_role_seed(self) -> list[str]:
        ldap3, connection = self._connect()
        created_dns: list[str] = []
        role_ou_dn = f"ou=roles,{self.ldap_base_dn}"
        try:
            exists = connection.search(
                search_base=role_ou_dn,
                search_filter="(objectClass=organizationalUnit)",
                search_scope=ldap3.BASE,
                attributes=["ou"],
            )
            if not exists or not connection.entries:
                ok = connection.add(
                    role_ou_dn,
                    ["top", "organizationalUnit"],
                    {"ou": "roles"},
                )
                if not ok:
                    raise RuntimeError(f"LDAP role OU bootstrap failed for {role_ou_dn}: {connection.result}")
                created_dns.append(role_ou_dn)

            for entry in build_role_ldap_entries(ldap_base_dn=self.ldap_base_dn):
                exists = connection.search(
                    search_base=entry.dn,
                    search_filter="(cn=*)",
                    search_scope=ldap3.BASE,
                    attributes=["cn"],
                )
                if exists and connection.entries:
                    continue
                ok = connection.add(entry.dn, list(entry.object_classes), entry.attributes)
                if not ok:
                    raise RuntimeError(f"LDAP role seed failed for {entry.dn}: {connection.result}")
                created_dns.append(entry.dn)
        finally:
            connection.unbind()
        return created_dns

    def verify_role_assignment(self, upi: str, *, expected_role: str | None = None, permission: str | None = None) -> bool:
        identity = self.lookup_identity(upi)
        if identity is None:
            return False
        if expected_role is not None and identity.role != expected_role:
            return False
        if permission is None:
            return True
        return permission in self.get_role_permissions(identity.role)

    def update_role_assignment(self, upi: str, new_role: str) -> ProcessIdentity:
        ldap3, connection = self._connect()
        try:
            dn = build_upi_dn(upi, ldap_base_dn=self.ldap_base_dn)
            ok = connection.modify(
                dn,
                {"orcaRole": [(ldap3.MODIFY_REPLACE, [new_role])]}
            )
            if not ok:
                raise RuntimeError(f"LDAP role update failed for {upi}: {connection.result}")
        finally:
            connection.unbind()
        updated = self.lookup_identity(upi)
        if updated is None:
            raise RuntimeError(f"LDAP lookup failed after role update for {upi}")
        return updated

    def register(self, *, upi: str, description: str, role: str) -> ProcessIdentity:
        entry = build_ldap_entry(upi, description=description, role=role, ldap_base_dn=self.ldap_base_dn)
        _, connection = self._connect()
        try:
            ok = connection.add(entry.dn, list(entry.object_classes), entry.attributes)
            if not ok:
                raise RuntimeError(f"LDAP registration failed for {upi}: {connection.result}")
        finally:
            connection.unbind()
        parsed = parse_upi(upi)
        return ProcessIdentity(
            upi=upi,
            component_type=parsed["component_type"],
            role=role,
            dn=entry.dn,
            description=description,
        )

    def ensure_base_tree(self, *, include_role_seed: bool = True) -> list[str]:
        ldap3, connection = self._connect()
        created_dns: list[str] = []
        try:
            for entry in build_ldap_ou_entries(ldap_base_dn=self.ldap_base_dn):
                exists = connection.search(
                    search_base=entry.dn,
                    search_filter="(objectClass=organizationalUnit)",
                    search_scope=ldap3.BASE,
                    attributes=["ou"],
                )
                if exists and connection.entries:
                    continue
                ok = connection.add(entry.dn, list(entry.object_classes), entry.attributes)
                if not ok:
                    raise RuntimeError(f"LDAP bootstrap failed for {entry.dn}: {connection.result}")
                created_dns.append(entry.dn)
        finally:
            connection.unbind()
        if include_role_seed:
            created_dns.extend(self.ensure_role_seed())
        return created_dns

    def authenticate(self, upi: str, password: str) -> bool:
        ldap3 = _optional_import_ldap3()
        if ldap3 is None:
            raise RuntimeError("ldap3 is required for live LDAP authentication")
        server = ldap3.Server(self.server_uri, get_info=ldap3.NONE)
        connection = ldap3.Connection(
            server,
            user=build_upi_dn(upi, ldap_base_dn=self.ldap_base_dn),
            password=password,
            auto_bind=False,
        )
        try:
            return bool(connection.bind())
        finally:
            connection.unbind()


class FortressRBACAdapter:
    """Optional py-fortress adapter with local policy fallback.

    If a live Fortress client is not injected, ORCA still enforces the shared
    default policy locally.
    """

    def __init__(self, client: Any | None = None) -> None:
        self.client = client
        self.backend = _optional_import_fortress()

    def authorize(self, upi: str, role: str, permission: str) -> bool:
        if self.client is not None:
            for method_name in ("authorize", "check_access", "can"):
                method = getattr(self.client, method_name, None)
                if callable(method):
                    return bool(method(upi, role, permission))
        return role_has_permission(role, permission)


@lru_cache(maxsize=1)
def _local_directory() -> InMemoryIdentityDirectory:
    return InMemoryIdentityDirectory()


def bootstrap_process_identity(
    *,
    component_type: str,
    role: str,
    description: str,
    upi: str | None = None,
    ldap_base_dn: str = DEFAULT_LDAP_BASE_DN,
    directory: InMemoryIdentityDirectory | None = None,
) -> ProcessIdentity:
    identity_upi = upi or generate_upi(component_type)
    if not is_valid_upi(identity_upi):
        raise ValueError(f"Invalid ORCA UPI: {identity_upi}")
    target_directory = directory or _local_directory()
    return target_directory.register(
        upi=identity_upi,
        description=description,
        role=role,
        ldap_base_dn=ldap_base_dn,
    )


def identity_posture(identity: ProcessIdentity) -> dict[str, Any]:
    permissions = sorted(DEFAULT_ROLE_PERMISSIONS.get(identity.role, set()))
    return {
        "upi": identity.upi,
        "component_type": identity.component_type,
        "role": identity.role,
        "api_role": identity_role_to_api_role(identity.role),
        "ldap_dn": identity.dn,
        "permissions": permissions,
        "registered_at": identity.registered_at,
    }