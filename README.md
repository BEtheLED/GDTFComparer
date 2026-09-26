# GDTF Comparer

Compare a target GDTF fixture file against one or more comparison GDTF
files and see which attributes actually differ, side by side. Phase 1 shows
the Beam and Physical Properties categories per element (per beam geometry
and per 3D model); full attribute browsing and diff highlighting land in
later phases.

## Requirements

- Python 3.11+
- macOS, Windows, or Linux

## Setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

Any Python 3.11 or newer works (for example `python3.11` or `python3.12`) —
substitute the interpreter you have if `python3` doesn't resolve to one.

On Windows, use the equivalent commands:

```bat
py -3 -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
```

## Run

```bash
.venv/bin/gdtf-comparer
```

or, from the repo root, without installing the console script:

```bash
PYTHONPATH=src .venv/bin/python -m gdtf_comparer.app
```

On Windows, substitute `.venv\Scripts\python`.

## Test

```bash
.venv/bin/python -m pytest
```

## Project Layout

- `src/gdtf_comparer/core/` — Qt-free parsing/comparison service (pygdtf
  wrapping, attribute extraction, comparison logic). Never imports Qt.
- `src/gdtf_comparer/gui/` — PySide6 presentation layer. Only talks to
  `core` through `core.comparator`, `core.models` and `core.errors`; never
  imports `pygdtf`, `zipfile` or `defusedxml` directly.
- `src/gdtf_comparer/app.py` — composition root: builds the `QApplication`,
  applies the OS-following qt-material theme, and shows the main window.
- `tests/core`, `tests/gui` — unit/integration tests for each layer;
  `tests/test_architecture.py` enforces the `core`/`gui` boundary above.

## Safety

Every selected `.gdtf` file is treated as untrusted input, including files
you pick yourself. Files over 100 MB, XML containing a DTD or external
entities, and zip archives with an implausible compression ratio (zip
bombs) are rejected with a friendly error message instead of being parsed.

## Blender Addon

This repository now also contains a minimal skeleton for a Blender addon that
aims to provide support for importing MVR and GDTF files. The addon lives in
the `blender_addon` directory and currently only defines the basic structure
needed for a Blender add-on.
