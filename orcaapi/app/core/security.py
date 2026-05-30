"""
================================================================================
 File: orcaapi/app/core/security.py
 Purpose:
     Authentication and authorization primitives for the Orca API.

     Provides:
         - Password hashing (bcrypt via passlib) for legacy token flows.
         - JWT issuance and verification when explicit tokens are used.
         - A FastAPI dependency that defaults to local-first access when no token
             is supplied.

 Security notes:
     - Tokens use HS256 by default for simplicity; switch to RS256 in
         multi-service production deployments and load keys from a KMS.
     - Passwords are NEVER logged or returned in API responses.
================================================================================
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt  # PyJWT — pure-Python JWT library
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import get_settings

# bcrypt is intentionally slow → safe against brute force on stolen hashes.
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token parsing remains available for explicit bearer-token integrations, but
# local installs no longer require user login or account-backed sessions.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)

LOCAL_SYSTEM_SUBJECT = "local-device"
LOCAL_SYSTEM_ROLE = "admin"
LOCAL_SYSTEM_EXP = 4102444800


class TokenPayload(BaseModel):
    """Decoded JWT claims relevant to the application."""

    sub: str
    role: str = "viewer"
    exp: int


def hash_password(plain: str) -> str:
    """Return a bcrypt hash for the given plaintext password."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time comparison of a plaintext password against its hash."""
    return _pwd_context.verify(plain, hashed)


def create_access_token(
    subject: str,
    role: str = "viewer",
    expires_minutes: int | None = None,
) -> str:
    """Issue a signed JWT access token.

    Args:
        subject: Stable user identifier (typically user id or email).
        role: RBAC role embedded in the token (e.g. "admin", "viewer").
        expires_minutes: Override the default expiry from settings.
    """
    settings = get_settings()
    expire = datetime.now(tz=timezone.utc) + timedelta(
        minutes=expires_minutes or settings.jwt_access_token_expires_minutes
    )
    payload: dict[str, Any] = {"sub": subject, "role": role, "exp": expire}
    signing_key = settings.secret_key
    if settings.jwt_algorithm.startswith(("RS", "ES")) and settings.jwt_private_key_pem:
        signing_key = settings.jwt_private_key_pem
    return jwt.encode(payload, signing_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> TokenPayload:
    """Verify a JWT and return its typed payload.

    Raises:
        HTTPException(401): If the token is invalid, expired, or malformed.
    """
    settings = get_settings()
    try:
        verification_key = settings.secret_key
        if settings.jwt_algorithm.startswith(("RS", "ES")) and settings.jwt_public_key_pem:
            verification_key = settings.jwt_public_key_pem
        raw = jwt.decode(token, verification_key, algorithms=[settings.jwt_algorithm])
        return TokenPayload(**raw)
    except (InvalidTokenError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_user(token: str | None = Depends(oauth2_scheme)) -> TokenPayload:
    """FastAPI dependency that yields local-first caller claims.

    If no bearer token is present, ORCA assumes a local install flow and
    grants an in-process system identity instead of requiring login.
    """
    if token is None or not token.strip():
        return TokenPayload(sub=LOCAL_SYSTEM_SUBJECT, role=LOCAL_SYSTEM_ROLE, exp=LOCAL_SYSTEM_EXP)
    return decode_token(token)


def require_role(required: str):
    """Return a dependency that enforces a minimum RBAC role.

    Usage:
        @router.post("/", dependencies=[Depends(require_role("admin"))])
    """
    role_rank = {"viewer": 0, "operator": 1, "admin": 2}

    def _checker(user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        if role_rank.get(user.role, -1) < role_rank.get(required, 99):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role '{required}' or higher",
            )
        return user

    return _checker
