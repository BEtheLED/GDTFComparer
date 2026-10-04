---
phase: 03-compare-profiles-export
plan: 02
subsystem: ui
tags: [pyside6, status-bar, attribute-catalog, transparency]

# Dependency graph
requires:
  - phase: 03-compare-profiles-export (Plan 01)
    provides: ProfileRepository, Profile, AttributePicker.set_checked()/_known, MainWindow._active_profile and the Profiles dropdown/Save… toolbar row
provides:
  - "core/profile_repository.py: missing_attributes(profile_attributes, available_pairs) pure helper (D-06)"
  - "gui/main_window.py: PROFILE_ITEMS_NOT_FOUND_TEMPLATE, PROFILE_LOADED_NO_RESULT_TEMPLATE, MainWindow._profile_items_not_found_message(), a highest-precedence not-found branch in _show_result_status, and a pre-comparison message in _load_selected_profile"
affects: [03-03-compare-profiles-export, any future export/CSV work that reuses the D-06 not-found computation]

# Actuals (#2632)
actuals:
  tokens: 7000
  tasks: 2
  commits: 2
plan_head_before: f14c327756e5b3a54622be236b1dbe16fb498b55

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "D-06's not-found check is computed fresh from core.comparator.attribute_catalog(result) on every call, never from AttributePicker._known (a sticky cross-run superset) -- the single Pitfall 1 rule this plan exists to enforce"
    - "A persistent highest-precedence branch inside the existing single status writer (_show_result_status), rather than a one-shot message from the load handler, so it survives the coalesced selection_changed that loading itself triggers and recomputes on every re-run"

key-files:
  created:
    - tests/gui/test_profile_portability.py
  modified:
    - src/gdtf_comparer/core/profile_repository.py
    - src/gdtf_comparer/gui/main_window.py
    - tests/core/test_profile_repository.py

key-decisions:
  - "missing_attributes() takes Iterable (not FrozenSet) for both parameters per the plan's interface, accepting a list or a set from either caller without requiring pre-conversion"
  - "The pre-comparison PROFILE_LOADED_NO_RESULT_TEMPLATE message is written directly by _load_selected_profile (not routed through _show_result_status), since _show_result_status returns immediately while table_model.result() is None and would never reach a branch written there"

patterns-established:
  - "_profile_items_not_found_message(result) is read-only and idempotent: calling it (or _show_result_status) repeatedly never changes the checked set, the rendered rows, or the ComparisonResult -- verified directly by test_not_found_check_never_changes_selection_or_result"

requirements-completed: [ATTR-03]

duration: 12min
completed: 2026-10-04
status: complete
---

# Phase 3 Plan 2: Compare Profiles — Spec-Item Portability Reporting Summary

**A loaded compare profile now tells the user exactly how many and which of its spec items aren't present in the current comparison's files, via a highest-precedence `_show_result_status` branch recomputed from the current `attribute_catalog(result)` on every selection change and re-run — never from the picker's sticky cross-run `_known` set.**

## Performance

- **Duration:** 12 min
- **Completed:** 2026-10-04
- **Tasks:** 2
- **Files modified:** 4 (1 created, 3 modified)

## Accomplishments

- `missing_attributes(profile_attributes, available_pairs)` in `core/profile_repository.py`: a pure, Qt-free helper returning the subset of a profile's checked pairs with no row in the current comparison (D-06)
- `MainWindow._profile_items_not_found_message()` and the new `PROFILE_ITEMS_NOT_FOUND_TEMPLATE` status: "N of M spec items in '<profile>' weren't found in these files: <names>." — the highest-precedence branch inside `_show_result_status`, ahead of `NO_ATTRIBUTES_SELECTED_MESSAGE`, and combined with `NO_DIFFERENCES_MESSAGE` when "Show differences only" also empties the table
- A regression test (`test_check_uses_current_catalog_not_remembered_attributes`) deliberately plants the Pitfall-1 trap — an attribute present in `AttributePicker._known` from an earlier full-catalog run — and proves the not-found count still reports it missing once the files change, since the check is recomputed from the *current* result's catalog, never the picker's sticky known set
- Loading a profile before any comparison has finished says "Loaded profile '<name>' (<count> spec items). Run a comparison to check them against your files." instead of either a misleading 0% or 100% not-found claim (RESEARCH Pitfall 2) — the message is written directly by the load handler since `_show_result_status` returns early with no current result
- Every edge case from the plan's `must_haves` holds: an item on only one file counts as found; re-running against different files always rechecks from scratch; "Show differences only" never hides the warning; an empty profile never reports "0 of 0"; unticking a found item lowers the total but not the missing count; reloading the same profile is idempotent; loading another profile fully replaces the tracked spec sheet; the check never mutates the checked set, the rendered rows, or the `ComparisonResult`

## Task Commits

Each task was committed atomically:

1. **Task 1: End-to-end "load a spec sheet against fixtures missing some of its items" (tracer)** — `aedb77b` (feat)
2. **Task 2: Edges — before any comparison, all items missing, differences only, empty/reloaded profiles (TDD)** — `2fc12f7` (feat)

**Plan metadata:** pending (docs: complete plan)

## Files Created/Modified

- `src/gdtf_comparer/core/profile_repository.py` — added `missing_attributes(profile_attributes, available_pairs) -> FrozenSet[AttributePair]`
- `src/gdtf_comparer/gui/main_window.py` — added `PROFILE_ITEMS_NOT_FOUND_TEMPLATE`, `PROFILE_LOADED_NO_RESULT_TEMPLATE`, `_profile_items_not_found_message()`; extended `_show_result_status()` with the new highest-precedence branch; extended `_load_selected_profile()` with the pre-comparison message
- `tests/core/test_profile_repository.py` — added `test_missing_attributes` (VALIDATION.md D-06 row)
- `tests/gui/test_profile_portability.py` — new, 13 real-run tests covering both tasks' behavior and every edge from `must_haves`

## Decisions Made

- `missing_attributes()`'s signature takes `Iterable[AttributePair]` for both parameters (per the plan's interface block) rather than requiring `FrozenSet` up front, so a caller can pass a plain list or set directly; neither input is mutated and the return is always a `frozenset`.
- The pre-comparison message (Task 2) is written directly from `_load_selected_profile`, never routed through `_show_result_status`, because that method's existing early return (`result is None: return`) means a branch placed there would simply never run in this state — the plan's Design notes call this out explicitly, and the implementation follows it exactly.

## Deviations from Plan

None — plan executed exactly as written. Both tasks' RED/GREEN sequencing, the exact message templates, and the `_show_result_status` precedence ordering (not-found+differences-empty, not-found alone, no-attributes-selected, no-differences, normal summary) all match the plan's `<action>` and Design notes verbatim.

## Issues Encountered

None — every test passed on first implementation attempt for both tasks; no auth gates, checkpoints, or architectural questions arose.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- `missing_attributes()` and `_profile_items_not_found_message()` are available for Plan 03-03's rename/delete work (D-05, D-07) to build on if a renamed or deleted profile needs to interact with the active not-found report.
- No blockers identified.

---
*Phase: 03-compare-profiles-export*
*Completed: 2026-10-04*

## Self-Check: PASSED

- FOUND: src/gdtf_comparer/core/profile_repository.py
- FOUND: src/gdtf_comparer/gui/main_window.py
- FOUND: tests/core/test_profile_repository.py
- FOUND: tests/gui/test_profile_portability.py
- FOUND commit: aedb77b (Task 1)
- FOUND commit: 2fc12f7 (Task 2)
