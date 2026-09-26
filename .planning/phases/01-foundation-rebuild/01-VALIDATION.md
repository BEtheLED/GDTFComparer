---
phase: "01"
slug: "foundation-rebuild"
status: draft
nyquist_compliant: true
wave_0_complete: false
created: "2026-09-25"
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 + pytest-qt 4.5.0 (installed by Plan 01-01 into the shared `.venv`) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]`: `testpaths=["tests"]`, `pythonpath=["src"]`, `addopts="--import-mode=importlib -ra"`, `qt_api="pyside6"` (created by 01-01-T2) |
| **Quick run command** | `$PY -m pytest tests/core -x -q` |
| **Full suite command** | `$PY -m pytest -q` (tests/conftest.py sets `QT_QPA_PLATFORM=offscreen`, so no display is needed) |
| **Estimated runtime** | ~15 seconds (includes a ~3 s app-launch smoke test) |

---

## Sampling Rate

- **After every task commit:** Run the task's `<automated>` command (quick: `$PY -m pytest tests/core -x -q` once tests/core exists)
- **After every plan wave:** Run `$PY -m pytest -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

`$PY` below = `"$(git rev-parse --path-format=absolute --git-common-dir)/../.venv/bin/python"` (the ONE shared venv in the main checkout, created by 01-01-T2); run every command from `cd "$(git rev-parse --show-toplevel)"`.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-T1 | 01-01 | 1 | (gate) | T-01-SC | No package installed before human legitimacy approval | checkpoint (blocking-human) | n/a — human gate | n/a | ⬜ pending |
| 01-01-T2 | 01-01 | 1 | UI-02 (layout), D-02 | T-01-SC, T-01-02 | Pinned toolchain in isolated venv; builder output parses with pygdtf | smoke | `$PY -m pytest tests/test_fixture_builder.py -q` | ❌ created by 01-01-T2 | ⬜ pending |
| 01-02-T1 | 01-02 | 2 | PARSE-01, UI-02 | T-01-04, T-01-05, T-01-06 | pick files -> QThread worker -> core.compare_files -> pygdtf -> table; core imports without Qt | integration (pytest-qt) | `$PY -m pytest tests/test_walking_skeleton.py -q` | ❌ created by 01-02-T1 | ⬜ pending |
| 01-02-T1 | 01-02 | 2 | UI-02 | — | gui has no parsing-library imports; core has no Qt imports | static | `! grep -rEq '^[[:space:]]*(from\|import)[[:space:]]+(pygdtf\|zipfile\|defusedxml)' src/gdtf_comparer/gui` | n/a | ⬜ pending |
| 01-03-T1 | 01-03 | 3 | PARSE-01 | T-01-08 | Same-named attributes from different geometries don't collide | unit | `$PY -m pytest tests/core/test_comparator.py::test_no_attribute_collision -q` | ❌ created by 01-03-T1 | ⬜ pending |
| 01-03-T2 | 01-03 | 3 | PARSE-01 | T-01-07 | Per-model dimensions + single Weight; namespaced rows render in the app | unit + pytest-qt | `$PY -m pytest tests/core/test_extract.py tests/gui/test_namespaced_rows.py -q` | ❌ created by 01-03 | ⬜ pending |
| 01-04-T1 | 01-04 | 3 | PARSE-01, RELI-01 | T-01-16 | pygdtf-backed load returns a structured `FixtureModel` | unit | `$PY -m pytest tests/core/test_repository.py::test_load_valid_gdtf -q` | ❌ created by 01-04-T1 | ⬜ pending |
| 01-04-T1 | 01-04 | 3 | RELI-01 | T-01-16 (V5/V10) | Malformed XML inside a valid zip is caught before reaching pygdtf's silent-fallback behavior | unit | `$PY -m pytest tests/core/test_hardening.py::test_malformed_xml_raises -q` | ❌ created by 01-04-T1 | ⬜ pending |
| 01-04-T1 | 01-04 | 3 | RELI-01 | — | Invalid/non-zip file raises a catchable, friendly error | unit | `$PY -m pytest tests/core/test_repository.py::test_invalid_zip_raises -q` | ❌ created by 01-04-T1 | ⬜ pending |
| 01-04-T1 | 01-04 | 3 | RELI-02 | T-01-12, T-01-13 (V10/V12) | Oversized file / bad compression ratio is rejected before parsing | unit | `$PY -m pytest tests/core/test_hardening.py::test_oversized_file_rejected tests/core/test_hardening.py::test_compression_ratio_rejected -q` | ❌ created by 01-04-T1 | ⬜ pending |
| 01-04-T1 | 01-04 | 3 | RELI-02 | T-01-10, T-01-11 (V5 XXE) | XXE/entity-expansion payload is rejected | unit | `$PY -m pytest tests/core/test_hardening.py::test_xxe_rejected tests/core/test_hardening.py::test_billion_laughs_rejected -q` | ❌ created by 01-04-T1 | ⬜ pending |
| 01-04-T2 | 01-04 | 3 | RELI-01 | T-01-17 | Friendly plain-text dialog naming the bad file; no partial table; app usable after error | pytest-qt | `$PY -m pytest tests/gui/test_error_handling.py -q` | ❌ created by 01-04-T2 | ⬜ pending |
| 01-05-T1 | 01-05 | 3 | UI-01 | T-01-20 | qt-material theme applied at startup, follows OS light/dark live | pytest-qt + human-check | `$PY -m pytest tests/gui/test_theme.py -q` | ❌ created by 01-05-T1 | ⬜ pending |
| 01-05-T2 | 01-05 | 3 | UI-02 | T-01-18, T-01-19 | gui imports only core.comparator/models/errors; core is Qt-free; no network modules (AST, non-vacuous) | static (AST test) | `$PY -m pytest tests/test_architecture.py -q` | ❌ created by 01-05-T2 | ⬜ pending |
| 01-05-T1 | 01-05 | 3 | UI-01 | — | App has a modernized look (not stock Tk) | manual-only (`<human-check>`) | End-of-phase UAT: launch app in Light and Dark appearance | n/a | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

