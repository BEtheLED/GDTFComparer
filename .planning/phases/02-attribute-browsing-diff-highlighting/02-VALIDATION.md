---
phase: "2"
slug: "attribute-browsing-diff-highlighting"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-29"
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 + pytest-qt 4.5.0 |
| **Config file** | none at repo root — pytest auto-discovers `tests/` (`tests/core/` and `tests/gui/` both scanned) |
| **Quick run command** | `pytest tests/core -x -q` (core-layer tasks, no Qt event loop) or `pytest tests/gui -x -q` (GUI-layer tasks; `QT_QPA_PLATFORM=offscreen` already set in `tests/conftest.py:5`) |
| **Full suite command** | `pytest -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/core -x -q` for core-layer tasks, or `pytest tests/gui/<touched_file>.py -x -q` for GUI-layer tasks
- **After every plan wave:** Run `pytest -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 0 | ATTR-01 | — | New category(ies) extracted with correct declared-vs-default presence semantics | unit | `pytest tests/core/test_extract.py -x -q` | ✅ (extend existing) | ⬜ pending |
| 02-01-02 | 01 | 0 | ATTR-01 | — | `compare()` no longer drops non-Beam/Physical rows | unit | `pytest tests/core/test_comparator.py -x -q` | ✅ (existing; needs `DISPLAY_CATEGORIES` fix) | ⬜ pending |
| 02-02-01 | 02 | 1 | ATTR-01 | — | Picker shows a section per category with checkable attribute rows, search narrows visibility only | gui | `pytest tests/gui/test_attribute_picker.py -x -q` | ❌ Wave 0 — new file | ⬜ pending |
| 02-02-02 | 02 | 1 | ATTR-02 | — | Only checked attributes appear in the results table | gui | `pytest tests/gui/test_attribute_selection.py -x -q` | ❌ Wave 0 — new file | ⬜ pending |
| 02-02-03 | 02 | 1 | ATTR-02 | — | First-use default selection = today's two categories (D-04) | gui | `pytest tests/gui/test_attribute_selection.py -x -q` | ❌ Wave 0 | ⬜ pending |
| 02-03-01 | 03 | 1 | DIFF-01 | — | Differing cells get a `BackgroundRole` color; non-differing cells and the Target column do not | gui | `pytest tests/gui/test_diff_highlighting.py -x -q` | ❌ Wave 0 — new file | ⬜ pending |
| 02-03-02 | 03 | 1 | DIFF-01 | — | "Show differences only" toggle hides `any_differs is False` rows without removing highlight logic | gui | `pytest tests/gui/test_differences_only_toggle.py -x -q` | ❌ Wave 0 — new file | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

*Task IDs above are provisional — the planner assigns final plan/task numbering; update this table to match once PLAN.md files exist.*

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` — extend `build_description_xml`/`make_gdtf` with `attributes_xml=` (and, if Wheels/extended Properties are in scope, `wheels_xml=`/richer `properties` injection) following the existing `models_xml=`/`geometries_xml=` pattern
- [ ] `tests/gui/test_attribute_picker.py` — new
- [ ] `tests/gui/test_attribute_selection.py` — new
- [ ] `tests/gui/test_diff_highlighting.py` — new
- [ ] `tests/gui/test_differences_only_toggle.py` — new
- [ ] `tests/core/test_comparator.py` — existing file needs its `DISPLAY_CATEGORIES` import/assertions updated for the relaxed filter before other tests in this file can be trusted

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
