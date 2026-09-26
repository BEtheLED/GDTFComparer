---
phase: 01-foundation-rebuild
plan: 02
subsystem: walking-skeleton-tracer
tags: [pygdtf, pyside6, qthread, comparison-service, tracer]
dependency graph:
  requires:
    - "01-01 (pyproject.toml, src-layout package skeleton, shared .venv, make_gdtf fixture)"
  provides:
    - "core.models: AttributeKey, FixtureModel, ComparisonRow, ComparisonResult, CATEGORY_BEAM, CATEGORY_PHYSICAL, DISPLAY_CATEGORIES, FIXTURE_LEVEL_PATH, format_value, values_equal"
    - "core.extract.extract_attributes(fixture_type)"
    - "core.repository.FixtureRepository.load(path)"
    - "core.comparator.compare(target, comparisons) / compare_files(target_path, compare_paths, repository=None)"
    - "gui.worker.ComparisonWorker (comparison_ready/comparison_failed signals)"
    - "gui.table_model.ComparisonTableModel (find_row)"
    - "gui.main_window.MainWindow"
    - "app.create_main_window(app) / app.main(argv)"
    - "documented local run command: PYTHONPATH=src .venv/bin/python -m gdtf_comparer.app"
  affects:
    - "01-03 (fills extract_attributes with per-GeometryBeam and per-Model keys, no other file touched)"
    - "01-04 (inserts hardening + typed errors inside FixtureRepository.load and the worker)"
    - "01-05 (adds theming at the app.py composition root)"
tech-stack:
  added: []
  patterns:
    - "core/ package has zero Qt imports (D-16), verified by grep in the same verify block that runs pytest"
    - "QThread worker pattern: ComparisonWorker(QObject) moved to a QThread(self)-parented thread; run_button re-enabled only in _on_thread_finished so two comparisons can never overlap (D-14)"
    - "AttributeKey(category, element_path, attribute) namespaced keying (D-11); Weight is the only key this tracer produces, at FIXTURE_LEVEL_PATH"
    - "compare_files(target_path, compare_paths, repository=None) is the one batch service call the GUI makes (D-15); repository is injectable for tests"
key-files:
  created:
    - src/gdtf_comparer/core/models.py
    - src/gdtf_comparer/core/extract.py
    - src/gdtf_comparer/core/repository.py
    - src/gdtf_comparer/core/comparator.py
    - src/gdtf_comparer/gui/worker.py
    - src/gdtf_comparer/gui/table_model.py
    - src/gdtf_comparer/gui/main_window.py
    - src/gdtf_comparer/app.py
    - tests/test_walking_skeleton.py
  modified: []
  deleted: []
decisions:
  - "Confirmed the installed pygdtf 1.4.5 FixtureType defines __enter__/__exit__ (reads __init__.py:167-172 directly) -- used `with pygdtf.FixtureType(path) as fixture_type:` in FixtureRepository.load, no finally-block fallback was needed"
  - "Confirmed fixture_type.properties defaults to a Properties() instance (weight=0.0) whenever <PhysicalDescriptions> is present but <Weight> is absent, and stays None only when <PhysicalDescriptions> itself is absent -- extract_attributes handles both (properties is None -> Weight None; weight attribute present -> float(weight))"
metrics:
  duration: "~35 min"
  completed: 2026-09-26
status: complete
actuals:
  tokens: 8630
  tasks: 1
  commits: 1
  plan_head_before: 57ca33d741d53d2d080138569e0b89d1991003ae
---

# Phase 01 Plan 02: Walking-Skeleton Tracer Summary

Built the whole rebuilt architecture end to end on one thin path: `MainWindow` file pickers -> `ComparisonWorker` on a `QThread` -> Qt-free `core.comparator.compare_files` -> `pygdtf.FixtureType` -> a typed `ComparisonResult` -> `QAbstractTableModel` rendering the fixture-level Physical Properties / Weight comparison row.

## What Was Built

**Task 1 (type="tracer") — the only task in this plan, executed and committed as a single unit:**

