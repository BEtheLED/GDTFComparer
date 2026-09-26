---
phase: 01-foundation-rebuild
plan: 01
subsystem: toolchain-scaffold
tags: [scaffold, pyproject, venv, pytest, pytest-qt, pygdtf, pyside6]
dependency graph:
  requires: []
  provides:
    - pyproject.toml (pinned deps, setuptools src-layout, pytest+pytest-qt config)
    - src/gdtf_comparer/{__init__,core/__init__,gui/__init__}.py package skeleton
    - tests/conftest.py::build_description_xml, fixture make_gdtf
    - tests/test_fixture_builder.py (toolchain + round-trip guard)
    - shared .venv at the main checkout with the approved pinned toolchain
  affects:
    - "01-02 (tracer plan): consumes the venv, pyproject entry point, package skeleton, and make_gdtf fixture"
tech-stack:
  added:
    - "PySide6==6.11.2"
    - "pygdtf==1.4.5"
    - "defusedxml==0.7.1"
    - "qt-material==2.17"
    - "pytest==9.1.1"
    - "pytest-qt==4.5.0"
  patterns:
    - "src-layout package with Qt-free core/ vs PySide6 gui/ (D-04, D-16)"
    - "ONE shared venv resolved via git-common-dir, used from any worktree"
key-files:
  created:
    - pyproject.toml
    - .gitignore
    - src/gdtf_comparer/__init__.py
    - src/gdtf_comparer/core/__init__.py
    - src/gdtf_comparer/gui/__init__.py
    - tests/conftest.py
    - tests/test_fixture_builder.py
  modified: []
  deleted:
    - tests/test_parse_gdtf.py
decisions:
  - "Task 1 package-legitimacy checkpoint resolved as approved per retry_context (human already reviewed the exact pinned set in a prior attempt); no re-stop"
  - "pytest 9.1.1 + pytest-qt 4.5.0 installed cleanly together — no plugin import error at collection, so the plan's 8.4.2 fallback was not needed"
metrics:
  duration: "~15 min"
  completed: 2026-09-26
status: complete
actuals:
  tokens: 2327
  tasks: 2
  commits: 1
  plan_head_before: 26dbd103502d12bcde622f2f0e3b8a13e4c770ce
---

# Phase 01 Plan 01: Toolchain Scaffold + Package Legitimacy Gate Summary

Gated the phase's first third-party install behind human package-legitimacy review (resolved as approved), then scaffolded the pinned src-layout project (pyproject.toml, core/gui package skeleton, pytest+pytest-qt harness, GDTF test-file builder) with a shared `.venv` at the main checkout.

## What Was Built

**Task 1 (checkpoint:human-verify, gate="blocking-human") — resolved, not re-stopped.**
This is a RETRY of plan 01-01. A prior attempt correctly halted at this exact checkpoint without installing or committing anything; that empty worktree was torn down with no commits. Per the orchestrator's retry instructions, the human had already reviewed and approved the exact pinned package set proposed in 01-01-PLAN.md (PySide6==6.11.2, pygdtf==1.4.5, defusedxml==0.7.1, qt-material==2.17, pytest==9.1.1, pytest-qt==4.5.0, plus expected transitives: shiboken6, PySide6-Essentials, PySide6-Addons, Jinja2, MarkupSafe, pluggy, iniconfig, packaging, Pygments). No substitutions were requested. This resolution is recorded here as the checkpoint's outcome instead of re-emitting a `checkpoint:human-verify` stop.

