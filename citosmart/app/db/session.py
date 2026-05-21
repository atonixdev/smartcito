"""
================================================================================
 File: backend/app/db/session.py
 Purpose:
   Async SQLAlchemy engine + session factory. Exposes a FastAPI
   dependency (`get_session`) that hands out a per-request session and
   guarantees it is closed.

   We use the async PostgreSQL driver (asyncpg) by default. The DSN is
   computed from settings — no hard-coded strings.
================================================================================
"""

from __future__ import annotations

from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_settings = get_settings()

# `pool_pre_ping` cheaply detects stale connections after DB restarts.
engine = create_async_engine(
    _settings.database_url,
    pool_pre_ping=True,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields an async DB session.

    Usage:
        @router.get("/things")
        async def list_things(session: AsyncSession = Depends(get_session)):
            ...
    """
    async with AsyncSessionLocal() as session:
        yield session
