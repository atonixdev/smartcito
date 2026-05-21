"""
================================================================================
 File: database/bootstrap.py
 Purpose:
   Lightweight database bootstrap helper for local SmartCito development.
================================================================================
"""

from __future__ import annotations

from pathlib import Path


def load_schema() -> str:
    """Return the bundled SQL schema for local initialization."""
    return (Path(__file__).parent / "init" / "001_schema.sql").read_text()


if __name__ == "__main__":
    print(load_schema())
