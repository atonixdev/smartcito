"""
================================================================================
 File: backend/app/db/base.py
 Purpose:
   Declarative base for SQLAlchemy 2.0 ORM models.

   We use the typed `DeclarativeBase` style — every model column is
   declared with `Mapped[...]` so mypy and IDEs can reason about it.
================================================================================
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Project-wide ORM base class. Import this in every model module."""
