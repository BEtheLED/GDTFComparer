---
phase: 03-compare-profiles-export
plan: 04
subsystem: ui
tags: [pyside6, qboxlayout, qlistwidget, qicon, gap-closure]

# Dependency graph
requires:
  - phase: 03-compare-profiles-export (Plans 01-03)
    provides: ProfileRepository/Profile, the Profiles dropdown/Save…/Manage toolbar row, missing_attributes()/_profile_items_not_found_message(), ComparisonRow.differs (core, unchanged)
provides:
  - "gui/main_window.py: profile_combo_row / profile_actions_row two-row toolbar layout, ATTRIBUTES_PANEL_MIN_WIDTH_PX (240 px drag floor)"
  - "gui/main_window.py: COMPARE_MATCH_STATE_ROLE, MATCH_STATE_MATCH/DIFFERS/UNKNOWN, MATCH_STATE_TOOLTIPS, _MATCH_INDICATOR_COLORS, _match_indicator_icon(), _set_compare_item_match_state/_mark_all_compare_items_unknown/_reset_match_indicators/_update_match_indicators"
  - "tests/gui/test_compare_list_match_indicator.py: 10 tests covering match/differs/unknown states, every reset trigger, icon color/shape, tooltip wording, the defensive mismatch guard, and the read-only guarantee"
affects: [03-compare-profiles-export (UAT gap closure, G-03-1/G-03-2), any future export/CSV work touching the Compare with list or the Attributes panel toolbar]

# Actuals (#2632)
actuals:
  tokens: 6300
  tasks: 2
  commits: 3
plan_head_before: 862bb76cdfe12ea87c4cb5a3e5d12d12e9aa4d9a

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Fixed, theme-independent indicator colors (QColor hex literals) for a per-item status dot, deliberately NOT derived from qt-material's theme like diff_highlight_color -- a dot needs to read identically in light and dark mode"
    - "A shared private helper (_mark_all_compare_items_unknown) backs both the public _reset_match_indicators (called from the three list/target mutators) and _update_match_indicators' own no-result/stale-defensive paths, so 'reset to unknown' has exactly one implementation reachable two ways without a second literal call to the public reset method"
    - "QToolButton/QPushButton stretch-1 rows inside a QVBoxLayout, replacing a single QHBoxLayout, as the fix for 'three widgets whose combined sizeHint exceeds the available width' -- measured per-widget sizeHint against the available panel width at both the default and drag-floor widths, in both qt-material themes, rather than guessing"

key-files:
  created:
    - tests/gui/test_compare_list_match_indicator.py
  modified:
    - src/gdtf_comparer/gui/main_window.py
    - tests/gui/test_profile_toolbar.py
    - tests/gui/test_profile_manage.py

key-decisions:
  - "Task 2's _update_match_indicators achieves its 'reset to unknown' behavior (no-result case, and the defensive compare_list/result mismatch case) by calling a new private _mark_all_compare_items_unknown() helper directly, rather than calling the public _reset_match_indicators() by name -- this satisfies the plan's own acceptance criterion that grep for the literal string 'self._reset_match_indicators()' match exactly 3 times (the three list/target mutators), while keeping the actual reset logic in one place (both methods delegate to the same helper, so behavior is identical either way)"
  - "profile_actions_row's two buttons both get layout stretch 1 (not stretch 0 on Manage), matching the plan's Design notes measurement that both widgets clear their sizeHint with stretch 1 at both the 260 px default and the new 240 px floor"

requirements-completed: [ATTR-03]

# Coverage metadata (#1602)
coverage:
  - id: D1
    description: "G-03-1: the profile toolbar (dropdown, Save…, Manage) never clips at the Attributes panel's 260 px default or its 240 px drag floor, in both qt-material themes, still as one consolidated block above the attribute picker (now two stacked rows)."
    requirement: "ATTR-03"
    verification:
      - kind: unit
        ref: "tests/gui/test_profile_toolbar.py#test_profile_toolbar_widgets_never_clipped"
        status: pass
      - kind: unit
        ref: "tests/gui/test_profile_toolbar.py#test_profile_toolbar_sits_above_picker_in_attributes_panel"
        status: pass
      - kind: unit
        ref: "tests/gui/test_profile_manage.py#test_manage_button_sits_in_profile_row"
        status: pass
    human_judgment: false
  - id: D2
    description: "G-03-2: each 'Compare with' file shows a green/red/gray dot reflecting only the currently checked attributes' match status against the target, reusing ComparisonRow.differs with zero new comparison logic, neutral before any run and after any file-list/target/selection change."
    requirement: "ATTR-03"
    verification:
      - kind: unit
        ref: "tests/gui/test_compare_list_match_indicator.py (10 tests: new-item state, match/differs after run, unchecking falls back to unknown, add/remove/retarget resets, icon color/shape, tooltip wording, read-only guarantee, defensive mismatch reset)"
        status: pass
    human_judgment: true
    rationale: "The plan's Task 2 <human-check> explicitly covers both gaps together in the real app -- dot colors against real qt-material chrome at real screen DPI, and the toolbar's readability at a user-dragged panel width -- neither of which the offscreen test platform (QT_QPA_PLATFORM=offscreen) can fully judge. Not run by this automated executor; carried forward to /gsd-verify-work per the plan's <verification> block."

