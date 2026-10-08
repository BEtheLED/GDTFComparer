---
phase: 03-compare-profiles-export
reviewed: 2026-10-08T00:38:14Z
depth: standard
files_reviewed: 11
files_reviewed_list:
  - src/gdtf_comparer/gui/main_window.py
  - tests/gui/test_compare_list_match_indicator.py
  - tests/gui/test_profile_manage.py
  - tests/gui/test_profile_toolbar.py
  - src/gdtf_comparer/core/comparator.py
  - tests/core/test_comparator.py
  - tests/gui/test_attribute_selection.py
  - tests/gui/test_cross_fixture_rows.py
  - tests/gui/test_differences_only_toggle.py
  - tests/gui/test_namespaced_rows.py
  - tests/gui/test_unspecified_values.py
findings:
  critical: 0
  warning: 0
  info: 2
  total: 2
status: issues_found
---

# Phase 03: Code Review Report

**Reviewed:** 2026-10-08T00:38:14Z
**Depth:** standard
**Files Reviewed:** 11
**Status:** issues_found (2 non-blocking Info items remain open from the 03-04 review; no new issues found in the 03-05 gap-closure increment)

## Summary

This REVIEW.md now covers two review passes over phase 03:

1. **03-04** (original pass, 2026-10-04): `gui/main_window.py`'s profile
   toolbar restructure (G-03-1) and the per-file match-indicator dots
   (G-03-2). One Warning (stale match-indicator dots) was found and has
   since been **fixed** (commit `564217d`); two Info items remain open.
2. **03-05** (this incremental pass, 2026-10-08): the gap-closure plan for
   G-03-3, which changes `core/comparator.py` to match Beam rows across
   files by **position** (1st beam vs 1st beam, 2nd vs 2nd, ...) instead of
   by each file's own geometry-element name, and drops per-model
   Width/Height/Length dimension rows from the cross-file comparison
   entirely. Eight existing GUI tests across four files were rebaselined to
   the new positional contract, and one new GUI test file
   (`test_cross_fixture_rows.py`) and sixteen new core tests were added.

**03-05 assessment:** the new `_cross_file_attributes()` helper and its
integration into `compare()` were read line-by-line against
`core/extract.py`'s attribute-extraction contract, and independently
exercised against the real GDTF-parsing path (not just synthetic
`FixtureModel` objects) to rule out a hypothesized "beam with zero declared
attributes creates a position gap and silently misaligns later beams"
defect -- `extract._declared_values()` always yields all 6 `BEAM_ATTRIBUTES`
keys per geometry beam node (value `None` when undeclared), so no beam is
ever invisible to the position counter regardless of how little it
declares; the hypothesis did not hold up under an end-to-end repro. The
per-model dimension filter is scoped tightly enough (category +
non-fixture-level path + name membership in `extract.MODEL_ATTRIBUTES`) that
it cannot accidentally swallow a real comparison row given what
`extract.py` currently produces. All 8 rebaselined assertions and all 16 new
core tests were run (not just read) and pass, and the full suite (276
tests) passes with no other breakage, confirming the rebaseline is complete
and no dependent test elsewhere in the tree was missed. No Critical,
Warning, or new Info issues were found in the 03-05 file set.

The two Info items below originate from the 03-04 pass and concern
`gui/main_window.py`, which was not touched by 03-05 -- they remain open and
are carried forward unchanged.

## Warnings

### WR-01: Match indicator dots go stale during a re-run and after a failed re-run — **FIXED**

**Resolution (commit `564217d`):** `_reset_match_indicators()` is now called
from both `run_comparison` (right after `table_model.set_result(None)`) and
`on_comparison_failed` (same place). Two regression tests added to
`tests/gui/test_compare_list_match_indicator.py`:
`test_running_again_resets_stale_indicators_before_new_result` and
`test_failed_comparison_resets_stale_indicators_to_unknown`. Full suite
(258 tests, at the time of that fix) passes.

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

_Reviewed: 2026-10-08T00:38:14Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
