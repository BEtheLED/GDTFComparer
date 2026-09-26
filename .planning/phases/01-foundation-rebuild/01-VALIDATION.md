---
phase: "01"
slug: "foundation-rebuild"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-25"
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (already used for `tests/test_parse_gdtf.py`) + pytest-qt 4.5.0 (new, for GUI/worker tests) |
| **Config file** | none — Wave 0 installs (`pyproject.toml` `[tool.pytest.ini_options]` or `pytest.ini`) |
| **Quick run command** | `pytest tests/core -x` |
| **Full suite command** | `pytest tests/` (requires a display or `QT_QPA_PLATFORM=offscreen` in CI) |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/core -x`
- **After every plan wave:** Run `pytest tests/`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD (planner) | TBD | TBD | PARSE-01 | — | Same-named attributes from different geometries/models don't collide | unit | `pytest tests/core/test_comparator.py::test_no_attribute_collision -x` | ❌ Wave 0 | ⬜ pending |
| TBD (planner) | TBD | TBD | PARSE-01 | — | pygdtf-backed load returns a structured `FixtureModel` | unit | `pytest tests/core/test_repository.py::test_load_valid_gdtf -x` | ❌ Wave 0 | ⬜ pending |
| TBD (planner) | TBD | TBD | RELI-01 | V5 / V10 | Malformed XML inside a valid zip is caught before reaching pygdtf's silent-fallback behavior | unit | `pytest tests/core/test_hardening.py::test_malformed_xml_raises -x` | ❌ Wave 0 | ⬜ pending |
| TBD (planner) | TBD | TBD | RELI-01 | — | Invalid/non-zip file raises a catchable error | unit | `pytest tests/core/test_repository.py::test_invalid_zip_raises -x` | ❌ Wave 0 | ⬜ pending |
| TBD (planner) | TBD | TBD | RELI-02 | V10 / V12 | Oversized file / bad compression ratio is rejected before parsing | unit | `pytest tests/core/test_hardening.py::test_oversized_file_rejected -x` | ❌ Wave 0 | ⬜ pending |
| TBD (planner) | TBD | TBD | RELI-02 | V5 (XXE) | XXE/entity-expansion payload is rejected | unit | `pytest tests/core/test_hardening.py::test_xxe_rejected -x` | ❌ Wave 0 | ⬜ pending |
| TBD (planner) | TBD | TBD | UI-02 | — | `gui/` package contains no direct `import pygdtf` or `import zipfile` | static/lint check | `grep -rn "import pygdtf\|import zipfile" src/gui/` (expect empty) | ❌ Wave 0 | ⬜ pending |
| TBD (planner) | TBD | TBD | UI-01 | — | App launches with qt-material theme applied, no stock-Tkinter look | manual-only | Manual smoke test (purely visual, no automatable "looks modern" assertion) | n/a | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `pyproject.toml` with `[tool.pytest.ini_options]` (`testpaths = ["tests"]`) — no config file exists yet
- [ ] `tests/core/__init__.py`, `tests/gui/__init__.py` — new test package structure replacing the current single `tests/test_parse_gdtf.py`
- [ ] `tests/core/conftest.py` — shared fixtures for building minimal valid/malformed/oversized `.gdtf` zips in `tmp_path`, following the existing `build_gdtf_zip()` helper pattern already in `tests/test_parse_gdtf.py`
- [ ] Framework install: `pip install -D pytest-qt==4.5.0` — needed before any `tests/gui/` tests can run
- [ ] Decide fate of `tests/test_parse_gdtf.py` — it tests the old `BEtheLD.parse_gdtf()` function being removed this phase; should be deleted/replaced by `tests/core/test_repository.py`, not left dangling against dead code

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| App has a modernized, visually refreshed look (qt-material theme, no stock Tkinter appearance) | UI-01 | Purely visual — no automatable "looks modern" assertion | Launch app, confirm qt-material stylesheet is applied and no native Tk widgets are visible |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
