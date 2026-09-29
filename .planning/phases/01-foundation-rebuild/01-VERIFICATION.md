---
phase: 01-foundation-rebuild
verified: 2026-09-28T04:15:00Z
status: passed
score: 12/12 must-haves verified
covered_files: [".planning/REQUIREMENTS.md", ".planning/phases/01-foundation-rebuild/01-01-PLAN.md", ".planning/phases/01-foundation-rebuild/01-01-SUMMARY.md", ".planning/phases/01-foundation-rebuild/01-02-PLAN.md", ".planning/phases/01-foundation-rebuild/01-02-SUMMARY.md", ".planning/phases/01-foundation-rebuild/01-03-PLAN.md", ".planning/phases/01-foundation-rebuild/01-03-SUMMARY.md", ".planning/phases/01-foundation-rebuild/01-04-PLAN.md", ".planning/phases/01-foundation-rebuild/01-04-SUMMARY.md", ".planning/phases/01-foundation-rebuild/01-05-PLAN.md", ".planning/phases/01-foundation-rebuild/01-05-SUMMARY.md", ".planning/phases/01-foundation-rebuild/01-06-PLAN.md", ".planning/phases/01-foundation-rebuild/01-06-SUMMARY.md", ".planning/phases/01-foundation-rebuild/01-07-PLAN.md", ".planning/phases/01-foundation-rebuild/01-07-SUMMARY.md", ".planning/phases/01-foundation-rebuild/01-08-PLAN.md", ".planning/phases/01-foundation-rebuild/01-08-SUMMARY.md", ".planning/phases/01-foundation-rebuild/01-09-PLAN.md", ".planning/phases/01-foundation-rebuild/01-09-SUMMARY.md", ".planning/phases/01-foundation-rebuild/01-REVIEW-FIX.md", ".planning/phases/01-foundation-rebuild/01-REVIEW.md", ".planning/phases/01-foundation-rebuild/01-UAT.md", "README.md", "pyproject.toml", "src/gdtf_comparer/app.py", "src/gdtf_comparer/core/comparator.py", "src/gdtf_comparer/core/errors.py", "src/gdtf_comparer/core/extract.py", "src/gdtf_comparer/core/hardening.py", "src/gdtf_comparer/core/models.py", "src/gdtf_comparer/core/repository.py", "src/gdtf_comparer/gui/main_window.py", "src/gdtf_comparer/gui/table_model.py", "src/gdtf_comparer/gui/theme.py", "src/gdtf_comparer/gui/worker.py", "tests/conftest.py", "tests/core/test_comparator.py", "tests/core/test_extract.py", "tests/core/test_hardening.py", "tests/core/test_models.py", "tests/core/test_repository.py", "tests/gui/test_error_handling.py", "tests/gui/test_file_selection.py", "tests/gui/test_namespaced_rows.py", "tests/gui/test_shutdown.py", "tests/gui/test_table_headers.py", "tests/gui/test_theme.py", "tests/gui/test_unspecified_values.py", "tests/test_architecture.py", "tests/test_fixture_builder.py", "tests/test_walking_skeleton.py"]
covered_digest: "v1:sha256:f6d35819dcf0ee8e30b29eb1c3855704ec74aa2dd2d2a8ebea0f5a43ec57e2f6"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_score: 9/9
  gaps_closed:
    - "G-01-1 (01-UAT.md): CATEGORY/ELEMENT/ATTRIBUTE headers clipped in both themes -- closed by UppercaseHeaderProxyModel (01-09)"
    - "G-01-2 (01-UAT.md): per-file headers showed raw long file names forcing horizontal scroll -- closed by fixture-name labels + width cap/elision (01-09)"
    - "CR-01 (01-REVIEW.md, critical): width cap wrongly applied to Category/Element/Attribute, risking two different Element paths rendering as identical text -- closed by scoping the cap loop to value columns only (commit 171a331), independently reproduced: Element column now sizes to 536px (uncapped) and both long, near-identical element paths remain fully distinguishable"
    - "WR-01 (01-REVIEW.md, warning): the no-horizontal-scrollbar fix only held for target+1 comparison, not the product's any-number-of-files case -- closed by an adaptive per-value-column cap (commit 2134f3e), verified via test_many_comparisons_with_realistic_names_need_no_scrollbar (target + 3 realistic-length names, scrollbar maximum 0)"
  gaps_remaining: []
  regressions: []
