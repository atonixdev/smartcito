"""
================================================================================
 File: ingestion/spark_job.py
 Purpose:
   Minimal Spark Structured Streaming job template for SmartCito ingestion.
================================================================================
"""

from __future__ import annotations


def build_stream_description() -> dict[str, object]:
    """Return a declarative description of the intended Spark pipeline."""
    return {
        "source": "kafka",
        "transformations": ["parse-json", "validate-schema", "enrich-location"],
        "sink": "console",
    }


if __name__ == "__main__":
    print(build_stream_description())
