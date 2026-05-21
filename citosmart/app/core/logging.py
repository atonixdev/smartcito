"""
================================================================================
 File: backend/app/core/logging.py
 Purpose:
   Configure structured (JSON-friendly) logging via the standard library.
   Structured logs are essential for shipping to ELK/Loki/Datadog and for
   building reliable audit trails in a smart-city deployment.
================================================================================
"""

from __future__ import annotations

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """Install a single root handler with a consistent format.

    Args:
        level: A logging level name ("DEBUG", "INFO", "WARNING", ...).
    """
    root = logging.getLogger()
    # Avoid duplicate handlers on hot-reload (uvicorn --reload).
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt='{"ts":"%(asctime)s","lvl":"%(levelname)s",'
                '"logger":"%(name)s","msg":"%(message)s"}',
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )
    root.addHandler(handler)
    root.setLevel(level.upper())