- **`core/models.py`** — `AttributeKey` (category, element_path, attribute) with `element_label` returning `"Fixture"` at `FIXTURE_LEVEL_PATH`; `FixtureModel` (source_path, name, manufacturer, attributes, `fixture_type` retained verbatim per D-09 with `repr=False, compare=False`) with `file_name` property; `ComparisonRow` with `any_differs`; `ComparisonResult`; `format_value` (None -> "N/A", float via `.10g`, int via `str`, str passthrough); `values_equal` (both-None -> True, one-None -> False, numeric via `math.isclose(rel_tol=1e-9, abs_tol=1e-12)`, else `==`). Zero Qt imports, no module-level mutable state.
- **`core/extract.py`** — `extract_attributes(fixture_type)` returns exactly one key this tracer needs: `AttributeKey(CATEGORY_PHYSICAL, FIXTURE_LEVEL_PATH, "Weight")` -> `float(fixture_type.properties.weight)`, or `None` when `properties` itself is `None`.
- **`core/repository.py`** — `FixtureRepository.load(path)` opens `pygdtf.FixtureType(path)` as a context manager (verified against the installed 1.4.5 source that `__enter__`/`__exit__` exist and close the zip on exit), calls `extract_attributes` inside the `with` block, returns a `FixtureModel`. Reads the archive in place; no temp-dir copy/extract. Errors propagate unchanged (Plan 01-04 adds pre-validation).
- **`core/comparator.py`** — `compare(target, comparisons)` builds the ordered key list from target then each comparison (first-seen order, no duplicates), filters to `DISPLAY_CATEGORIES`, stable-sorts by category index, and builds one `ComparisonRow` per key. `compare_files(target_path, compare_paths, repository=None)` is the D-15 batch service API and the only core call the GUI makes; any load error propagates, never a partial result.
- **`gui/worker.py`** — `ComparisonWorker(QObject)` imports `compare_files` at module level (so tests can monkeypatch `gdtf_comparer.gui.worker.compare_files`); `run()` never touches a widget, emits `comparison_ready(result)` or `comparison_failed(message)`.
- **`gui/table_model.py`** — `ComparisonTableModel(QAbstractTableModel)` with `COL_CATEGORY/COL_ELEMENT/COL_ATTRIBUTE/COL_TARGET`, `set_result`/`result`, DisplayRole/ToolTipRole `data()` and `headerData()` (target header shows `"Target: <file_name>"`; comparison headers show each file's basename; ToolTip shows `"<name> — <source_path>"`), `flags()` enabled+selectable, `find_row(category, element_path, attribute)`.
- **`gui/main_window.py`** — `MainWindow(QMainWindow)`: "Files" `QGroupBox`/`QGridLayout` with target row (read-only `target_edit`, placeholder "No target selected", `target_button` "Browse…") and compare row (`compare_list` `QListWidget` with `ExtendedSelection`, basenames shown + full path as tooltip + `Qt.UserRole` data, `add_button`/`remove_button` column); right-aligned `run_button`; `table_view` (`QTableView`, alternating rows, row selection, hidden vertical header, last section stretches); status bar starting at "Ready". `run_comparison()` guards against a running comparison and missing target/compare files, then builds `QThread(self)` + `ComparisonWorker`, wires `thread.started -> worker.run`, both worker signals `-> thread.quit`, `thread.finished -> worker.deleteLater / thread.deleteLater / _on_thread_finished`. `run_button.setEnabled(True)` appears exactly once, inside `_on_thread_finished`, so a second run cannot start while the old thread is alive (D-14). `closeEvent` quits and waits the thread before closing.
- **`app.py`** — `create_main_window(app)` sets the application name and returns a new `MainWindow`; `main(argv=None)` reuses or creates the `QApplication`, shows the window, and returns `app.exec()`; documented local run command `PYTHONPATH=src .venv/bin/python -m gdtf_comparer.app`.
- **`tests/test_walking_skeleton.py`** — 7 tests: `test_compare_files_headless` (weight diff row + `fixture_type.dmx_modes`/`geometries` retained), `test_core_imports_without_qt` (subprocess proves `PySide6` never gets imported by `core`), `test_gui_run_comparison_populates_table` (full UI flow via `qtbot`, checks cell values and headers), `test_comparison_runs_off_ui_thread` (records `threading.get_ident()` inside the monkeypatched `compare_files` and asserts it differs from the test thread), `test_run_button_disabled_until_worker_thread_stops`, `test_close_during_comparison_does_not_crash` (slow-wrapped `compare_files`, closes mid-run), `test_app_module_launches` (subprocess stays alive 3s under `QT_QPA_PLATFORM=offscreen`, then terminated/waited/killed).

## Verification

- `"$PY" -m pytest tests/test_walking_skeleton.py -q` -> **7 passed**
- `"$PY" -m pytest -q` (full suite, includes `tests/test_fixture_builder.py`) -> **10 passed**
- Import-boundary greps: `gui/` contains no `pygdtf`/`zipfile`/`defusedxml` imports; `core/` contains no `PySide6`/`shiboken6`/`qt_material` imports -> both clean
- All plan acceptance-criteria greps confirmed individually: `pygdtf.FixtureType` in `repository.py`, `def compare_files` in `comparator.py`, the worker's module-level `compare_files` import, `moveToThread`/`QThread(self)` in `main_window.py`, `class ComparisonResult`/`class AttributeKey` in `models.py`, and exactly one `run_button.setEnabled(True)` occurrence (inside `_on_thread_finished`)
- Tracer feedback gate: task carries no `gate="blocking-human"`; auto-chain/auto-advance are both off in `.planning/config.json` and `HUMAN_VERIFY_MODE` is the default `end-of-phase`; the task's `<verify>` block is fully automated, so it was re-run end-to-end per the interactive/automated-only branch — all three commands passed, logged, and execution continued with no checkpoint (this plan has only the one task, so no expansion task followed)

## Deviations from Plan

None — plan executed exactly as written. Two facts flagged as "confirm against the installed pygdtf" in the plan's `read_first`/interfaces were verified directly against `/Users/brandon/GDTFComparer/.venv/lib/python3.12/site-packages/pygdtf/{__init__.py,properties.py}` before writing `repository.py`/`extract.py` (see Decisions above); both matched the plan's assumptions, so no code deviated from the written contract.

## Known Stubs

None. Every UI element on this path is wired to a real pygdtf-parsed value; nothing renders a hardcoded empty/placeholder value.

## Threat Flags

None beyond what the plan's own threat model already tracks (T-01-03..T-01-06, all disposed to Plan 01-04 or already mitigated by the QThread design built here). This plan introduced no new trust-boundary surface.

## Self-Check: PASSED

- FOUND: src/gdtf_comparer/core/models.py
- FOUND: src/gdtf_comparer/core/extract.py
- FOUND: src/gdtf_comparer/core/repository.py
- FOUND: src/gdtf_comparer/core/comparator.py
- FOUND: src/gdtf_comparer/gui/worker.py
- FOUND: src/gdtf_comparer/gui/table_model.py
- FOUND: src/gdtf_comparer/gui/main_window.py
- FOUND: src/gdtf_comparer/app.py
- FOUND: tests/test_walking_skeleton.py
- FOUND commit: 5b292ee (feat(01-02): walking-skeleton tracer for GDTF compare end to end)
