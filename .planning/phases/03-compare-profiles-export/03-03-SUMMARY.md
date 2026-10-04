---
phase: 03-compare-profiles-export
plan: 03
subsystem: ui
tags: [pyside6, qtoolbutton, qmenu, atomic-write, rename, delete]

# Dependency graph
requires:
  - phase: 03-compare-profiles-export (Plan 01)
    provides: ProfileRepository, Profile, normalize_profile_name/profile_name_key, MainWindow._confirm/_ask_profile_name, the Profiles dropdown/Save… toolbar row
  - phase: 03-compare-profiles-export (Plan 02)
    provides: missing_attributes(), _profile_items_not_found_message(), the D-06 not-found status branch _active_profile feeds
provides:
  - "core/profile_repository.py: ProfileRepository.rename(old_name, new_name) -> Profile and .delete(name) -> None, both load_all()-first so a damaged file is never overwritten"
  - "gui/main_window.py: manage_profile_button/menu, rename_profile_action/delete_profile_action, _update_profile_actions, _rename_selected_profile, _delete_selected_profile"
  - "tests/gui/test_profile_manage.py: Manage button placement/enabling, rename and delete flows (conflict, cancel, restart persistence, selection untouched, D-06 continuity, damaged-file refusal)"
affects: [any future profile-management or export work that reads/writes profiles.json]

# Actuals (#2632)
actuals:
  tokens: 8500
  tasks: 2
  commits: 2
plan_head_before: 94026974aa1a6bbabe938ceab9c5de63edc8bd18

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Manage is a QToolButton with setPopupMode(InstantPopup) and a QMenu holding Rename…/Delete… QActions, following RESEARCH Pattern 3 exactly"
    - "profile_combo.currentIndexChanged drives only _update_profile_actions (enable/disable), never a load -- activated stays the sole load trigger (RESEARCH Pitfall 3 carried to the Manage button)"
    - "rename()/delete() both build a {profile_name_key: Profile} map from load_all() before mutating, so a damaged/newer-version profiles.json raises before anything is written -- the same load-then-write shape save() already established in Plan 03-01"

key-files:
  created:
    - tests/gui/test_profile_manage.py
  modified:
    - src/gdtf_comparer/core/profile_repository.py
    - src/gdtf_comparer/gui/main_window.py
    - tests/core/test_profile_repository.py
    - .planning/REQUIREMENTS.md

key-decisions:
  - "rename()'s only-written-when-changed check compares the new normalized display name to the stored name (not just the identity key), so a pure case-only rename ('spec' -> 'Spec') still writes, while renaming to the exact same text is a true no-op"
  - "delete() writes an empty {\"version\": 1, \"profiles\": []} rather than removing profiles.json entirely when the last profile goes, keeping the file's existence/shape invariant simple for load_all()"

patterns-established:
  - "_update_profile_actions() is called both from the currentIndexChanged connection and directly at the end of _refresh_profile_combo, since the index can stay at -1 across a repopulation (no signal fires) -- the same reasoning RESEARCH Pitfall 3 already established for the combo's placeholder text"

requirements-completed: [ATTR-03]

duration: 36min
completed: 2026-10-04
status: complete
---

# Phase 3 Plan 3: Compare Profiles — Rename & Delete via a Manage Menu Summary

**A "Manage" QToolButton in the Profiles toolbar row now opens Rename…/Delete… for whichever profile is shown in the dropdown: rename keeps attributes and refuses name collisions, delete always asks first (No default) and removes the profile everywhere, and neither ever touches the checked attributes, the current comparison, or a damaged profiles.json.**

## Performance

- **Duration:** 36 min
- **Completed:** 2026-10-04
- **Tasks:** 2
- **Files modified:** 5 (1 created, 4 modified)

## Accomplishments

- `ProfileRepository.rename(old_name, new_name)`: keeps the profile's attributes, allows a case-only rename, refuses a name already used by a different saved profile with a friendly message naming the existing profile ("A profile named 'B' already exists..."), and is a true no-op (no write) when the new name is identical to the one already stored
- `ProfileRepository.delete(name)`: removes the matched profile, writing an empty `{"version": 1, "profiles": []}` rather than deleting the file when it was the last one; both `rename` and `delete` start from `load_all()`, so a damaged, oversized or newer-version `profiles.json` is never overwritten (T-03-16)
- A `Manage` `QToolButton` with an instant-popup `QMenu` (`Rename…`, `Delete…`) sits in the same profile toolbar row as the dropdown and `Save…` (D-07), disabled until a profile is shown in the dropdown and re-enabled/disabled purely from `profile_combo.currentIndexChanged` — never from `activated`, so showing a profile in the dropdown without the user choosing it never loads it
- Renaming updates `_active_profile` when the renamed profile is the one currently loaded, so the Phase 3 D-06 "N of M spec items not found" report keeps naming it correctly under the new name; deleting the loaded profile clears `_active_profile`, so that report stops cleanly instead of naming a profile that no longer exists
- Delete always asks first via the existing `_confirm` helper (plain text, No as both the default and escape button, T-03-14); neither rename nor delete ever changes the checked attributes, re-runs the comparison, or disturbs `is_comparison_running()`/`run_button.isEnabled()`

