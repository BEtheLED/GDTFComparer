---
phase: 01-foundation-rebuild
plan: 07
subsystem: gui
tags: [pyside6, self-comparison-guard, code-review-followup, docs]
requires:
  - phase: 01-foundation-rebuild
    provides: "MainWindow file-selection/comparison workflow (01-02/01-04) and OsThemeFollower (01-05)"
provides:
  - "add_compare_files refuses a candidate that resolves to the current target, with status-bar feedback"
  - "set_target_file evicts a newly chosen target from the comparison list, with status-bar feedback"
  - "_normalized_path() canonicalizes paths (realpath + normcase) so './'/symlink aliases of the target are also refused"
  - "ComparisonRow.any_differs and OsThemeFollower.current_theme are now covered by automated tests"
  - "README states the real Python 3.11+ floor instead of pinning python3.12"
affects: [phase-02-diff-highlighting, phase-03-export]
actuals:
  tokens: 2755
  tasks: 2
  commits: 3
tech-stack:
  added: []
  patterns:
    - "Path identity for GUI selection state is decided by os.path.normcase(os.path.realpath(path)), not raw string equality"
key-files:
  created:
    - tests/gui/test_file_selection.py
    - tests/core/test_models.py
  modified:
    - src/gdtf_comparer/gui/main_window.py
    - tests/gui/test_theme.py
    - README.md
key-decisions:
  - "IN-01: keep both ComparisonRow.any_differs and OsThemeFollower.current_theme as intentional future surface (Phase 2 diff highlighting / Phase 3 export, and 01-05's published OsThemeFollower interface) rather than removing them; add tests instead of deleting code"
  - "WR-02 fix lives entirely in gui/main_window.py using stdlib os.path only -- no new gdtf_comparer.core import, keeping the UI-02 import boundary intact"
patterns-established:
  - "Self-selection guard: refuse-on-add plus evict-on-promote, both surfaced via statusBar().showMessage(), is the template for any future GUI list dedupe-by-identity behaviour"
requirements-completed: [RELI-01]
coverage:
  - id: D1
    description: "add_compare_files refuses the current target (direct path, './' alias, and symlink alias) and reports it in the status bar"
    requirement: "RELI-01"
    verification:
      - kind: unit
        ref: "tests/gui/test_file_selection.py::test_target_file_is_not_added_as_comparison"
        status: pass
      - kind: unit
        ref: "tests/gui/test_file_selection.py::test_same_file_via_alternate_path_is_detected"
        status: pass
    human_judgment: false
  - id: D2
    description: "set_target_file evicts a newly chosen target from the comparison list and reports it in the status bar"
    requirement: "RELI-01"
    verification:
      - kind: unit
        ref: "tests/gui/test_file_selection.py::test_new_target_is_removed_from_comparison_list"
        status: pass
    human_judgment: false
  - id: D3
    description: "Distinct comparison files are still added in order, with duplicates skipped, when no self-selection is involved"
    requirement: "RELI-01"
    verification:
      - kind: unit
        ref: "tests/gui/test_file_selection.py::test_distinct_comparison_files_are_still_added"
        status: pass
    human_judgment: false
  - id: D4
    description: "ComparisonRow.any_differs and OsThemeFollower.current_theme are exercised by tests as intended kept surface (IN-01)"
    requirement: "RELI-01"
    verification:
      - kind: unit
        ref: "tests/core/test_models.py::test_any_differs_true_when_any_comparison_differs"
        status: pass
      - kind: unit
        ref: "tests/gui/test_theme.py::test_follower_reports_current_theme"
        status: pass
    human_judgment: false
  - id: D5
    description: "README setup instructions state the 3.11+ floor and no longer pin the 3.12 interpreter (IN-02)"
    requirement: "RELI-01"
    verification:
      - kind: manual
        ref: "README.md Setup section"
        status: pass
    human_judgment: false
duration: 25min
completed: 2026-09-26
status: complete
---

# Phase 01 Plan 07: Self-Comparison Guard and Review Hygiene Summary

**Comparing a file against itself is now impossible from either direction (adding it as a comparison, or promoting a listed comparison to target), and both cases explain what happened in the status bar instead of silently producing a misleading "no differences" table.**

## Performance
- **Duration:** 25min
- **Started:** 2026-09-26T22:07:00Z
- **Completed:** 2026-09-26T22:32:15Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- `add_compare_files` refuses any candidate path that resolves to the current target file -- including via a `./` segment or a symlink alias -- and shows `"Skipped '<basename>': it is already selected as the target file."` in the status bar.
- `set_target_file` evicts a newly chosen target from the comparison list (both `compare_files` and the `QListWidget`) and shows `"Removed '<basename>' from the comparison list: it is now the target file."`.
- A new module-level `_normalized_path(path) -> str` (`os.path.normcase(os.path.realpath(path))`) is the single identity function both checks share, so path aliases can never slip a self-comparison past a naive string comparison (closes 01-REVIEW.md WR-02, threats T-01-26/T-01-27).
- `ComparisonRow.any_differs` and `OsThemeFollower.current_theme` are confirmed as deliberately kept public surface for Phase 2/3 and 01-05 respectively, and are now exercised by tests instead of being untested dead code (closes 01-REVIEW.md IN-01).
- README's Setup section no longer tells contributors they need Python 3.12 specifically; it states the real `>=3.11` floor from `pyproject.toml` (closes 01-REVIEW.md IN-02).

## Task Commits
1. **Task 1 RED: failing tests for self-selection guard** - `ed7ca46` (test)
2. **Task 1 GREEN: refuse/evict self-selection with status-bar feedback** - `eb17d92` (feat)
3. **Task 2: cover kept public surface + fix README Python floor** - `38ff4bc` (test)

## Files Created/Modified
- `src/gdtf_comparer/gui/main_window.py` - adds `_normalized_path()`; `add_compare_files` refuses the target by normalized identity; `set_target_file` evicts a promoted target from the comparison list; both report via `statusBar()`.
- `tests/gui/test_file_selection.py` - new: `test_target_file_is_not_added_as_comparison`, `test_new_target_is_removed_from_comparison_list`, `test_same_file_via_alternate_path_is_detected`, `test_distinct_comparison_files_are_still_added`.
- `tests/core/test_models.py` - new: three `ComparisonRow.any_differs` behaviour tests.
- `tests/gui/test_theme.py` - adds `test_follower_reports_current_theme`.
- `README.md` - Setup section states "3.11 or newer" and uses `python3 -m venv .venv` / `py -3 -m venv .venv` instead of pinning `python3.12`.

## Decisions Made
- IN-01: keep both `any_differs` and `current_theme` rather than removing them -- they are consumed by Phase 2 (DIFF-01) and Phase 3 (EXPORT-02) plans and by 01-05's published `OsThemeFollower` interface respectively. Resolved with tests, not code changes (`git diff` against `core/models.py`, `gui/theme.py`, `pyproject.toml` is empty for this plan).
- The self-comparison guard was implemented purely in `gui/main_window.py` using stdlib `os.path`, per the plan's UI-02 constraint (no new `gdtf_comparer.core` import).

## Deviations from Plan

None - plan executed exactly as written.

**Total deviations:** 0.
**Impact:** None.

## Issues Encountered

None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
Ready for 01-08.

---
*Phase: 01-foundation-rebuild*
*Completed: 2026-09-26*

## Self-Check: PASSED

All created/modified files found on disk; all four task commits (`ed7ca46`, `eb17d92`, `38ff4bc`) plus the SUMMARY metadata commit (`936957c`) verified present in `git log`.
