"""
================================================================================
 File: citosmart/app/api/v1/endpoints/auth.py
 Purpose:
   OAuth2 password-flow authentication for first-party clients (city ops
   dashboard, mobile). In production, swap to an external IdP (Keycloak,
   Auth0, Azure AD B2C) and keep this module as a thin facade.

 NOTE:
   The user store here is an in-memory stub for demonstration only.
   Replace `FAKE_USERS` with a real DB lookup before any real deployment.
     Production deployments must delegate to an external IdP with MFA and
     short-lived RS256-signed tokens as documented in `security/iam/oauth2.md`.
================================================================================
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
    TokenPayload,
)
from app.schemas.api_response import api_envelope

router = APIRouter()


# ----- Demo user store (replace with database lookups) ----------------------
# Passwords are pre-hashed at import to avoid logging plaintext anywhere.
FAKE_USERS: dict[str, dict[str, str]] = {
    "admin@smartcito.dev": {
        "hashed_password": hash_password("changeme"),
        "role": "admin",
    },
    "viewer@smartcito.dev": {
        "hashed_password": hash_password("changeme"),
        "role": "viewer",
    },
}


class TokenResponse(BaseModel):
    """OAuth2-compliant token response."""

    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    """Caller-info response."""

    username: str
    role: str


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Exchange username/password for a JWT access token",
)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
    """OAuth2 password grant.

    Returns:
        A signed JWT access token suitable for the `Authorization: Bearer`
        header on subsequent calls.
    """
    user = FAKE_USERS.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        # Avoid leaking which half of the credential was wrong.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(subject=form_data.username, role=user["role"])
    return TokenResponse(access_token=token)


@router.get("/me", response_model=MeResponse, summary="Return the current caller")
async def whoami(current: TokenPayload = Depends(get_current_user)) -> MeResponse:
    """Echo the decoded token. Useful for debugging webapps."""
    return MeResponse(username=current.sub, role=current.role)


@router.post("/login", summary="Login and return a traced API envelope")
async def login_envelope(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    token = await login(form_data)
    return api_envelope(request, token.model_dump())


@router.post("/refresh", summary="Refresh the current JWT")
async def refresh_token(
    request: Request,
    current: TokenPayload = Depends(get_current_user),
):
    token = create_access_token(subject=current.sub, role=current.role)
    return api_envelope(request, {"access_token": token, "token_type": "bearer"})


@router.post("/logout", summary="Client-side token logout acknowledgement")
async def logout(request: Request, current: TokenPayload = Depends(get_current_user)):
    return api_envelope(request, {"username": current.sub, "logged_out": True})
