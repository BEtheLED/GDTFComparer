---
phase: "03"
slug: "compare-profiles-export"
status: validated
nyquist_compliant: true
wave_0_complete: true
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

| Task ID | Plan | Requirement | Secure Behavior | Test Type | Automated Command (abbreviated) | Status |
|---------|------|-------------|-----------------|-----------|----------------------------------|--------|
| 03-01-T1 | 01 | ATTR-03 | N/A | unit + gui | `pytest tests/gui/test_profile_toolbar.py -q` | ✅ COVERED |
| 03-01-T2 | 01 | ATTR-03 | Save-over-existing-name confirms before overwrite | unit + gui | `pytest tests/core/test_profile_repository.py tests/gui/test_profile_toolbar.py -q` | ✅ COVERED |
| 03-01-T3 | 01 | ATTR-03 | Typed error, not a crash, on corrupt/failed-save profiles file | unit + gui | `pytest tests/core/test_profile_repository.py tests/gui/test_profile_toolbar.py -q` | ✅ COVERED |
| 03-02-T1 | 02 | ATTR-03 | N/A | unit + gui | `pytest tests/core/test_profile_repository.py tests/gui/test_profile_portability.py -q` | ✅ COVERED |
| 03-02-T2 | 02 | ATTR-03 | N/A | gui | `pytest tests/gui/test_profile_portability.py tests/gui/test_differences_only_toggle.py -q` | ✅ COVERED |
| 03-03-T1 | 03 | ATTR-03 | N/A | unit + gui | `pytest tests/core/test_profile_repository.py tests/gui/test_profile_manage.py -q` | ✅ COVERED |
| 03-03-T2 | 03 | ATTR-03 | Delete confirms first, then removes everywhere | unit + gui | `pytest tests/core/test_profile_repository.py tests/gui/test_profile_manage.py -q` | ✅ COVERED |
| 03-04-T1 (G-03-1) | 04 | ATTR-03 | N/A | gui | `pytest tests/gui/test_profile_toolbar.py tests/gui/test_profile_manage.py -q` | ✅ COVERED |
| 03-04-T2 (G-03-2) | 04 | ATTR-03 | N/A | gui | `pytest tests/gui/test_compare_list_match_indicator.py -q` | ✅ COVERED |
| 03-05-T1 (G-03-3) | 05 | ATTR-03 | N/A | unit + gui | `pytest tests/core/test_comparator.py tests/gui/test_cross_fixture_rows.py -q` | ✅ COVERED |
| 03-05-T2 (G-03-3) | 05 | ATTR-03 | N/A | unit + gui | `pytest tests/gui/test_namespaced_rows.py tests/gui/test_attribute_selection.py tests/gui/test_unspecified_values.py tests/gui/test_differences_only_toggle.py -q` | ✅ COVERED |

All 11 tasks across the 5 executed plans carry an `<automated>` verify command backed by a real,
existing test file (confirmed on disk, not just referenced). Full suite re-run as part of this
audit (2026-10-11): `.venv/bin/python -m pytest -q -W error::DeprecationWarning` → **276 passed**,
0 failed, 0 skipped. No gaps found — every requirement (ATTR-03) has automated coverage; no task
needed Nyquist auditor intervention.

---

## Wave 0 Requirements

- [x] `tests/core/test_profile_repository.py` — covers ATTR-03's save/load/rename/delete/missing-attribute/corrupted-file behaviors; uses `tmp_path` (built-in pytest fixture) as `ProfileRepository(base_dir=str(tmp_path))` so tests never touch the real user profile directory
- [x] `tests/gui/test_profile_toolbar.py` — covers the toolbar wiring (D-02/D-03/D-04/D-07) using the existing `qtbot` fixture (pytest-qt), the same way every other `tests/gui/*.py` file does
- [x] No new shared fixtures needed — `tmp_path` and `qtbot` are both already available project-wide

---

## Manual-Only Verifications

*All phase behaviors have automated verification.* The one item that required a human (re-running
the user's own real GDTF files through the live app to confirm gap G-03-3's fix) was tracked as a
UAT checkpoint rather than a Nyquist task — see `03-UAT.md` test 3 (passed 2026-10-11) and
`03-VERIFICATION.md`'s `human_verification` block.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated 2026-10-11 (retroactive audit via `/gsd-validate-phase`, dispatched from `/gsd-execute-phase 03`'s stale-verification re-run)

## Validation Audit

| Date | Gaps found | Resolved | Escalated |
|------|-----------|----------|-----------|
| 2026-10-11 | 0 | 0 | 0 |