**Task 2 (auto) — scaffold + install, all as specified in 01-01-PLAN.md:**
- `pyproject.toml`: setuptools src-layout build, `requires-python = ">=3.11"`, exact pins for all 4 runtime deps + 2 dev deps, `[project.gui-scripts] gdtf-comparer = "gdtf_comparer.app:main"`, `[tool.pytest.ini_options]` with `testpaths`, `pythonpath = ["src"]`, `--import-mode=importlib`, `qt_api = "pyside6"`.
- `.gitignore`: `.venv/`, caches, build artifacts, `.DS_Store`.
- `src/gdtf_comparer/__init__.py` (`__version__ = "0.1.0"`), `src/gdtf_comparer/core/__init__.py` and `src/gdtf_comparer/gui/__init__.py` — docstring-only markers, no imports, enforcing D-16's Qt-free core boundary.
- `tests/conftest.py`: sets `QT_QPA_PLATFORM=offscreen` at import time, `build_description_xml(...)` builds a well-formed GDTF 1.2 `description.xml` with XML-escaped attribute values, `make_gdtf(tmp_path)` fixture writes real `.gdtf` ZIP_DEFLATED archives (with support for omitted description, explicit description override, and extra members).
- `tests/test_fixture_builder.py`: `test_toolchain_versions` (importlib.metadata pins + Python floor), `test_builder_roundtrips_through_pygdtf` (builds a fixture with one Model + one Beam geometry, opens it with `pygdtf.FixtureType` as a context manager, asserts name/manufacturer/weight/model width/beam angle), `test_qt_offscreen_platform` (asserts `qapp.platformName() == "offscreen"`).
- Deleted `tests/test_parse_gdtf.py` (loaded `BEtheLD`, which imports `tkinter`; the new venv has no `_tkinter`, so it could not even be collected — its three behaviors are re-covered by Plan 01-02 (valid parse), 01-04 `test_repository.py` (invalid zip) and `test_hardening.py` (malformed XML)).
- Built the shared venv at `/Users/brandon/GDTFComparer/.venv` (main checkout, sibling to `.git`) via `/opt/homebrew/bin/python3.12 -m venv`, appended `.venv/` to the main checkout's `.git/info/exclude`, then ran `pip install -e ".[dev]"`.

## Installation Result

All approved packages installed at the exact pinned versions, with exactly the transitive tree research predicted:
`Jinja2-3.1.6 MarkupSafe-3.0.3 PySide6-6.11.2 PySide6_Addons-6.11.2 PySide6_Essentials-6.11.2 defusedxml-0.7.1 gdtf-comparer-0.1.0 iniconfig-2.3.0 packaging-26.3 pluggy-1.6.0 pygdtf-1.4.5 pygments-2.21.0 pytest-9.1.1 pytest-qt-4.5.0 qt-material-2.17 shiboken6-6.11.2 typing_extensions-4.16.0`

No unexpected/typosquatted package names appeared. pytest 9.1.1 and pytest-qt 4.5.0 loaded together with no plugin import error at collection, so the plan's `pytest==8.4.2` fallback pin was **not** needed.

## Verification

- `.venv/bin/python -m pytest tests/test_fixture_builder.py -q` -> **3 passed**
- `test ! -e tests/test_parse_gdtf.py && git check-ignore -q .venv/ && grep -q 'requires-python = ">=3.11"' pyproject.toml` -> all three conditions true
- `.venv/bin/python -c "import sys; assert (3,11) <= sys.version_info[:2] < (3,15)"` -> exits 0 (3.12.13)
- `git ls-files tests/test_parse_gdtf.py` -> prints nothing (confirmed after commit)
- `find tests -name __init__.py` -> prints nothing
- `src/gdtf_comparer/core/__init__.py` and `gui/__init__.py` contain no import statements (docstring text containing the word "import" was verified by direct read, not just grep, to rule out a false positive)

## Deviations from Plan

None — plan executed exactly as written. The Task 1 checkpoint resolution (recording pre-existing human approval instead of re-emitting the stop) was explicitly directed by the orchestrator's retry_context, not an executor-initiated deviation.

## Known Stubs

None. This plan is toolchain scaffolding only; no UI-facing code was written.

## Self-Check: PASSED

- FOUND: pyproject.toml
- FOUND: .gitignore
- FOUND: src/gdtf_comparer/__init__.py
- FOUND: src/gdtf_comparer/core/__init__.py
- FOUND: src/gdtf_comparer/gui/__init__.py
- FOUND: tests/conftest.py
- FOUND: tests/test_fixture_builder.py
- MISSING (intentionally deleted): tests/test_parse_gdtf.py
- FOUND commit: 878dd53 (feat(01-01): scaffold pinned src-layout project and GDTF test-file builder)
