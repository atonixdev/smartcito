"""
================================================================================
 File: backend/migrations/env.py
 Purpose:
   Alembic environment script. Two key differences from the default
   template:

     1. The database URL is read from `app.core.config.Settings` (no
        secrets in alembic.ini).
     2. `target_metadata` points at our SQLAlchemy `Base.metadata` so
        autogenerate sees every ORM model imported in `app.db.models`.

 Run from `backend/`:
     alembic upgrade head
     alembic revision --autogenerate -m "describe change"
================================================================================
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.db.base import Base
import app.db.models  # noqa: F401 — import so models register on Base.metadata

# Alembic config object.
config = context.config

# Inject the live DB URL from Settings. Alembic uses the sync DSN, so
# strip the `+asyncpg` driver suffix that the async engine uses.
_settings = get_settings()
sync_url = _settings.database_url.replace("+asyncpg", "+psycopg2")
config.set_main_option("sqlalchemy.url", sync_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Render the migration SQL without a live DB connection."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