All Wave 0 items are owned by Plan 01-01 Task 2 (executes after the blocking-human legitimacy checkpoint, 01-01-T1):

- [ ] `pyproject.toml` with `[tool.pytest.ini_options]` (`testpaths`, `pythonpath=["src"]`, `--import-mode=importlib`, `qt_api="pyside6"`) — 01-01-T2
- [ ] Test package structure: `tests/core/` and `tests/gui/` WITHOUT `__init__.py` (importlib import mode allows duplicate basenames and avoids a `core` package-name clash) — directories are created by the first plan writing into them (01-03 / 01-04 / 01-05)
- [ ] `tests/conftest.py` (root, shared by core + gui tests) — `make_gdtf` factory fixture following the old `build_gdtf_zip()` pattern, plus `QT_QPA_PLATFORM=offscreen` default — 01-01-T2; malformed/malicious/oversized variants are built per-test via its `description`/`extra_members` parameters and monkeypatched limits (01-04)
- [ ] Framework install: `pip install -e ".[dev]"` into the shared `.venv` (pytest 9.1.1, pytest-qt 4.5.0 + runtime pins) — 01-01-T2
- [x] Fate of `tests/test_parse_gdtf.py` decided: deleted in 01-01-T2 (it cannot even import under the tkinter-less 3.12 venv); its behaviours are re-covered by 01-02 (valid parse), `tests/core/test_repository.py::test_invalid_zip_raises` and `tests/core/test_hardening.py::test_malformed_xml_raises` (01-04)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| App has a modernized, visually refreshed look (qt-material theme, no stock Tkinter appearance), re-themes live on OS Light/Dark switch | UI-01 | Purely visual — no automatable "looks modern" assertion | `<human-check>` in 01-05-T1: launch `PYTHONPATH=src .venv/bin/python -m gdtf_comparer.app`, toggle macOS Appearance Light/Dark |
| Real-world GDTF files compare correctly end to end; renamed non-GDTF shows friendly dialog | PARSE-01, RELI-01 | Real fixture variety (multi-emitter, many models) is not representable by synthetic fixtures | `<human-check>` in 01-05-T2: follow README, compare real GDTF-Share / manufacturer files, then a renamed non-GDTF file |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies (only 01-01-T1, the blocking-human legitimacy gate, has none by design)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [ ] Feedback latency < 15s (full suite estimated ~15 s including the 3 s launch smoke test — confirm after 01-02)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