## Task Commits

Each task was committed atomically:

1. **Task 1: End-to-end "Manage > Rename… renames the profile shown in the dropdown" (tracer)** — `bcae1d7` (feat)
2. **Task 2: Manage > Delete… asks first, then removes the profile everywhere (TDD)** — `7768edb` (feat)

**Plan metadata:** pending (docs: complete plan)

## Files Created/Modified

- `src/gdtf_comparer/core/profile_repository.py` — added `ProfileRepository.rename()` and `.delete()`
- `src/gdtf_comparer/gui/main_window.py` — added `MANAGE_PROFILES_LABEL`/`_TOOLTIP`, `RENAME_PROFILE_LABEL`/`_TITLE`/`_PROMPT`, `PROFILE_RENAMED_TEMPLATE`, `DELETE_PROFILE_LABEL`, `DELETE_PROFILE_TEMPLATE`, `PROFILE_DELETED_TEMPLATE`; the `manage_profile_button`/`manage_profile_menu`/`rename_profile_action`/`delete_profile_action` widgets; `_update_profile_actions`, `_rename_selected_profile`, `_delete_selected_profile`; extended `_refresh_profile_combo` to call `_update_profile_actions` on both paths
- `tests/core/test_profile_repository.py` — added 10 tests covering rename/delete round trip, case-only rename, name conflicts, not-found, invalid name, damaged-file refusal, last-profile-empties-store, and `test_rename_and_delete` (VALIDATION.md D-05 row)
- `tests/gui/test_profile_manage.py` — new, 13 tests covering Manage button placement/enabling, rename flow (restart persistence, cancel, conflict, continuity under the profile's own not-found report), and delete flow (ask-first/No-keeps, Yes-removes-everywhere, stops the not-found report, disables the dropdown after the last profile, refuses a damaged file)
- `.planning/REQUIREMENTS.md` — marked ATTR-03 complete (Phase 3's last plan; see Final Requirement Note below)

## Decisions Made

- `rename()` compares the new normalized display name against the stored profile's exact `name` (not just the `profile_name_key` identity) to decide whether anything needs to be written — this lets a pure case-change ("spec" → "Spec") still produce a write (the display name genuinely changed) while a rename to literally the same text is a true no-op.
- `delete()` follows `_write_all`'s existing shape exactly: it always calls `_write_all()`, even when the result is an empty profile list, rather than special-casing file removal — keeping `load_all()`'s "file exists with a valid empty list" and "file never existed" cases distinct and both well-defined.
- `_update_profile_actions()` is wired to `currentIndexChanged` (fires on both user and programmatic changes) rather than `activated` (user-only), and is also called directly at the end of `_refresh_profile_combo` for the case where the index stays at `-1` across a repopulation and no signal fires at all — this is the correct signal choice specifically because *enabling the Manage button* should react to any index change, unlike loading a profile which must only ever happen on `activated`.

## Deviations from Plan

None — plan executed exactly as written. Both tasks' RED/GREEN sequencing, the exact message templates, the `rename()`/`delete()` signatures, and the Manage button/menu construction all match the plan's `<action>` and interfaces block verbatim.

## Issues Encountered

None — every test passed on first implementation attempt for both tasks; no auth gates, checkpoints, or architectural questions arose.

## User Setup Required

None — no external service configuration required. No new dependency was added.

## Next Phase Readiness

- `ProfileRepository.rename()`/`.delete()` and the Manage menu are in place; Phase 3's three plans (save/load/confirm/harden, D-06 portability reporting, rename/delete) together complete ATTR-03 end to end.
- Task 2's human-check (the whole-phase real-app walkthrough: save, restart, load against unrelated fixtures, rename, delete with No then Yes) is carried forward to `/gsd-verify-work` per the plan's `<verification>` block — it was not run by this automated executor (real macOS dialogs, the 260 px panel's fit, and the real per-user profiles folder cannot be judged from the offscreen test platform).
- No blockers identified.

---
*Phase: 03-compare-profiles-export*
*Completed: 2026-10-04*

## Self-Check: PASSED

- FOUND: src/gdtf_comparer/core/profile_repository.py
- FOUND: src/gdtf_comparer/gui/main_window.py
- FOUND: tests/core/test_profile_repository.py
- FOUND: tests/gui/test_profile_manage.py
- FOUND: .planning/phases/03-compare-profiles-export/03-03-SUMMARY.md
- FOUND commit: bcae1d7 (Task 1)
- FOUND commit: 7768edb (Task 2)
