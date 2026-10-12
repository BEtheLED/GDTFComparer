---
phase: "2"
slug: "attribute-browsing-diff-highlighting"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-09-29"
validated: "2026-10-12"
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
| 02-01-T1 | 01 | 1 | ATTR-01, ATTR-02 | T-02-04 | Attributes panel + selection proxy; unchecking an attribute hides its rows, core stays category-agnostic | unit+gui | `pytest tests/core/test_comparator.py tests/gui/test_attribute_selection.py -q -W error::DeprecationWarning` | ✅ | ✅ green |
| 02-01-T2 | 01 | 1 | ATTR-01, ATTR-02 | T-02-01 | Search narrows picker visibility only; empty selection shows a status-bar hint | gui | `pytest tests/gui/test_attribute_picker.py tests/gui/test_attribute_selection.py -q -W error::DeprecationWarning` | ✅ | ✅ green |
| 02-02-T1 | 02 | 1 | ATTR-01 | — | DMX `<AttributeDefinitions>` entries become one picker entry per (category, attribute), ticking one compares its definition | unit+gui | `pytest tests/core/test_extract.py tests/gui/test_dmx_attributes.py -q -W error::DeprecationWarning` | ✅ | ✅ green |
| 02-02-T2 | 02 | 1 | ATTR-01 | — | Odd/colliding definitions never break the panel or leak into Beam/Physical Properties; shared presence-check helper | unit+gui | `pytest tests/core/test_extract.py tests/gui/test_dmx_attributes.py -q -W error::DeprecationWarning` | ✅ | ✅ green |
| 02-03-T1 | 03 | 1 | DIFF-01 | — | Differing comparison cells painted with the theme's highlight color (pixel-level render proof) | gui | `pytest tests/gui/test_diff_highlighting.py -q -W error::DeprecationWarning` | ✅ | ✅ green |
| 02-03-T2 | 03 | 1 | DIFF-01 | — | "Show differences only" toggle hides agreeing rows on top of highlighting, unchanged by the attribute selection proxy | gui | `pytest tests/gui/test_differences_only_toggle.py tests/gui/test_attribute_selection.py -q -W error::DeprecationWarning` | ✅ | ✅ green |
| 02-03-T3 | 03 | 1 | DIFF-01 | — | Highlight re-tints live on OS theme switch without re-running the comparison; theme color resolved once per theme | gui | `pytest tests/gui/test_diff_highlighting.py tests/gui/test_theme.py -q -W error::DeprecationWarning` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

*Updated 2026-10-12 against the actual PLAN/SUMMARY task numbering (plans 02-01..02-03 executed 2026-09-30). Confirmed by re-running the full suite: `pytest -q -W error::DeprecationWarning` → 276 passed. All seven named test files listed above exist and pass; no gaps found, so the auditor dispatch was skipped (workflow step 3: "No gaps → skip to Step 6").*

---

## Wave 0 Requirements

- [x] `tests/conftest.py` — extended with `attributes_xml=` injection
- [x] `tests/gui/test_attribute_picker.py` — created
- [x] `tests/gui/test_attribute_selection.py` — created
- [x] `tests/gui/test_diff_highlighting.py` — created
- [x] `tests/gui/test_differences_only_toggle.py` — created
- [x] `tests/core/test_comparator.py` — `DISPLAY_CATEGORIES` removed; replaced with `LEADING_CATEGORIES`/`DEFAULT_SELECTED_CATEGORIES` assertions (`grep -rn "DISPLAY_CATEGORIES" src tests` → no matches)

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s (full suite: 14.22s)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated 2026-10-12 (audit of existing VALIDATION.md; no gaps — full suite 276/276 passed, all seven named test files present)

## Validation Audit 2026-10-12

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
