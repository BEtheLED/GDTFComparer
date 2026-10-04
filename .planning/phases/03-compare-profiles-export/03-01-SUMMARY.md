---
phase: 03-compare-profiles-export
plan: 01
subsystem: ui
tags: [pyside6, json, atomic-write, qcombobox, persistence]

# Dependency graph
requires:
  - phase: 02-attribute-browsing-diff-highlighting
    provides: AttributePicker.checked_attributes()/_checked state, set_catalog()'s D-04 first-use default-seeding, and the Attributes side panel layout this plan's toolbar row attaches to
provides:
  - "core/profile_repository.py: Profile dataclass, ProfileRepository (load_all/find/get/save, atomic os.open(O_EXCL)+os.replace write, validated read, hand-rolled per-OS app_data_dir), normalize_profile_name, profile_name_key"
  - "core/errors.py: ProfileError/ProfileNameError/ProfileNotFoundError/ProfileStorageError"
  - "AttributePicker.set_checked() (D-03 replace-not-merge) and _defaults_enabled"
  - "MainWindow: Profiles dropdown + Save… toolbar row above the Attributes picker, _refresh_profile_combo/_save_profile/_load_selected_profile/_ask_profile_name/_confirm"
affects: [03-02-compare-profiles-export, 03-03-compare-profiles-export, any future rename/delete or profile-export work]

# Actuals (#2632)
actuals:
  tokens: 18000
  tasks: 3
  commits: 3
plan_head_before: 7dea865daf87f5704f713fa6939d22d34f84100f

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Atomic JSON writes in core/ via os.open(O_CREAT|O_EXCL)+os.fsync+os.replace instead of tempfile.mkstemp, to satisfy the Phase 1 architecture guard that forbids tempfile/shutil imports in core/"
    - "A new GUI-facing core service is added to tests/test_architecture.py's APPROVED_CORE_SURFACE allow-list (now comparator, models, errors, profile_repository)"
    - "Case/whitespace/Unicode-NFC-insensitive name identity (profile_name_key) used uniformly for find/get/save/sort, decoupled from the stored display name (normalize_profile_name)"

key-files:
  created:
    - src/gdtf_comparer/core/profile_repository.py
    - tests/core/test_profile_repository.py
    - tests/gui/test_profile_toolbar.py
  modified:
    - src/gdtf_comparer/core/errors.py
    - src/gdtf_comparer/gui/attribute_picker.py
    - src/gdtf_comparer/gui/main_window.py
    - src/gdtf_comparer/app.py
    - tests/test_architecture.py
    - tests/conftest.py

key-decisions:
  - "Fixed a write-path gap (Rule 1): _write_all's os.open() call sat outside the except-OSError wrapper, so a failure creating the temp file would have propagated as a raw OSError instead of ProfileStorageError -- moved inside the wrapped try block"
  - "Shape-validation failures in a damaged/malformed profiles.json (wrong version type, non-list profiles, bad pair shape, duplicate names) all route through one _damaged() helper so every failure mode produces the same friendly, non-crashing message"

patterns-established:
  - "ProfileRepository(base_dir=Optional[str]) takes an explicit constructor argument (unlike FixtureRepository's no-arg constructor) specifically so tests inject tmp_path; the real default is resolved lazily via a module-level _default_profiles_dir() function tests/conftest.py monkeypatches, never a class-level default evaluated at import time"

requirements-completed: [ATTR-03]

duration: 13min
completed: 2026-10-04
status: complete
---

# Phase 3 Plan 1: Compare Profiles — Save, Load, Confirm, Harden Summary

**Compare profiles persisted as one atomic JSON file (core/profile_repository.py) behind a Profiles dropdown + Save… row in the Attributes panel, with D-03 replace-on-load, D-04 overwrite confirmation, and D-04/T-03-01 hardening against a damaged or half-written profiles.json.**

## Performance

- **Duration:** 13 min
- **Started:** 2026-10-04T22:07:18Z
- **Completed:** 2026-10-04T22:20:44Z
- **Tasks:** 3
- **Files modified:** 9 (3 created, 6 modified)

## Accomplishments

- A reusable spec sheet of checked (category, attribute) pairs can be saved under a name, survives an app restart, and is picked from a dropdown that replaces the checked set exactly (D-03) — including when loaded before any comparison has run, where Phase 2's D-04 first-use defaults no longer silently widen it (D-01 substitute-fixture workflow)
- Saving over an existing name (matched ignoring case, surrounding whitespace and Unicode normalization form) asks "Replace it?" with No as the safe default; a blank, too-long or control-character name is refused with a friendly message and nothing is written (D-04, ASVS V5)
- A damaged, oversized, non-UTF-8 or newer-schema-version `profiles.json` can never crash the app or be silently overwritten: the dropdown disables itself with a friendly status-bar message, and a save against a damaged file is refused before anything is written
- Every write to `profiles.json` is atomic (same-folder random temp file, `O_CREAT|O_EXCL`, fsynced, then `os.replace`) without importing `tempfile` in `core/`, keeping the Phase 1 architecture guard intact while still satisfying the standard atomic-write idiom

## Task Commits

Each task was committed atomically:

