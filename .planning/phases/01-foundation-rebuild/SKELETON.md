# Walking Skeleton — GDTF Comparer

**Phase:** 1 (Foundation Rebuild)
**Generated:** 2026-09-25
**Skeleton plans:** 01-01 (gated toolchain + scaffold) -> 01-02 (end-to-end `type="tracer"`). Plans 01-03..01-05 are expansion slices layered on this skeleton without changing any decision below.

## Capability Proven End-to-End

A user launches the rebuilt app locally, picks a target `.gdtf` and one or more comparison `.gdtf` files, clicks **Run Comparison**, and sees a comparison table whose values were parsed by pygdtf and compared by the Qt-free core service on a background thread.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| GUI framework | PySide6 6.11.2 (Qt for Python): `QMainWindow` + `QAbstractTableModel`/`QTableView` | D-01 (one-way, user-chosen): model/view scales to Phase 2 sort/filter/highlight; LGPL; mature PyInstaller hooks for Phase 4 |
| Runtime | CPython `>=3.11` (`requires-python`); dev venv on 3.12 | D-02: floor required by PySide6 6.11 / Phase 5 `websockets`; conda base 3.14 avoided (near PySide6's `<3.15` ceiling) |
| GDTF parsing | pygdtf 1.4.5 behind `core.repository.FixtureRepository.load(path)` | PARSE-01 / D-09: spec-correct object model; the full `FixtureType` is retained on `FixtureModel.fixture_type` |
| Data layer / persistence | None. Read-only local files; nothing is written to disk (no temp extraction) | Comparison tool, not an editor; closes CONCERNS.md temp-dir and double-I/O issues |
| Service API | `core.comparator.compare_files(target_path, compare_paths) -> ComparisonResult` | D-13 typed result + D-15 batch API; the ONLY core call the GUI makes |
| Attribute identity | `AttributeKey(category, element_path, attribute)`; Beam path = geometry names joined by `/`, model rows keyed by model name, Weight at fixture level (`""`); duplicates get `#N` | D-11 (Claude's discretion on format): fixes the flat-dict collision bug; stable row identity for Phase 2/3 |
| Display scope | Categories `Beam` and `Physical Properties` only | D-10 |
| Threading | One `ComparisonWorker(QObject)` moved to a parented `QThread` per run; results via `comparison_ready`/`comparison_failed` signals; Run disabled until the thread stops | D-14: no UI freeze, no cross-thread widget access, no concurrent runs |
| Input hardening | `core.hardening.prevalidate_gdtf` (size limits, zip-bomb checks, defusedxml with DTD/entities forbidden) runs before pygdtf; pygdtf parses the validated in-memory bytes | RELI-02 + RESEARCH Pitfall 1 (pygdtf swallows malformed XML) — added by Plan 01-04 inside the same `load()` call site |
| Error model | `GDTFError` hierarchy with `user_message`; mapped to a plain-text `QMessageBox` at the worker boundary | RELI-01 / D-12 |
| Theming | qt-material `dark_blue.xml` / `light_blue.xml`, chosen from `QStyleHints.colorScheme()` and re-applied on `colorSchemeChanged` | D-05/D-06/D-07/D-08 — added by Plan 01-05 at the composition root |
| Auth | None — single-user local desktop app | No accounts, sessions or network in Phase 1 |
| Deployment target | Local run: `PYTHONPATH=src .venv/bin/python -m gdtf_comparer.app` from the repo root, or the `gdtf-comparer` gui-script after `pip install -e ".[dev]"` | Standalone macOS/Windows builds are Phase 4 (PKG-01..03) |
| Directory layout | `src/gdtf_comparer/{core,gui}/`, `src/gdtf_comparer/app.py` composition root; `tests/core`, `tests/gui`, root-level cross-cutting tests | D-04/D-16: `core` never imports Qt; `gui` imports only `core.comparator`, `core.models`, `core.errors` (enforced by `tests/test_architecture.py`) |
| Test harness | pytest 9.1.1 + pytest-qt 4.5.0; `--import-mode=importlib`, `pythonpath=["src"]`, `QT_QPA_PLATFORM=offscreen`; `make_gdtf` fixture builds real `.gdtf` archives | Tests always import the checkout's own `src/`, including inside git worktrees |
| Dev environment | ONE shared venv at the main checkout's `.venv`, resolved from any worktree as `$(git rev-parse --path-format=absolute --git-common-dir)/../.venv` | Worktree-safe execution without duplicate installs |

## Stack Touched in Phase 1

- [x] Project scaffold — pyproject (pinned deps, setuptools src layout), pytest + pytest-qt config, .gitignore (Plan 01-01)
- [x] Routing — N/A for a single-window desktop app; the one "route" is `MainWindow` built by `app.create_main_window` (Plan 01-02)
- [x] Data read — one real pygdtf read of a real `.gdtf` archive per selected file (Plan 01-02). Data write: intentionally none — the tool is read-only by design
- [x] UI — file pickers + Run Comparison wired through the QThread worker to the core service, rendering a `QTableView` (Plan 01-02)
- [x] Deployment — documented local full-stack run command, exercised by `test_app_module_launches` (Plan 01-02) and documented in README (Plan 01-05)

## Symbols by Plan (phase-wide index)

| Plan | Creates |
|---|---|
| 01-01 | `pyproject.toml`, `.gitignore`, `gdtf_comparer.__version__`, `tests/conftest.py::build_description_xml`, fixture `make_gdtf`, `tests/test_fixture_builder.py` |
| 01-02 | `AttributeKey`, `FixtureModel`, `ComparisonRow`, `ComparisonResult`, `CATEGORY_BEAM`, `CATEGORY_PHYSICAL`, `DISPLAY_CATEGORIES`, `FIXTURE_LEVEL_PATH`, `format_value`, `values_equal`, `extract_attributes`, `FixtureRepository.load`, `compare`, `compare_files`, `ComparisonWorker` (+ signals), `ComparisonTableModel` (+ `find_row`), `MainWindow`, `create_main_window`, `main`, `tests/test_walking_skeleton.py` |
| 01-03 | `BEAM_ATTRIBUTES`, `MODEL_ATTRIBUTES`, `PATH_SEPARATOR`, `UNNAMED_GEOMETRY`, `iter_geometry_paths`, `_unique_path`, `tests/core/test_extract.py`, `tests/core/test_comparator.py`, `tests/gui/test_namespaced_rows.py` |
| 01-04 | `GDTFError`, `GDTFValidationError`, `GDTFUnsafeFileError`, `GDTFParseError`, hardening limits + `read_gdtf_bytes`, `extract_description_bytes`, `parse_description_safely`, `prevalidate_gdtf`, `PYGDTF_BROKEN_XML_STUB_NAME`, `tests/core/test_hardening.py`, `tests/core/test_repository.py`, `tests/gui/test_error_handling.py` |
| 01-05 | `LIGHT_THEME`, `DARK_THEME`, `THEME_PROPERTY`, `theme_for_scheme`, `apply_theme`, `OsThemeFollower`, `install_os_theme`, `tests/gui/test_theme.py`, `tests/test_architecture.py`, rewritten `README.md` |

**Deleted by this phase:** `tests/test_parse_gdtf.py` (Plan 01-01 — tkinter-bound test of dead code), `BEtheLD` (Plan 01-05 — superseded by the rewrite, D-03).

## Out of Scope (Deferred to Later Slices)

- Browsing/searching the full 60+ GDTF attribute set and choosing attributes (Phase 2: ATTR-01, ATTR-02)
- Visual diff highlighting in the table (Phase 2: DIFF-01) — `ComparisonRow.differs` is computed now but not rendered
- Compare profiles and CSV export (Phase 3: ATTR-03, EXPORT-01, EXPORT-02)
- Standalone packaging, signing, notarization (Phase 4: PKG-01..03)
- MVR parsing and MVR-xchange networking (Phase 5: PARSE-02, NET-01..03) — Phase 1 is local-only and test-enforced
- Command-line interface, parsed-file caching, the Blender addon

## Subsequent Slice Plan

Each later phase adds one vertical slice on top of this skeleton without altering its architectural decisions:

- Phase 2: user browses/filters all GDTF attributes (from `FixtureModel.fixture_type`) and sees differing values highlighted (from `ComparisonRow.differs`)
- Phase 3: user saves named attribute selections (keyed by `AttributeKey`) and exports full / diff-only CSV from `ComparisonResult`
- Phase 4: user downloads a signed standalone macOS/Windows build (PyInstaller over `gdtf_comparer.app:main`)
- Phase 5: user pulls MVR fixtures from LAN MVR-xchange peers into the same `compare_files`-style workflow (network rule in `tests/test_architecture.py` amended deliberately)
