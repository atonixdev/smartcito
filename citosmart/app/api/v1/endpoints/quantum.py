"""
================================================================================
 File: citosmart/app/api/v1/endpoints/quantum.py
 Purpose:
   Quantum-ready security endpoints for Orca.

 Endpoints:
   GET  /api/v1/quantum/profile      Advertise PQC/QKD posture.
   GET  /api/v1/quantum/qkd-keys     List imported QKD key metadata.
   POST /api/v1/quantum/qkd-keys     Import externally derived QKD material.
   POST /api/v1/quantum/envelope     Create a hybrid encrypted payload.
================================================================================
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import require_role
from app.schemas.quantum import (
    HybridEnvelopeIn,
    HybridEnvelopeOut,
    QkdKeyImportIn,
    QkdKeyMetadata,
    QuantumSecurityProfile,
)
from app.services.quantum_security import quantum_security_service

router = APIRouter()


@router.get(
    "/profile",
    response_model=QuantumSecurityProfile,
    dependencies=[Depends(require_role("viewer"))],
    summary="Return the service's quantum-ready security profile",
)
async def quantum_profile() -> QuantumSecurityProfile:
    """Advertise supported PQC migration targets and QKD ingest capability."""
    return quantum_security_service.profile()


@router.get(
    "/qkd-keys",
    response_model=list[QkdKeyMetadata],
    dependencies=[Depends(require_role("viewer"))],
    summary="List imported QKD key metadata",
)
async def list_qkd_keys() -> list[QkdKeyMetadata]:
    """Return metadata for imported QKD-derived keys without exposing secrets."""
    return quantum_security_service.list_qkd_keys()


@router.post(
    "/qkd-keys",
    response_model=QkdKeyMetadata,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin"))],
    summary="Import externally provisioned QKD key material",
)
async def import_qkd_key(request: QkdKeyImportIn) -> QkdKeyMetadata:
    """Ingest externally derived QKD material into the local secure store."""
    try:
        return quantum_security_service.import_qkd_key(request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/envelope",
    response_model=HybridEnvelopeOut,
    dependencies=[Depends(require_role("operator"))],
    summary="Encrypt a payload using the hybrid quantum-ready envelope",
)
async def create_hybrid_envelope(request: HybridEnvelopeIn) -> HybridEnvelopeOut:
    """Return an AES-256-GCM envelope derived from PQC/QKD-aware metadata."""
    try:
        return quantum_security_service.create_hybrid_envelope(request)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
