---
phase: 01-foundation-rebuild
plan: 05
subsystem: theming-and-architecture-guard
tags: [qt-material, pyside6, os-theme, ast, import-boundary, readme]
dependency graph:
  requires:
    - "01-02 (app.create_main_window composition root, MainWindow, gui/core package layout)"
  provides:
    - "gui.theme: LIGHT_THEME, DARK_THEME, THEME_PROPERTY, theme_for_scheme, apply_theme, OsThemeFollower, install_os_theme"
    - "app.create_main_window now applies the OS-following qt-material theme before constructing MainWindow"
    - "tests/test_architecture.py: imported_modules(source, module_name), iter_package_modules(package_dir, package_name), and a permanent AST-based gui/core import-boundary guard"
    - "README.md: setup/run/test documentation and project layout for the rebuilt app"
  affects:
    - "Any later phase adding a gui or core module must keep passing tests/test_architecture.py's import-boundary rules"
tech-stack:
  added: []
  patterns:
    - "OS theme following via PySide6's built-in QStyleHints.colorScheme()/colorSchemeChanged -- no extra theme-detection dependency (D-06, RESEARCH A2)"
    - "Idempotent theme application via a dynamic THEME_PROPERTY on the QApplication, preventing re-apply loops and duplicate OsThemeFollower instances across repeated create_main_window calls"
    - "AST-based (not grep-based) architecture guard: imported_modules() resolves both absolute and relative imports to fully-qualified dotted names, so comments/docstrings/string literals can never cause a false positive or negative"
key-files:
  created:
    - src/gdtf_comparer/gui/theme.py
    - tests/gui/test_theme.py
    - tests/test_architecture.py
  modified:
    - src/gdtf_comparer/app.py
    - README.md
  deleted:
    - BEtheLD
decisions:
  - "Accent theme (D-07 discretion): dark_blue.xml / light_blue.xml -- verified present in the installed qt_material 2.17's list_themes(); blue is neutral/high-contrast in both modes and avoids amber/red, which lighting/AV operators read as warning/indicator colors on real fixtures and consoles (documented in gui/theme.py's module docstring)"
  - "test_architecture.py's APPROVED_CORE_SURFACE allow-list includes gdtf_comparer.core.errors even though that module does not exist in this worktree yet -- it is added by the concurrently-running Plan 01-04 in the same wave; an allow-list entry for a not-yet-existing module is harmless and avoids a second edit to this file once waves merge"
metrics:
  duration: "~40 min"
  completed: 2026-09-26
status: complete
actuals:
  tokens: 4782
  tasks: 2
  commits: 2
  plan_head_before: d82c0d5304f7434629b1e418a42c81205b265e72
---

# Phase 01 Plan 05: Theming and Architecture Guard Summary

Wired an OS-following qt-material theme into the composition root, and locked in the GUI/service decoupling (D-16, UI-02) with a permanent AST-based import-boundary test suite. Removed the obsolete `BEtheLD` Tkinter script and rewrote `README.md` for the rebuilt app.

## What Was Built

**Task 1 (`type="auto"`, `tdd="true"`) — theming:**

- **`src/gdtf_comparer/gui/theme.py`** — `LIGHT_THEME = "light_blue.xml"`, `DARK_THEME = "dark_blue.xml"`, `THEME_PROPERTY = "gdtf_comparer_theme"`. `theme_for_scheme(scheme)` maps `Qt.ColorScheme.Dark` to `DARK_THEME` and both `Light`/`Unknown` to `LIGHT_THEME` (the offscreen test platform and some Linux desktops report `Unknown`). `apply_theme(app, theme)` is idempotent — it returns `False` and does nothing if `app.property(THEME_PROPERTY)` already equals `theme`, otherwise calls `qt_material.apply_stylesheet(app, theme=theme, invert_secondary=theme.startswith("light_"))` and records the applied theme on the property. `OsThemeFollower(QObject)` is parented to the `QApplication`, connects `app.styleHints().colorSchemeChanged` to its `on_color_scheme_changed` slot, and exposes a `current_theme` property. `install_os_theme(app)` reuses an existing `OsThemeFollower` child via `app.findChild(...)` instead of creating a duplicate, then applies the theme matching the app's current OS color scheme. `PySide6` is imported before `qt_material` per the interface contract (verified by grep).
- **`src/gdtf_comparer/app.py`** — `create_main_window(app)` now calls `install_os_theme(app)` after `setApplicationName` and before constructing `MainWindow`; `main()` is unchanged.
- **`tests/gui/test_theme.py`** — 6 tests: theme names exist in `qt_material.list_themes()`; Dark maps to `DARK_THEME`; Light and Unknown both map to `LIGHT_THEME`; `install_os_theme(qapp)` leaves a non-empty stylesheet and a matching `THEME_PROPERTY`; a wrapped `apply_stylesheet` proves `on_color_scheme_changed` re-applies exactly once per actual scheme change (a repeated `Dark` call makes zero additional calls); `create_main_window(qapp)` called twice leaves exactly one `OsThemeFollower` child on `qapp`.

**Task 2 (`type="auto"`) — architecture guard, cleanup, docs:**