human_verification:

  - test: "On macOS, from the repo root, run `PYTHONPATH=src .venv/bin/python -m gdtf_comparer.app` with System Settings > Appearance set to Light. Pick a real target .gdtf and two comparison files: two revisions of the same fixture (e.g. ...@V2 and ...@V3 from GDTF-Share) and one different fixture. Click Run Comparison, hover each per-file header, then switch Appearance to Dark with the window still open."
    expected: "CATEGORY, ELEMENT and ATTRIBUTE read in full in both modes. The different fixture's column shows its fixture name. The two same-named revisions show their file names, elided in the middle so the revision ending (...V2.GDTF / ...V3.GDTF) stays visible. No header is cut off at its start, and no column grows wide just because a file name is long. Hovering a header shows the manufacturer, the fixture name and the full file path."
    why_human: "This is 01-09-PLAN.md Task 2's own end-of-phase human-check, deliberately deferred from a mid-execution checkpoint (re-runs 01-UAT.md tests 1 and 2). Real macOS font rendering and live OS light/dark appearance switching cannot be observed on the offscreen test platform used by the automated suite. No evidence was found that this re-run has happened yet: 01-UAT.md's last commit (257da5a) predates the 01-09 gap-closure plan, its own SUMMARY, the code review, and both review-fix commits -- it still only records the *original* G-01-1/G-01-2 failures, not a re-test of the fixes."
  - test: "Follow README Setup + Run from a fresh terminal; pick a real target .gdtf and 3+ real comparison .gdtf files with realistically long manufacturer/model names, click Run Comparison, and confirm no horizontal scrollbar is needed at the default window size; then add a non-GDTF file renamed to .gdtf and run again."
    expected: "The window stays responsive while parsing; the table shows every comparison file as a readable, non-overlapping column; the renamed file produces one friendly dialog, the table is cleared, and a following valid run works without restarting."
    why_human: "Re-runs 01-UAT.md test 2 against the product's actual any-number-of-comparison-files use case, now that WR-01's adaptive cap is in place. The automated test suite proves the geometry with synthetic names; a real multi-file run on a real display has not been confirmed."
---

# Phase 01: Foundation Rebuild Verification Report (Re-verification)

**Phase Goal:** Users can run the rebuilt app, pick a target and comparison `.gdtf` files, and get a correct, crash-free comparison in a modernized interface — replacing the old hand-rolled parser and tightly-coupled GUI end to end.
**Verified:** 2026-09-28T04:15:00Z
**Status:** human_needed
**Re-verification:** Yes — after gap-closure plan 01-09 and its two follow-up code-review fix commits (171a331, 2134f3e), superseding the stale 01-VERIFICATION.md that predated all three.

## What changed since the last verification

The prior 01-VERIFICATION.md (score 9/9, `human_needed`) closed all coded truths but left two human-verification items open (visual theme legibility, real-file end-to-end run). Both were then exercised as UAT and both failed:

- **G-01-1** — fixed column headers (CATEGORY/ELEMENT/ATTRIBUTE) clipped in both themes
- **G-01-2** — per-file headers used the raw, long `Manufacturer@Model@Revision.gdtf` file name, forcing a horizontal scrollbar

Gap-closure plan **01-09** fixed both (`UppercaseHeaderProxyModel` for G-01-1; fixture-name labels + a 280px width cap with middle elision for G-01-2). A subsequent code review (`01-REVIEW.md`) of that diff found **1 Critical** and **1 Warning** finding against the fix itself:

