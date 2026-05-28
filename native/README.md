<!--
================================================================================
 File: native/README.md
 Purpose:
   Explains the role of C in Orca and how to build the optional
   native acceleration module.
================================================================================
-->

# `native/` — C performance extensions

Orca is **Python-first**. This directory contains optional C code for
the narrow cases where Python is genuinely the wrong tool:

1. **Low-level IoT drivers** — talking to a serial/SPI/I²C sensor where
   microsecond timing or bit-banged protocols matter.
2. **Hot-path packet parsing** — decoding tens of thousands of binary
   sensor frames per second per core.
3. **Crypto primitives** — when a deployment must run on a constrained
   edge box and can't depend on OpenSSL.

If your contribution does **not** fit one of those three buckets, please
keep it in pure Python. Python is the project's lingua franca.

## What's included

- `orca_fast.c` — a CPython extension module with a `parse_frame()`
  function that decodes the Orca binary sensor frame format
  ~10–50x faster than a pure-Python implementation.

## Building

The extension is **opt-in**. Building it requires a C compiler and the
Python development headers.

```bash
# macOS:  brew install python  (headers ship with the official installer)
# Debian: sudo apt-get install build-essential python3-dev

cd native
python setup.py build_ext --inplace
```

This produces a `orca_fast*.so` (or `.pyd` on Windows) next to
`setup.py`. Drop it onto `PYTHONPATH` or install with:

```bash
pip install .
```

## Using from Python

```python
try:
    from orca_fast import parse_frame  # C accelerator
except ImportError:
    from app.services.frame_parser import parse_frame  # Pure-Python fallback
```

Always provide a pure-Python fallback so contributors without a C toolchain
can still run the project.

## Style

- C11.
- `clang-format` (LLVM style) — config lives in `.clang-format`.
- Every public function gets a Doxygen-style comment.
- No `malloc()` without a paired `free()` on every code path.
