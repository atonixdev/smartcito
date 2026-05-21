"""
================================================================================
 File: backend/app/core/security.py
 Purpose:
   Authentication and authorization primitives for the SmartCito API.

   Provides:
     - Password hashing (bcrypt via passlib).
     - JWT issuance and verification (python-jose).
     - A FastAPI dependency to extract the current user from a Bearer token.

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

# The tokenUrl points at the OAuth2 password flow endpoint exposed by the API.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


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
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> TokenPayload:
    """Verify a JWT and return its typed payload.

    Raises:
        HTTPException(401): If the token is invalid, expired, or malformed.
    """
    settings = get_settings()
    try:
        raw = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        return TokenPayload(**raw)
    except (InvalidTokenError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    """FastAPI dependency that yields the authenticated user's claims."""
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
