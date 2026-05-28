# ============================================================================
# File: native/setup.py
# Purpose:
#   Build script for the optional `orca_fast` C extension. Kept as a
#   separate distribution so it never blocks pure-Python contributors.
#
# Build (in-place .so next to this file):
#     python setup.py build_ext --inplace
#
# Install into the active environment:
#     pip install .
# ============================================================================

from setuptools import Extension, setup

setup(
    name="orca-fast",
    version="0.1.0",
    description="C accelerators for the Orca Urban Data Backbone",
    license="Apache-2.0",
    ext_modules=[
        Extension(
            name="orca_fast",
            sources=["orca_fast.c"],
            extra_compile_args=["-O3", "-Wall", "-Wextra", "-std=c11"],
        ),
    ],
)