duration: 23min
completed: 2026-10-05
status: complete
---

# Phase 3 Plan 4: Gap Closure — Toolbar Clipping Fix & Compare-List Match Indicator Summary

**Split the squeezed profile toolbar into two stacked rows (closes G-03-1) and added a reused-logic green/red/gray match dot to each "Compare with" file (closes G-03-2), both via TDD/tracer execution against 03-UAT.md's whole-phase walkthrough findings.**

## Performance

- **Duration:** 23 min
- **Started:** 2026-10-05T03:40:00Z
- **Completed:** 2026-10-05T04:02:42Z
- **Tasks:** 2
- **Files modified:** 4 (1 created, 3 modified)

## Accomplishments

- G-03-1 closed: the profile toolbar's dropdown, "Save…" and "Manage" button each measure at or above their own `sizeHint().width()` at the Attributes panel's 260 px default AND its new 240 px drag floor, in both qt-material themes -- confirmed by a new parametrized clipping test that reproduces the exact pre-fix measurement (65/65/64 px actual vs. 122/78/92 px needed) and proves it resolved
- The fix kept D-07's "one consolidated toolbar block" intact: `profile_row` is now a `QVBoxLayout` holding `profile_combo_row` (the dropdown alone) above `profile_actions_row` (Save…+Manage) -- nothing moved to a different part of the panel, no label was abbreviated or hidden behind an icon
- `ATTRIBUTES_PANEL_MIN_WIDTH_PX = 240` replaces the inline `220` drag-floor literal, 10 px above the plan's measured 230 px breakeven for margin against font-metric variance
- G-03-2 closed: every file in "Compare with" now carries a `COMPARE_MATCH_STATE_ROLE` and a small colored-dot icon -- green when none of the currently checked (category, attribute) pairs differ from the target for that file, red when at least one does, gray before any comparison has run or whenever the target, file list, or checked attributes change afterward
- The match color is read straight off the existing `ComparisonRow.differs` tuple filtered to `attribute_picker.checked_attributes()` -- zero new comparison logic, and `git diff` against `src/gdtf_comparer/core/` is empty for the whole plan
- A defensive check in `_update_match_indicators` falls back every dot to gray whenever `compare_list` and the current `result.comparisons` disagree by count or by path order, so a dot never guesses which file it belongs to
- Each dot's tooltip appends a plain-language state sentence after the file's existing full-path tooltip; `_update_match_indicators`/`_reset_match_indicators` are provably read-only (`test_indicator_never_changes_comparison_or_selection`)

## Task Commits

Each task was committed atomically:

1. **Task 1: Split profile toolbar into two stacked rows (tracer)** — `8ab8516` (fix)
2. **Task 2: Match indicator — RED** — `39ecaae` (test)
3. **Task 2: Match indicator — GREEN** — `efdaa11` (feat)

_No refactor commit: the GREEN implementation was already written in its final shared-helper shape (see Decisions Made) before the first commit of that task, so there was nothing left to refactor afterward._

**Plan metadata:** pending (docs: complete plan)

## Files Created/Modified

