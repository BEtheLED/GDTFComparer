---
phase: 03-compare-profiles-export
reviewed: 2026-10-04T00:00:00Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - src/gdtf_comparer/gui/main_window.py
  - tests/gui/test_compare_list_match_indicator.py
  - tests/gui/test_profile_manage.py
  - tests/gui/test_profile_toolbar.py
findings:
  critical: 0
  warning: 0
  info: 2
  total: 2
status: issues_found
---

# Phase 03: Code Review Report

**Reviewed:** 2026-10-04T00:00:00Z
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found (WR-01 fixed post-review; 2 non-blocking Info items remain open)

## Summary

Incremental review of gap-closure plan 03-04, scoped only to what changed
since the prior review's diff base: (1) G-03-1, splitting the single-row
profile toolbar (`profile_row`) into two stacked `QHBoxLayout`s
(`profile_combo_row`, `profile_actions_row`) inside a `QVBoxLayout`, to stop
qt-material's chrome from clipping the dropdown/Save…/Manage widgets, and
raising the Attributes panel's drag floor from 220px to 240px; and (2)
G-03-2, a new per-file colored-dot match indicator on the "Compare with"
list, computed from the existing `ComparisonRow.differs` data with no new
comparison logic, reset to "unknown" on every file-list/target mutation and
recomputed through the existing `_apply_attribute_selection` call site.

Both changes are narrowly scoped, well-commented, and the new indexing logic
(`_update_match_indicators`) correctly matches `ComparisonRow.differs`'
documented per-comparison ordering and defensively re-verifies path
alignment between `compare_list` and `result.comparisons` before trusting
either's ordering. No security issues, crashes, or data-loss paths were
found. The one real gap is a stale-state bug: the match indicators are only
ever reset/recomputed on file-list changes and on a *successful*
`on_comparison_ready`, never when a new run starts or fails, so a dot can
keep showing a previous run's match/differs color after the data it
describes is no longer current.

## Warnings

### WR-01: Match indicator dots go stale during a re-run and after a failed re-run — **FIXED**

**Resolution (commit `564217d`):** `_reset_match_indicators()` is now called
from both `run_comparison` (right after `table_model.set_result(None)`) and
`on_comparison_failed` (same place). Two regression tests added to
`tests/gui/test_compare_list_match_indicator.py`:
`test_running_again_resets_stale_indicators_before_new_result` and
`test_failed_comparison_resets_stale_indicators_to_unknown`. Full suite
(258 tests) passes.

**File:** `src/gdtf_comparer/gui/main_window.py:547-577` (`run_comparison`), `871-879` (`on_comparison_failed`)

**Issue:** The feature's own stated invariant (`_update_match_indicators`
docstring, lines 686-701) is "Resets every indicator to unknown when there
is no current result... the dots always describe the comparison CURRENTLY
on screen, never a stale one." In practice this invariant is only enforced
inside `_update_match_indicators`/`_reset_match_indicators`, and those are
never called from `run_comparison` or `on_comparison_failed`:

- `run_comparison` (line 558) calls `self.table_model.set_result(None)` to
  clear the table before starting the worker, but does not reset the
  "Compare with" dots. While the new comparison runs, the dots keep showing
  the *previous* result's match/differs colors even though
  `table_model.result()` is already `None`.
- `on_comparison_failed` (line 871) also leaves `table_model.result()` as
  `None` after a failed re-run, and shows "Comparison failed" in the status
  bar, but never touches the dots either. If the user previously ran a
  successful comparison (dots showing green/red) and a later re-run against
  the same files fails (e.g. a file was deleted or became invalid on disk),
  the dots keep showing the *stale, no-longer-trustworthy* colors from the
  earlier successful run indefinitely, until the user changes the file list
  or attribute selection.

Given the feature's stated purpose (03-CONTEXT.md D-01: helping a user judge
whether a comparison file is safe to substitute for the target), a green dot
left over from a stale or failed run is a meaningfully misleading signal,
not just a cosmetic nit.

**Fix:** Reset the indicators at the start of `run_comparison` (so "in
progress" never shows a stale verdict) and in `on_comparison_failed`:

```python
def run_comparison(self) -> None:
    ...
    self.table_model.set_result(None)
    self._reset_match_indicators()  # add this
    self.run_button.setEnabled(False)
    ...

def on_comparison_failed(self, message: str) -> None:
    self.table_model.set_result(None)
    self._reset_match_indicators()  # add this
    self.statusBar().showMessage("Comparison failed")
    self._show_error(message)
```

## Info

### IN-01: `set_target_file("")` skips the match-indicator reset via an early return

**File:** `src/gdtf_comparer/gui/main_window.py:464-497`

**Issue:** `set_target_file` returns early when `path` is falsy (line
478-479), *before* reaching `self._reset_match_indicators()` at line 497.
Every current caller (the file dialog in `select_target_file`, and every
test) only ever passes a non-empty path, so this is not reachable today.
But `set_target_file` is a public method on `MainWindow`, and the empty-path
branch exists specifically to represent "no target selected" — if any future
caller (or a "Clear target" action) uses it that way, the Compare list's
dots would keep showing whatever match/differs state was last computed
against the now-cleared target, silently violating the same "never stale"
invariant WR-01 is about.

**Fix:** Move the reset above the early return, or add it to the empty-path
branch as well:

```python
self.target_file = path
self.target_edit.setText(path)

if not path:
    self._reset_match_indicators()
    return
```

### IN-02: `_reset_match_indicators` is a same-body wrapper around `_mark_all_compare_items_unknown`

**File:** `src/gdtf_comparer/gui/main_window.py:664-684`

**Issue:** `_reset_match_indicators` (lines 677-684) has no logic of its
own beyond calling `_mark_all_compare_items_unknown()` once; the two
docstrings describe the same action from two different "callers' intent"
angles, but there's no behavioral difference between the two methods today.
This is harmless, but it's an extra indirection a future reader has to trace
through for no functional reason, and increases the chance a future edit is
made to only one of the two names when both were intended to change
together.

**Fix:** Either inline `_mark_all_compare_items_unknown`'s body into
`_reset_match_indicators` and have `_update_match_indicators` call
`_reset_match_indicators()` directly for its own unknown-fallback paths, or
drop `_reset_match_indicators` and call `_mark_all_compare_items_unknown()`
directly from the three file-list mutators. Either removes the redundant
pass-through without losing either docstring's intent.

---

_Reviewed: 2026-10-04T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