1. **Task 1: End-to-end save → reopen → load (tracer)** — `a83c517` (feat)
2. **Task 2: Confirm before overwrite, validate names (TDD)** — `65621d7` (feat)
3. **Task 3: Harden against a damaged file or failed save (TDD)** — `14d7e02` (feat)

**Plan metadata:** pending (docs: complete plan)

## Files Created/Modified

- `src/gdtf_comparer/core/profile_repository.py` — new: `Profile`, `ProfileRepository` (load_all/find/get/save/_write_all/_damaged/_parse_payload), `normalize_profile_name`, `profile_name_key`, `app_data_dir`, `_default_profiles_dir`
- `src/gdtf_comparer/core/errors.py` — added `ProfileError`/`ProfileNameError`/`ProfileNotFoundError`/`ProfileStorageError`
- `src/gdtf_comparer/gui/attribute_picker.py` — added `AttributePicker.set_checked()` (D-03) and `_defaults_enabled`
- `src/gdtf_comparer/gui/main_window.py` — added the Profiles dropdown + Save… toolbar row, `profile_repository`/`_active_profile` state, `_refresh_profile_combo`/`_save_profile`/`_load_selected_profile`/`_ask_profile_name`/`_confirm`
- `src/gdtf_comparer/app.py` — updated the shutdown comment to account for synchronous profile saves on the GUI thread
- `tests/test_architecture.py` — widened `APPROVED_CORE_SURFACE` by one module
- `tests/conftest.py` — added the autouse `_isolate_profile_storage` fixture
- `tests/core/test_profile_repository.py` — new, 31 tests (parametrized)
- `tests/gui/test_profile_toolbar.py` — new, 17 tests

## Decisions Made

- Followed the plan's `assumption_delta_decision` exactly: atomic writes in `core/` use `os.open(O_EXCL)` + `os.replace` rather than `tempfile.mkstemp`, because `tests/test_architecture.py::test_core_never_unpacks_archives_or_uses_temp_dirs` forbids importing `tempfile`/`shutil` anywhere under `core/`.
- `ProfileRepository.__init__(base_dir=None)` takes an explicit constructor argument (a deliberate, documented deviation from `FixtureRepository`'s no-arg shape) so tests inject `tmp_path` directly; the default resolves through a module-level `_default_profiles_dir()` function at construction time, so `tests/conftest.py`'s autouse monkeypatch takes effect for every `ProfileRepository()` built after the patch — never a class-level default evaluated once at import time.
- Name identity for find/get/save/sort is `profile_name_key` (NFC + strip + casefold), decoupled from the stored display name (`normalize_profile_name`, which only trims/NFC-normalizes and validates, preserving the user's typed case).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed an unwrapped `os.open()` failure path in `ProfileRepository._write_all`**
- **Found during:** Task 3, while writing `test_failed_replace_keeps_old_file_and_leaves_no_temp` / `test_failed_temp_write_leaves_no_temp`
- **Issue:** The initial Task 1 implementation called `fd = os.open(tmp_path, ...)` *outside* the `try/except OSError` block that wraps the rest of the atomic write. A failure creating the temp file itself (e.g. the folder becoming unwritable between `os.makedirs` and `os.open`) would have propagated as a raw, unwrapped `OSError` instead of the typed `ProfileStorageError` every other failure path produces — breaking the "never a raw exception reaches the GUI" contract (D-12-style convention) for this one specific failure point.
- **Fix:** Moved `fd = os.open(...)` inside the same `try` block as the rest of the write, so every `OSError` on this path — temp-file creation, write, fsync, or replace — is uniformly wrapped as `ProfileStorageError(...) from exc`.
- **Files modified:** `src/gdtf_comparer/core/profile_repository.py`
- **Verification:** Full suite green (207 passed), including the two failed-write tests added in the same task.
- **Committed in:** `14d7e02` (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Necessary for correctness (a consistent typed-error contract across every write-path failure mode); no scope creep.

## Issues Encountered

None — every task's tests passed on the first implementation attempt; no auth gates, checkpoints, or architectural questions arose.

## User Setup Required

None — no external service configuration required. No new dependency was installed (`platformdirs` was evaluated in RESEARCH and deliberately not adopted).

## Next Phase Readiness

- `ProfileRepository`, `Profile`, `normalize_profile_name`/`profile_name_key`, and the Profiles dropdown/Save… row are in place for Plan 03-02 (D-06 "N of M spec items not found" messaging) and Plan 03-03 (D-05 rename/delete, D-07's "Manage" control) to build on directly.
- `_confirm()` is already shaped for reuse by Plan 03-03's delete confirmation (same plain-text, No-default `QMessageBox` convention).
- No blockers identified.

---
*Phase: 03-compare-profiles-export*
*Completed: 2026-10-04*

## Self-Check: PASSED

- FOUND: src/gdtf_comparer/core/profile_repository.py
- FOUND: tests/core/test_profile_repository.py
- FOUND: tests/gui/test_profile_toolbar.py
- FOUND: .planning/phases/03-compare-profiles-export/03-01-SUMMARY.md
- FOUND commit: a83c517 (Task 1)
- FOUND commit: 65621d7 (Task 2)
- FOUND commit: 14d7e02 (Task 3)
