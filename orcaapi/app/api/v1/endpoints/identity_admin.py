"""
================================================================================
 File: orcaapi/app/api/v1/endpoints/identity_admin.py
 Purpose:
   Admin-only identity management endpoints for LDAP-backed ORCA identity
   inspection and mutation, suitable for desktop operator tooling.
================================================================================
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.core.security import require_role
from orca_shared.identity import LDAPIdentityDirectory, generate_upi, identity_posture

router = APIRouter(dependencies=[Depends(require_role("admin"))])


class IdentityInspectResponse(BaseModel):
    upi: str
    component_type: str
    role: str
    api_role: str
    ldap_dn: str
    permissions: list[str]
    registered_at: str
    live_role_permissions: list[str]
    ldap_verified: bool


class IdentityRegisterRequest(BaseModel):
    component_type: str = Field(..., examples=["service"])
    role: str = Field(..., examples=["orca.service"])
    description: str
    upi: str | None = None


class IdentityRegisterResponse(BaseModel):
    upi: str
    component_type: str
    role: str
    api_role: str
    ldap_dn: str
    permissions: list[str]
    registered_at: str
    ldap_verified: bool


class IdentityUpdateRoleRequest(BaseModel):
    role: str


class IdentityVerifyRequest(BaseModel):
    expected_role: str | None = None
    permission: str | None = None


class IdentityVerifyResponse(BaseModel):
    upi: str
    expected_role: str | None = None
    permission: str | None = None
    current_role: str | None = None
    verified: bool


class RolePermissionsResponse(BaseModel):
    role: str
    permissions: list[str]
    permission_count: int


class BootstrapRolesResponse(BaseModel):
    ldap_base_dn: str
    created_dns: list[str]
    seeded_roles: bool = True


def _get_ldap_admin_directory(settings: Settings = Depends(get_settings)) -> LDAPIdentityDirectory:
    if not settings.ldap_bind_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LDAP admin operations are unavailable: missing bind password",
        )
    return LDAPIdentityDirectory(
        server_uri=settings.ldap_server_uri,
        bind_dn=settings.ldap_bind_dn,
        bind_password=settings.ldap_bind_password,
        ldap_base_dn=settings.ldap_base_dn,
    )


@router.get("/{upi}", response_model=IdentityInspectResponse, summary="Inspect one LDAP-backed ORCA identity")
async def inspect_identity(
    upi: str,
    directory: LDAPIdentityDirectory = Depends(_get_ldap_admin_directory),
) -> IdentityInspectResponse:
    identity = directory.lookup_identity(upi)
    if identity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"identity not found in LDAP: {upi}")
    posture = identity_posture(identity)
    posture["live_role_permissions"] = sorted(directory.get_role_permissions(identity.role))
    posture["ldap_verified"] = directory.verify_role_assignment(upi, expected_role=identity.role)
    return IdentityInspectResponse(**posture)


@router.post("/register", response_model=IdentityRegisterResponse, status_code=status.HTTP_201_CREATED, summary="Register a new ORCA UPI in LDAP")
async def register_identity(
    request: IdentityRegisterRequest,
    directory: LDAPIdentityDirectory = Depends(_get_ldap_admin_directory),
) -> IdentityRegisterResponse:
    identity = directory.register(
        upi=request.upi or generate_upi(request.component_type),
        description=request.description,
        role=request.role,
    )
    posture = identity_posture(identity)
    posture["ldap_verified"] = directory.verify_role_assignment(identity.upi, expected_role=identity.role)
    return IdentityRegisterResponse(**posture)


@router.post("/{upi}/verify", response_model=IdentityVerifyResponse, summary="Verify an LDAP identity role assignment")
async def verify_identity(
    upi: str,
    request: IdentityVerifyRequest,
    directory: LDAPIdentityDirectory = Depends(_get_ldap_admin_directory),
) -> IdentityVerifyResponse:
    identity = directory.lookup_identity(upi)
    return IdentityVerifyResponse(
        upi=upi,
        expected_role=request.expected_role,
        permission=request.permission,
        current_role=identity.role if identity is not None else None,
        verified=directory.verify_role_assignment(
            upi,
            expected_role=request.expected_role,
            permission=request.permission,
        ),
    )


@router.post("/{upi}/role", response_model=IdentityRegisterResponse, summary="Update the LDAP role assignment for one ORCA identity")
async def update_identity_role(
    upi: str,
    request: IdentityUpdateRoleRequest,
    directory: LDAPIdentityDirectory = Depends(_get_ldap_admin_directory),
) -> IdentityRegisterResponse:
    try:
        updated = directory.update_role_assignment(upi, request.role)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    posture = identity_posture(updated)
    posture["ldap_verified"] = directory.verify_role_assignment(upi, expected_role=updated.role)
    return IdentityRegisterResponse(**posture)


@router.get("/roles/{role}", response_model=RolePermissionsResponse, summary="List live LDAP permissions for one ORCA role")
async def get_role_permissions(
    role: str,
    directory: LDAPIdentityDirectory = Depends(_get_ldap_admin_directory),
) -> RolePermissionsResponse:
    permissions = sorted(directory.get_role_permissions(role))
    return RolePermissionsResponse(role=role, permissions=permissions, permission_count=len(permissions))


@router.post("/bootstrap-roles", response_model=BootstrapRolesResponse, summary="Seed ORCA LDAP role entries and permissions")
async def bootstrap_roles(
    directory: LDAPIdentityDirectory = Depends(_get_ldap_admin_directory),
    settings: Settings = Depends(get_settings),
) -> BootstrapRolesResponse:
    return BootstrapRolesResponse(
        ldap_base_dn=settings.ldap_base_dn,
        created_dns=directory.ensure_role_seed(),
    )