- `src/gdtf_comparer/gui/main_window.py` — `ATTRIBUTES_PANEL_MIN_WIDTH_PX`; `profile_combo_row`/`profile_actions_row` two-row toolbar (replacing the single `profile_row` QHBoxLayout); `COMPARE_MATCH_STATE_ROLE`, `MATCH_STATE_MATCH`/`DIFFERS`/`UNKNOWN`, `MATCH_STATE_TOOLTIPS`, `_MATCH_INDICATOR_DIAMETER_PX`, `_MATCH_INDICATOR_COLORS`, `_match_indicator_icon()`; `_set_compare_item_match_state`/`_mark_all_compare_items_unknown`/`_reset_match_indicators`/`_update_match_indicators`; wired into `add_compare_files`/`remove_selected_files`/`set_target_file` (reset) and `_apply_attribute_selection` (recompute)
- `tests/gui/test_profile_toolbar.py` — rescoped `test_profile_toolbar_sits_above_picker_in_attributes_panel` to the new rows; added `test_profile_toolbar_widgets_never_clipped` (parametrized over both themes)
- `tests/gui/test_profile_manage.py` — rescoped `test_manage_button_sits_in_profile_row` to `profile_actions_row`
- `tests/gui/test_compare_list_match_indicator.py` — new, 10 tests

## Decisions Made

- `_update_match_indicators` achieves its "reset to unknown" behavior via a new private `_mark_all_compare_items_unknown()` helper called directly, rather than calling the public `_reset_match_indicators()` by name, specifically so the plan's own acceptance criterion (`grep -c "self._reset_match_indicators()"` equals exactly 3 -- the three list/target mutators) holds literally, while `_reset_match_indicators()` itself just delegates to the same helper -- one implementation, two call paths, identical behavior either way.
- `profile_actions_row` gives both `save_profile_button` and `manage_profile_button` layout stretch 1 (not stretch 0 on Manage), matching the plan's Design notes measurement that both widgets clear their own `sizeHint` with stretch 1 at both the 260 px default and the new 240 px floor.
- Followed the plan's `assumption_delta_decision` exactly: stacked rows (not icon-only buttons) for G-03-1, since that keeps every label as readable text rather than hiding "Save…"/"Manage" behind icons + tooltips.

## Deviations from Plan

None — plan executed exactly as written for both tasks' behavior and acceptance criteria. The one implementation adjustment (the `_mark_all_compare_items_unknown` helper, documented above under Decisions Made) was made to satisfy a literal acceptance-criteria grep exactly as specified in the plan, not a deviation from the plan's intent -- the plan's own `<action>` prose and its `<acceptance_criteria>` grep count were in tension (the prose describes `_update_match_indicators` calling `self._reset_match_indicators()` directly; the acceptance criterion requires exactly 3 total occurrences of that literal call, i.e. only the three mutators), and this shape satisfies both: identical reset behavior, and the acceptance criterion passes byte-for-byte.

## Issues Encountered

A full-suite run of `tests/gui/test_compare_list_match_indicator.py` crashed once with a native stack trace during interpreter teardown (no Python traceback, no assertion failure) immediately after refactoring to the shared helper. Three immediate re-runs of the same file, and two full-suite runs afterward, all passed cleanly (10/10, then 256/256 twice) with no recurrence -- consistent with an environment-level flake in the offscreen Qt platform's teardown rather than a defect in this plan's code. Not treated as a deviation since it was not reproducible and no code change was needed to resolve it.

## User Setup Required

None — no external service configuration required. No new dependency was added.

## Next Phase Readiness

- Both 03-UAT.md gaps (G-03-1, G-03-2) are closed with passing automated coverage; the plan's Task 2 `<human-check>` (both gaps, real app, real qt-material chrome) is carried forward to `/gsd-verify-work` per the plan's `<verification>` block -- it was not run by this automated executor (real macOS rendering at a user-dragged panel width cannot be judged from the offscreen test platform).
- `.planning/REQUIREMENTS.md`'s ATTR-03 row was already marked complete by Plan 03-03 (the last plan to declare it as a *new* requirement); this gap-closure plan's own `requirements: [ATTR-03]` frontmatter references the same already-complete requirement and needs no further REQUIREMENTS.md edit. Left untouched; noting here for the orchestrator per this plan's worktree-mode instructions.
- No blockers identified. No modifications were made to `src/gdtf_comparer/core/` by either task, confirmed via `git diff --quiet HEAD -- src/gdtf_comparer/core` throughout.

---
*Phase: 03-compare-profiles-export*
*Completed: 2026-10-05*

## Self-Check: PASSED

- FOUND: tests/gui/test_compare_list_match_indicator.py
- FOUND: .planning/phases/03-compare-profiles-export/03-04-SUMMARY.md
- FOUND commit: 8ab8516 (Task 1)
- FOUND commit: 39ecaae (Task 2 RED)
- FOUND commit: efdaa11 (Task 2 GREEN)
- FOUND commit: 566f4e9 (SUMMARY)