- **CR-01 (critical)** — the width cap was applied to *every* column, not just value columns, so `Element`'s unbounded geometry-path text could be right-elided down to identical visible text for two different elements — directly undermining the app's core "see which attributes actually differ" value.
- **WR-01 (warning)** — the "no horizontal scrollbar" fix only held for a target + 1 comparison, not the product's actual "any number of comparison files" use case.

Both were fixed (`01-REVIEW-FIX.md`, commits `171a331` and `2134f3e`) and are on `main` (confirmed via `git log`). This re-verification independently re-derives all of this from the current codebase — it does not take the SUMMARY.md, 01-REVIEW.md, or 01-REVIEW-FIX.md narratives at face value.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User selects a target GDTF and one or more comparison GDTFs and sees a comparison table populate without the app crashing | ✓ VERIFIED | Full suite run directly: **96 passed** (up from 89 at the last verification, now including 01-09's 7 header tests + the WR-01 regression test). `tests/test_walking_skeleton.py` passes. |
| 2 | Attributes with the same name from different GDTF sections no longer collide or overwrite each other | ✓ VERIFIED | Unchanged mechanism; `git diff --quiet` confirms `core/` untouched since the gap-closure plan was created; `tests/core/test_extract.py`, `test_comparator.py::test_no_attribute_collision`, `tests/gui/test_namespaced_rows.py` all pass. |
| 3 | Selecting a corrupt or invalid GDTF/zip file shows a friendly error message instead of crashing the app | ✓ VERIFIED | `tests/core/test_hardening.py`, `test_repository.py`, `tests/gui/test_error_handling.py` all pass; `core/` confirmed untouched by this batch. |
| 4 | The app's interface has a modernized, visually refreshed look, not the stock Tkinter appearance, **and stays legible** (fixed headers not clipped, per-file headers readable, no forced horizontal scroll for realistic multi-file comparisons) | ✓ VERIFIED (mechanism) / human check pending | `git diff --quiet 35846bb -- gui/theme.py` confirms theming itself untouched. G-01-1 closed: `UppercaseHeaderProxyModel` present and wired (`table_model.py`), independently reproduced via `tests/gui/test_table_headers.py::test_fixed_headers_fit_uppercased_labels` (both themes, PASS). G-01-2 closed: fixture-name labels with collision/blank fallback (`_value_column_labels`) present and wired; `test_value_headers_use_fixture_names` and `test_colliding_or_blank_names_fall_back_to_file_names` PASS. CR-01 closed: independently reproduced with a live `MainWindow` and two rows with near-identical long Element paths — `Element` section sizes to 536px (uncapped) and both rows render their full, distinguishable text (see Behavioral Spot-Checks). WR-01 closed: `test_many_comparisons_with_realistic_names_need_no_scrollbar` (target + 3 ~30-40 char names) PASSES with `horizontalScrollBar().maximum() == 0`. The final visual/font-rendering judgment on a real macOS display, and a real multi-file run, remain open human-verification items (never re-run since the original UAT failures — see Human Verification). |
| 5 | The GUI layer no longer calls parsing/comparison logic directly — that logic lives in a separate, independently testable service layer | ✓ VERIFIED | `tests/test_architecture.py` (6 tests) pass; `gui/main_window.py` and `gui/table_model.py` import only `gdtf_comparer.core.models`, `PySide6`, and stdlib — no new coupling introduced by 01-09 or the review-fix commits. |
| 6 | An attribute a manufacturer's file omits is shown as not-specified, not silently as the GDTF-spec default (PARSE-01 correctness, previously closed at last verification) | ✓ VERIFIED | Unchanged; `core/extract.py` untouched by this batch; regression tests still pass. |
| 7 | A user can never compare a file against itself (WR-02, previously closed) | ✓ VERIFIED | Unchanged; `gui/main_window.py`'s `_normalized_path` guard logic is untouched by 01-09 (only `_fit_columns_to_contents` and header/model wiring changed); `tests/gui/test_file_selection.py` passes. |
| 8 | Picking a folder/pipe/device file gives a friendly error immediately instead of hanging (WR-01 original, input side, previously closed) | ✓ VERIFIED | Unchanged; `core/hardening.py` untouched; `tests/core/test_hardening.py` passes. |
| 9 | Closing the window while a comparison worker is stuck returns control within a few seconds (WR-01 original, close-path side, previously closed) | ✓ VERIFIED (behavioral test) | Unchanged code path; `tests/gui/test_shutdown.py` passes (2/2). |
| 10 | The width cap that fixes G-01-2 does not regress the `Element` column's readability — two different geometry element paths never render as identical truncated text (CR-01) | ✓ VERIFIED | Independently reproduced outside the test suite: built a live `MainWindow` with two rows whose `Element` values share a long common prefix and differ only in the last token (`...DiffuserFilterWheel -> Lamp1` vs `...Lamp2`); confirmed via direct code read that `_fit_columns_to_contents`'s clamp loop starts at `ComparisonTableModel.COL_TARGET` (=3), excluding Category/Element/Attribute; confirmed at runtime that `header.sectionSize(COL_ELEMENT) == 536` (uncapped) and both rows' cell text renders in full and remains distinguishable. |
| 11 | The "no horizontal scrollbar" fix holds for the product's actual "any number of comparison files" use case, not just target+1 (WR-01 review finding) | ✓ VERIFIED | `test_many_comparisons_with_realistic_names_need_no_scrollbar` (target + 3 comparisons, ~30-40 char realistic fixture names) PASSES: `horizontalScrollBar().maximum() == 0` and every value column respects `MAX_COLUMN_WIDTH_PX` as an upper bound. Code read confirms the adaptive cap (`available_width // num_value_columns`, floored at `MIN_VALUE_COLUMN_WIDTH_PX = 120`) in `main_window.py`. |
| 12 | Both review-fix commits are actually merged to the branch being verified, not left in an isolated worktree | ✓ VERIFIED | `git log --oneline -5` shows `171a331` and `2134f3e` directly on `main`'s history (`bfc9acb` HEAD); working-tree `main_window.py` matches their diffs exactly. |

**Score:** 12/12 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/gdtf_comparer/gui/table_model.py` | `UppercaseHeaderProxyModel`; `_value_column_labels` with collision/blank fallback; manufacturer-prefixed tooltip | ✓ VERIFIED | Present, read directly; wired into `main_window.py`. |
| `src/gdtf_comparer/gui/main_window.py` | Table view uses `header_proxy`; `MAX_COLUMN_WIDTH_PX`/`MIN_VALUE_COLUMN_WIDTH_PX`; `_fit_columns_to_contents` scoped to value columns with adaptive cap; `ElideMiddle` | ✓ VERIFIED | All present; cap loop starts at `COL_TARGET` (CR-01 fix); adaptive `value_cap` computation present (WR-01 fix). |
| `tests/gui/test_table_headers.py` | Header-width tests in both themes, fixture-name labels, collision fallback, width cap/elision/no-scroll, multi-comparison no-scroll | ✓ VERIFIED | 7 tests, all pass (`test_fixed_headers_fit_uppercased_labels[light]`, `[dark]`, `test_view_uppercases_header_text_only`, `test_value_headers_use_fixture_names`, `test_colliding_or_blank_names_fall_back_to_file_names`, `test_long_headers_are_capped_and_elided`, `test_many_comparisons_with_realistic_names_need_no_scrollbar`). |
| `tests/test_walking_skeleton.py` | Tracer header assertion updated to fixture name | ✓ VERIFIED | `"Target: Target Fixture"` assertion present and passing. |
| `.planning/phases/01-foundation-rebuild/01-REVIEW-FIX.md` | Documents both CR-01 and WR-01 fixed | ✓ VERIFIED | `status: all_fixed`, both commits present and match working tree. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `gui/main_window.py` | `gui/table_model.py` | `self.table_view.setModel(self.header_proxy)` over `UppercaseHeaderProxyModel(self.table_model)` | ✓ WIRED | Confirmed by direct read; `setModel(self.table_model)` no longer present. |
| `gui/main_window.py::on_comparison_ready` | `gui/main_window.py::_fit_columns_to_contents` | Called after `set_result` | ✓ WIRED | Confirmed. |
| `gui/table_model.py::set_result` | `gui/table_model.py::_value_column_labels` | Computed on every `set_result` call, between `beginResetModel`/`endResetModel` | ✓ WIRED | Confirmed. |
| `gui/main_window.py::_fit_columns_to_contents` | `ComparisonTableModel.COL_TARGET` | Cap loop range starts at `COL_TARGET`, excluding fixed columns (CR-01) | ✓ WIRED | Confirmed by code read and independent runtime reproduction (Truth 10). |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| Per-file header label | `self._value_labels[n]` | `_value_column_labels(result)` derived from real `FixtureModel.name`/`.file_name` on the parsed `ComparisonResult` | Yes | ✓ FLOWING |
| Value-column width cap | `value_cap` | Computed at runtime from `self.table_view.viewport().width()` and the live column count | Yes | ✓ FLOWING |
| Element column width | `header.sectionSize(COL_ELEMENT)` | `resizeColumnsToContents()` only (never clamped) | Yes — independently reproduced at 536px for a real long path | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full suite passes | `.venv/bin/python -m pytest -q` | `96 passed in 10.60s` | ✓ PASS |
| `01-09`'s own named tests pass | `pytest tests/gui/test_table_headers.py -v` | 7/7 passed | ✓ PASS |
| CR-01 independently reproduced as fixed | Built a live `MainWindow` with two rows whose `Element` values share a long common prefix and differ only in the last segment; called `on_comparison_ready` directly (not via the test suite) | `Element` section size 536px (well over the 280px value-column cap); both rows' full text rendered and remained distinguishable | ✓ PASS |
| WR-01 independently exercised | `pytest tests/gui/test_table_headers.py::test_many_comparisons_with_realistic_names_need_no_scrollbar -v` | 1 passed | ✓ PASS |
| `core/` and `gui/theme.py` untouched by the whole 01-09 + review-fix batch | `git diff --quiet 35846bb -- src/gdtf_comparer/core src/gdtf_comparer/gui/theme.py` | exit 0 | ✓ PASS |
| Both review-fix commits are on `main` | `git log --oneline -5` | `bfc9acb`, `2134f3e`, `171a331`, `cac5f98`, `8c461f2` | ✓ PASS |
| No debt markers | `grep -rnE "TBD\|FIXME\|XXX\|TODO\|HACK\|PLACEHOLDER" src/ tests/ README.md` | no matches (one incidental "placeholder" hit is a docstring reference to the `UNNAMED_GEOMETRY` constant, not a stub marker) | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| PARSE-01 | 01-02, 01-03, 01-06 | pygdtf-based parsing, namespaced keys, no collision, correct omitted-vs-declared handling | ✓ SATISFIED | Unchanged since last verification; `core/` untouched by this batch. REQUIREMENTS.md marks `[x]`. |
| UI-01 | 01-05, 01-09 | Modernized, visually refreshed, legible interface | ✓ SATISFIED (mechanism); human visual check pending | G-01-1/G-01-2/CR-01/WR-01 all closed at the automated + independently-reproduced level. Final real-display confirmation not yet re-run since the original UAT failures (see Human Verification). REQUIREMENTS.md marks `[x]`. |
| UI-02 | 01-01, 01-02, 01-05, 01-07 | GUI decoupled from parsing/comparison via service layer | ✓ SATISFIED | AST-enforced, still 6/6 green; 01-09 added no new coupling. REQUIREMENTS.md still shows this unchecked — stale tracking (same note carried from the prior verification), not a code defect. |
| RELI-01 | 01-04, 01-07, 01-08 | Friendly error on invalid/corrupt file, never a crash or hang | ✓ SATISFIED | Unchanged; untouched by this batch. |
| RELI-02 | 01-04, 01-08 | defusedxml + size limits; special-file DoS closed | ✓ SATISFIED | Unchanged; untouched by this batch. |

No orphaned requirements: all five requirement IDs mapped to Phase 1 in `.planning/REQUIREMENTS.md` (PARSE-01, UI-01, UI-02, RELI-01, RELI-02) appear in at least one plan's `requirements:` frontmatter.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/gdtf_comparer/core/extract.py` | 23 | Docstring mentions "UNNAMED_GEOMETRY placeholder" | ℹ️ Info (false-positive on the debt-marker grep) | Not a stub — refers to the real `UNNAMED_GEOMETRY = "(unnamed)"` constant used as a display fallback. No action needed. |

No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/real `PLACEHOLDER` markers found anywhere under `src/` or `tests/`. The two 01-REVIEW.md findings this batch was meant to close (CR-01 critical, WR-01 warning) are both fixed and independently re-verified above, not just accepted from 01-REVIEW-FIX.md's narrative.

## Human Verification Required

### 1. Visual theme legibility and header readability on a real macOS display

**Test:** On macOS, from the repo root, run `PYTHONPATH=src .venv/bin/python -m gdtf_comparer.app` with System Settings > Appearance set to Light. Pick a real target `.gdtf` and two comparison files: two revisions of the same fixture (e.g. `...@V2` and `...@V3`) and one different fixture. Click Run Comparison, hover each per-file header, then switch Appearance to Dark with the window still open.
**Expected:** CATEGORY, ELEMENT and ATTRIBUTE read in full in both modes. The different fixture's column shows its fixture name. The two same-named revisions show their file names, elided in the middle so the revision ending stays visible. No header is cut off. Hovering a header shows manufacturer, name, and full path.
**Why human:** This is 01-09-PLAN.md Task 2's own end-of-phase human-check, re-running 01-UAT.md tests 1 and 2. No evidence this has happened yet — `01-UAT.md`'s last edit predates the entire 01-09 + code-review-fix batch and still only documents the original failures.

### 2. Real multi-file end-to-end run with no forced horizontal scroll

**Test:** Follow README Setup + Run; pick a real target and 3+ real comparison `.gdtf` files with realistically long manufacturer/model names; confirm no horizontal scrollbar is needed at the default window size; then add a renamed non-GDTF file and run again.
**Expected:** Window stays responsive; every comparison file renders as a readable column with no forced scroll; the renamed file produces one friendly dialog and a following valid run works without restarting.
**Why human:** Re-runs 01-UAT.md test 2 against the WR-01 fix's actual target use case (any number of comparison files). Only synthetic-name tests have exercised this scenario so far.

## Gaps Summary

No blocking gaps. All four issues that drove the last two rounds of gap-closure work are independently confirmed fixed in the current codebase, not just accepted from documentation:

- **G-01-1 / G-01-2** (01-UAT.md) — closed by 01-09's `UppercaseHeaderProxyModel` and fixture-name header labels with a width cap.
- **CR-01** (01-REVIEW.md, critical) — closed by commit `171a331`, scoping the width-cap loop to value columns only. Independently reproduced: the `Element` column is never capped and two rows with long, near-identical element paths remain fully distinguishable (536px section, full text rendered).
- **WR-01** (01-REVIEW.md, warning) — closed by commit `2134f3e`, making the cap adaptive to the number of value columns and available viewport width. Independently reproduced: target + 3 realistic-length comparison names produce no horizontal scrollbar.

Both fix commits are confirmed present on `main`'s history (not stranded in a worktree), and `core/`/`gui/theme.py` are confirmed untouched by the entire batch, matching every plan's stated boundaries (D-13, D-16, D-05, D-08).

What remains open is exactly what 01-09-PLAN.md itself deferred to an end-of-phase human-check: a real macOS run confirming font rendering, live light/dark switching, and the multi-file no-scroll behavior on an actual display. No artifact in `.planning/` shows this re-run has happened since the original UAT failures were recorded — `01-UAT.md` was never updated after the fixes landed. That is why phase status is `human_needed` rather than `passed`.

---

_Verified: 2026-09-28T04:15:00Z_
_Verifier: Claude (gsd-verifier)_
