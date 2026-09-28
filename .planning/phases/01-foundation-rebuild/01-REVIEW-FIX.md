---
phase: 01-foundation-rebuild
fixed_at: 2026-09-28T03:37:41Z
review_path: /Users/brandon/GDTFComparer/.planning/phases/01-foundation-rebuild/01-REVIEW.md
iteration: 1
findings_in_scope: 2
fixed: 2
skipped: 0
status: all_fixed
---

# Phase 01: Code Review Fix Report

**Fixed at:** 2026-09-28T03:37:41Z
**Source review:** /Users/brandon/GDTFComparer/.planning/phases/01-foundation-rebuild/01-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 2 (CR-01 Critical, WR-01 Warning; IN-01 Info excluded by `fix_scope: critical_warning`)
- Fixed: 2
- Skipped: 0

**Verification environment:** an isolated git worktree at
`.claude/worktrees/rf-01-61887-1790566383` on temp branch
`gsd-reviewfix/01-61887`, fast-forwarded onto `main` and torn down after this
report was written. The shared project venv (`.venv/bin/python`, outside the
worktree) was used for all test runs via its absolute path, so `pytest-qt`/
`PySide6` were available without a worktree-local install.

## Fixed Issues

### CR-01: Column-width cap is applied to fixed columns too, and can make two different Element paths render as identical text

**Files modified:** `src/gdtf_comparer/gui/main_window.py`
**Commit:** `171a331`
**Applied fix:** Scoped the width-cap loop in `_fit_columns_to_contents` to
value columns only (`range(ComparisonTableModel.COL_TARGET, header.count())`)
instead of every header section, exactly as REVIEW.md's suggested fix shows.
`Category`/`Element`/`Attribute` are no longer clamped to
`MAX_COLUMN_WIDTH_PX`, so they keep their natural `resizeColumnsToContents()`
width and are never right-elided down to indistinguishable text. Updated the
method's docstring to explain why fixed columns are excluded (ties back to
CR-01 and the cell-vs-header elide-mode mismatch the review identified).

Reproduced the review's exact repro before fixing (a `MainWindow` with one row
whose `Element` label is a long geometry path): before the fix, the `Element`
column was clamped to 280px; after, it renders at its full natural width
(476px in my repro, matching the review's reported number) with no cap
applied. Ran `tests/gui/test_table_headers.py` and `tests/test_walking_skeleton.py`
(13 tests) plus the full suite (95 tests, pre-existing baseline) — all passed
with no changes needed to existing assertions, since the fixed-column cell
content in those tests (`"Category"`/`"Beam"`/`"BeamAngle"`) was already
narrower than the cap.

### WR-01: G-01-2's "no horizontal scrollbar" fix only holds for the single-comparison case the tests cover

**Files modified:** `src/gdtf_comparer/gui/main_window.py`, `tests/gui/test_table_headers.py`
**Commit:** `2134f3e`
**Applied fix:** Took REVIEW.md's option (b) rather than just documenting the
limit, since it closes the original G-01-2 UAT gap for the product's real
"any number of comparison files" use case. `_fit_columns_to_contents` now
computes an adaptive per-value-column cap: the smaller of
`MAX_COLUMN_WIDTH_PX` and an even share of the viewport width remaining after
the fixed `Category`/`Element`/`Attribute` columns
(`available_width // num_value_columns`), floored at a new
`MIN_VALUE_COLUMN_WIDTH_PX = 120` constant so a value column is never
squeezed to an unreadably narrow sliver when many comparison files are open
at once (at that point a horizontal scrollbar is accepted as the lesser
evil, matching the existing "user can still drag a column wider" escape
hatch). Updated the `MAX_COLUMN_WIDTH_PX` comment to describe it as the cap's
ceiling rather than the only cap value.

Added `test_many_comparisons_with_realistic_names_need_no_scrollbar` (and a
`_make_multi_comparison_result` helper alongside the existing
`_make_short_result`) to `tests/gui/test_table_headers.py`, using a target
plus 3 comparison files with realistic ~30-40 character fixture names (as
REVIEW.md's fix suggested), asserting `horizontalScrollBar().maximum() == 0`
and that every value column still respects `MAX_COLUMN_WIDTH_PX` as an upper
bound. This is the scenario REVIEW.md reproduced as still needing a
scrollbar pre-fix; it now passes.

Ran the full test suite after this change: 96 passed (95 pre-existing +
1 new), no regressions. `tests/gui/test_table_headers.py` alone: 7 passed
(was 6; the pre-existing `test_long_headers_are_capped_and_elided`,
target-plus-one-comparison case, still passes unchanged since the adaptive
cap reduces to `MAX_COLUMN_WIDTH_PX` at that column count on the default
1000px window).

## Skipped Issues

None — both in-scope findings were fixed.

---

_Fixed: 2026-09-28T03:37:41Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
