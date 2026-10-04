---
phase: "03"
slug: "compare-profiles-export"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-04"
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 + pytest-qt 4.5.0 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths = ["tests"]`, `pythonpath = ["src"]`, `qt_api = "pyside6"`) |
| **Quick run command** | `python -m pytest tests/core/test_profile_repository.py tests/gui/test_profile_toolbar.py -x` |
| **Full suite command** | `python -m pytest` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/core/test_profile_repository.py tests/gui/test_profile_toolbar.py -x`
- **After every plan wave:** Run `python -m pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | TBD | ATTR-03 | — | N/A | unit | `pytest tests/core/test_profile_repository.py::test_save_and_load_round_trip -x` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | TBD | ATTR-03 | — | N/A | gui | `pytest tests/gui/test_profile_toolbar.py::test_load_profile_replaces_checked_set -x` | ❌ W0 | ⬜ pending |
| 03-01-03 | 01 | TBD | ATTR-03 | — | N/A | gui | `pytest tests/gui/test_profile_toolbar.py::test_save_existing_name_confirms_overwrite -x` | ❌ W0 | ⬜ pending |
| 03-01-04 | 01 | TBD | ATTR-03 | — | N/A | unit + gui | `pytest tests/core/test_profile_repository.py::test_rename_and_delete -x` | ❌ W0 | ⬜ pending |
| 03-01-05 | 01 | TBD | ATTR-03 | — | N/A | unit | `pytest tests/core/test_profile_repository.py::test_missing_attributes -x` | ❌ W0 | ⬜ pending |
| 03-01-06 | 01 | TBD | ATTR-03 | — | Typed error, not a crash, on corrupt input | unit | `pytest tests/core/test_profile_repository.py::test_corrupted_file_raises_typed_error -x` | ❌ W0 | ⬜ pending |

*Task IDs are placeholders — the planner assigns final plan/wave/task numbering; this table's commands and requirement coverage are authoritative, the ID column is reconciled once PLAN.md exists.*

---

## Wave 0 Requirements

- [ ] `tests/core/test_profile_repository.py` — covers ATTR-03's save/load/rename/delete/missing-attribute/corrupted-file behaviors; use `tmp_path` (built-in pytest fixture) as `ProfileRepository(base_dir=str(tmp_path))` so tests never touch the real user profile directory
- [ ] `tests/gui/test_profile_toolbar.py` — covers the toolbar wiring (D-02/D-03/D-04/D-07) using the existing `qtbot` fixture (pytest-qt), the same way every other `tests/gui/*.py` file does
- [ ] No new shared fixtures needed — `tmp_path` and `qtbot` are both already available project-wide

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