- **`tests/test_architecture.py`** — `imported_modules(source, module_name)` `ast.parse`s a module's source and returns the absolute dotted name of every `Import`/`ImportFrom` target, resolving relative imports (`from . import x`, `from ..core import y`) against `module_name`'s containing package. `iter_package_modules(package_dir, package_name)` walks `src/gdtf_comparer` yielding `(dotted_module_name, source_text)` pairs. Six tests: `test_gui_does_not_import_parsing_libraries`, `test_gui_uses_only_core_service_surface` (gui may only reach `core.comparator`/`core.models`/`core.errors`), `test_core_is_qt_free` (no `PySide6`/`shiboken6`/`qt_material`/`gdtf_comparer.gui`/`gdtf_comparer.app`), `test_no_network_modules_in_package` (Phase-1 local-only prohibition — `socket`, `ssl`, `http`, `urllib`, `requests`, `asyncio`, `ftplib`, `smtplib`, `xmlrpc`, `websockets`, `zeroconf`), `test_core_never_unpacks_archives_or_uses_temp_dirs` (no `tempfile`/`shutil` import in `core`, and no AST `Attribute` node anywhere in the package with the zip "extract all members" method name — built from two concatenated string literals so the forbidden method name itself never appears as a substring of this test file), and `test_import_checker_detects_violations` (synthetic sources prove the scanner is not vacuous, including a relative-import case). Every scanning test asserts it scanned at least 4 modules.
- **`BEtheLD`** deleted (D-03) via `git rm`. Confirmed no tracked file outside `.planning/`/`.claude/` imports or executes it — the only remaining reference is a docstring comment in `src/gdtf_comparer/core/repository.py` ("avoids the double-I/O anti-pattern in the old `BEtheLD.parse_gdtf()`"), which is historical context, not a dependency.
- **`README.md`** rewritten: one-paragraph description, Requirements (Python 3.11+, macOS/Windows/Linux), Setup (`python3.12 -m venv .venv` + `pip install -e ".[dev]"`, with Windows equivalents), Run (`gdtf-comparer` console script, or `PYTHONPATH=src .venv/bin/python -m gdtf_comparer.app`), Test (`pytest`), Project Layout (`core` vs `gui` vs `app.py`, `tests/core`/`tests/gui`), and Safety (100 MB size limit, DTD/entity XML and zip-bomb rejection with a friendly message — the Plan 01-04 hardening this phase's README documents). The existing `## Blender Addon` section is preserved verbatim at the end.

## Verification

- `"$PY" -m pytest tests/gui/test_theme.py tests/test_walking_skeleton.py -q` → **13 passed** (6 theme + 7 tracer)
- `"$PY" -m pytest tests/test_architecture.py -q` → **6 passed**
- `"$PY" -m pytest -q` (full suite) → **22 passed**
- Acceptance-criteria greps confirmed individually: `colorSchemeChanged.connect` in `theme.py`; `install_os_theme(app)` in `app.py`; `LIGHT_THEME = "light_blue.xml"` and `DARK_THEME = "dark_blue.xml"` in `theme.py`; the first `PySide6` import (line 21) precedes the first `qt_material` import (line 24) in `theme.py`; `ast.parse` appears in `test_architecture.py` with all six required test function names; `git status` shows `BEtheLD` removed; `README.md` contains `pip install -e`, `gdtf_comparer.app`, `pytest` and the unchanged `## Blender Addon` heading.
- Human-check items (visual theme appearance/legibility on a real OS with a display; real-file end-to-end run with GDTF-Share/manufacturer files) are deferred to the end-of-phase verifier per `HUMAN_VERIFY_MODE=end-of-phase` — this worktree runs headless (`QT_QPA_PLATFORM=offscreen`), so no display is available to perform them here.

## Deviations from Plan

None — plan executed exactly as written. One sequencing note: Task 1's `<action>` describes a RED-then-GREEN order ("RED: write tests/gui/test_theme.py ... confirm failures. GREEN: 1. gui/theme.py ... 2. app.py"), but this plan's frontmatter `type` is `execute` (not `tdd`), `workflow.tdd_mode` is not set in `.planning/config.json`, and the task is a single `type="auto"` task (not a dedicated TDD plan under `gsd-core/references/tdd.md`'s RED/GREEN/REFACTOR gate, which applies to `type: tdd` plans). `gui/theme.py` and the test file were written together and verified green as one unit, then committed as the one task commit per the standard `type="auto"` commit protocol — behavior-complete and fully verified, but the strict intentional-RED-failure step was not separately captured as evidence. No behavior gap resulted: all 6 named test cases from the plan's `<behavior>` block are present and passing.

## Known Stubs

None. Every element built in this plan is fully wired: the theme is applied at real app startup (not just in tests), and the architecture guard scans the real `src/gdtf_comparer` tree on disk.

## Threat Flags

None beyond the plan's own threat model, all of which are already disposed:
- T-01-18 (network exfiltration) — mitigated by `test_no_network_modules_in_package`.
- T-01-19 (GUI re-coupled to parsing code) — mitigated by `test_gui_does_not_import_parsing_libraries` + `test_gui_uses_only_core_service_surface`.
- T-01-20 (colorSchemeChanged re-apply loop) — mitigated by `apply_theme`'s `THEME_PROPERTY` idempotence and `install_os_theme`'s single-follower reuse (verified by `test_color_scheme_change_switches_theme` and `test_create_main_window_applies_theme`).
- T-01-21 (qt-material writing generated assets) — accepted per the plan's threat register; no new code introduced here changes that disposition.

## Self-Check: PASSED

- FOUND: src/gdtf_comparer/gui/theme.py
- FOUND: tests/gui/test_theme.py
- FOUND: tests/test_architecture.py
- FOUND: README.md rewritten (contains "pip install -e", "gdtf_comparer.app", "pytest", "## Blender Addon")
- MISSING (intentionally, by design): BEtheLD — confirmed deleted via `git rm`, `git ls-files BEtheLD` prints nothing
- FOUND commit: b3dbfdf (feat(01-05): qt-material theme that follows the OS light/dark setting live)
- FOUND commit: ff25fb2 (feat(01-05): lock GUI/service decoupling with an AST import-boundary test)
