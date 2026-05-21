"""
================================================================================
 File: ai_models/model.py
 Purpose:
   Tiny scoring model used as a placeholder for real SmartCito inference.
================================================================================
"""

from __future__ import annotations


def score_anomaly(features: list[float]) -> float:
    """Return a simple bounded score for demo and smoke-test purposes."""
    if not features:
        return 0.0
    score = sum(abs(value) for value in features) / len(features)
    return round(min(score, 1.0), 4)
