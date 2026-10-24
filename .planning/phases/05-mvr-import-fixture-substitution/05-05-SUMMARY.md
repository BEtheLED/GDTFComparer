---
phase: 05-mvr-import-fixture-substitution
plan: 05
subsystem: mvr-import-substitution
tags: [fixture-substitution, scoring, ranking, pyside6, qt-material]

requires:
  - phase: 05-mvr-import-fixture-substitution
    provides: "Plan 05-02's MVR import hardening and Plan 05-03's requirement_options/DEFAULT_DIRECTIONS/ATTRIBUTE_UNITS/attribute_unit widened requirements editor, both built on 05-01's tracer (core.substitution's Direction/MatchState/score_value/rank, gui.candidate_results.CandidateResultsModel, gui.substitution_window.SubstitutionWindow)"
provides:
  - "Final single-folder, case-insensitive, read-only inventory scan (D-12) with named failure rows below ranked candidates, never silently dropped"
  - "Friendly scan-summary wording built from five named templates plus a private pluralizer, covering no-requirements/empty-folder/nothing-readable/checked(+failures) in one consistent voice"
  - "rank_key() extracted and independently tested: ranking depends only on red count, yellow count and the file-name tie-break -- never manufacturer, file date or folder-listing order (D-11)"
  - "Scoring arithmetic pinned against all three Task 2 options' worked examples (even the two not chosen), plus boundary/zero-tolerance/negative-value/missing-value/beam-by-position edges"
  - "A plain-words legend above the Check Inventory results table, word tooltips on every requirement cell, and traffic-light colors proven visible on screen in both light and dark themes"
affects: []

actuals:
  tokens: 11900
  tasks: 3
  commits: 3
  plan_head_before: 68f33d163afb2042cc00c6989381968a227d1ba7
  plan_head_after: 6694d6c1fb933de33fcd6a4f9dd0390adee57c8f

tech-stack:
  added: []
  patterns:
    - "rank_key(score) extracted from rank() so SUB-04's fairness prohibition (only red/yellow counts and file name may ever decide order) is independently testable and documented, mirroring how 05-02 extracted readable_gdtf_spec/resolve_member_name as standalone, pinnable functions"
    - "A private _count() pluralizer duplicated into core.substitution rather than imported from core.mvr_repository (no cross-module private import), matching the plan's own explicit instruction"
    - "_display_or_not_listed() shared by CandidateResultsModel._display_value and _tooltip so a requirement cell's displayed text and its tooltip's \"Candidate: ...\" fragment can never disagree about a missing value"

key-files:
  created: []
  modified:
    - src/gdtf_comparer/core/substitution.py
    - src/gdtf_comparer/gui/candidate_results.py
    - src/gdtf_comparer/gui/substitution_window.py
    - tests/core/test_substitution.py
    - tests/gui/test_candidate_results.py

key-decisions:
  - "scan_summary_message rewritten onto five named templates (NO_REQUIREMENTS_MESSAGE, NO_GDTF_FILES_TEMPLATE, NONE_READABLE_TEMPLATE, CHECKED_TEMPLATE, UNREADABLE_SUFFIX_TEMPLATE) instead of inline f-strings, so each SUB-04 wording guarantee has its own template to test and reuse from the GUI layer"
  - "Task 2's RED step (writing the scoring-edge tests) required zero production code changes: 05-01's score_value/_at_most/_tolerance_amount already matched every worked example from all three tolerance options, every boundary, zero tolerance, negative targets, missing/mismatched values and beam-by-position matching. Only the docstring was expanded to state the chosen option in the user's own words plus the shared rules, as the plan's action step required"
  - "The docstring for scan_candidate_folder was reworded to avoid the literal substring \"os.walk\" (even in prose explaining it is never used), since the acceptance grep `! grep -n \"os.walk\" ...` checks the whole file text, not just code"

requirements-completed: [SUB-04]

coverage:
  - id: D1
    description: "Check Inventory scans only the chosen folder itself (never a subfolder), keeps every *.gdtf file regardless of letter case, ignores every other file, and touches nothing in the folder"
    requirement: SUB-04
    verification:
      - kind: unit
        ref: "tests/core/test_substitution.py#test_scans_only_gdtf_files_in_that_folder"
        status: pass
      - kind: unit
        ref: "tests/core/test_substitution.py#test_folder_is_never_modified"
        status: pass
    human_judgment: false
  - id: D2
    description: "Duplicate GDTF files (byte-identical or same manufacturer/model) are scored and listed as separate rows, never merged"
    requirement: SUB-04
    verification:
      - kind: unit
        ref: "tests/core/test_substitution.py#test_duplicates_are_not_merged"
        status: pass
    human_judgment: false
  - id: D3
    description: "Empty folder, no-readable-files, and no-requirements-marked edges each get their own distinct, correctly-worded summary message; a single readable candidate gives a ranked list of one"
    requirement: SUB-04
    verification:
      - kind: unit
        ref: "tests/core/test_substitution.py#test_empty_folder"
        status: pass
      - kind: unit
        ref: "tests/core/test_substitution.py#test_nothing_readable"
        status: pass
      - kind: unit
        ref: "tests/core/test_substitution.py#test_no_requirements_skips_scoring"
        status: pass
      - kind: unit
        ref: "tests/core/test_substitution.py#test_single_candidate"
        status: pass
      - kind: unit
        ref: "tests/core/test_substitution.py#test_summary_wording"
        status: pass
    human_judgment: false
  - id: D4
    description: "Every inventory file that can't be read appears as its own greyed failure row below the ranked candidates, naming the file and the plain reason, counted in the summary and through the real window"
    requirement: SUB-04
    verification:
      - kind: unit
        ref: "tests/core/test_substitution.py#test_unreadable_folder_raises_friendly_error"
        status: pass
      - kind: automated_ui
        ref: "tests/gui/test_candidate_results.py#test_unreadable_files_listed_below_candidates"
        status: pass
      - kind: automated_ui
        ref: "tests/gui/test_candidate_results.py#test_empty_folder_message_in_window"
        status: pass
    human_judgment: false
  - id: D5
    description: "Green/yellow/red scoring matches the user's chosen option exactly at every edge: all three tolerance options' worked examples, boundaries (including float noise), zero tolerance, negative targets, missing/mismatched values, and beam attributes matched by position"
    requirement: SUB-04
    verification:
      - kind: unit
        ref: "tests/core/test_substitution.py#test_score_and_rank"
        status: pass
      - kind: unit
        ref: "tests/core/test_substitution.py#test_worked_examples_from_decision"
        status: pass
      - kind: unit
        ref: "tests/core/test_substitution.py#test_formula_for_each_option"
        status: pass
      - kind: unit
        ref: "tests/core/test_substitution.py#test_boundaries_take_better_color"
        status: pass
      - kind: unit
        ref: "tests/core/test_substitution.py#test_zero_tolerance"
        status: pass
      - kind: unit
        ref: "tests/core/test_substitution.py#test_negative_values"
        status: pass
      - kind: unit
        ref: "tests/core/test_substitution.py#test_missing_and_mismatched_values_are_red"
        status: pass
      - kind: unit
        ref: "tests/core/test_substitution.py#test_beams_match_by_position"
        status: pass
    human_judgment: false
  - id: D6
    description: "Candidates rank by fewest reds then fewest yellows then file name only -- manufacturer, file dates and the operating system's own listing order never influence order, including a case-only file-name tie on a case-sensitive filesystem"
    requirement: SUB-04
    verification:
      - kind: unit
        ref: "tests/core/test_substitution.py#test_ranking_ignores_everything_but_lights"
        status: pass
    human_judgment: false
  - id: D7
    description: "Traffic-light colors paint on screen (not just in model data) in both light and dark qt-material themes, every requirement cell's tooltip explains its color in words, the Result column counts in words, and a plain-words legend sits above the table"
    verification:
      - kind: automated_ui
        ref: "tests/gui/test_candidate_results.py#test_traffic_lights_paint_in_both_themes"
        status: pass
      - kind: automated_ui
        ref: "tests/gui/test_candidate_results.py#test_cell_tooltips_explain_in_words"
        status: pass
      - kind: automated_ui
        ref: "tests/gui/test_candidate_results.py#test_result_column_counts_in_words"
        status: pass
      - kind: automated_ui
        ref: "tests/gui/test_candidate_results.py#test_legend_shown_above_results"
        status: pass
    human_judgment: false
  - id: D8
    description: "Only one inventory check runs at a time: the button is disabled for the whole check, a second click starts no second scan, results appear complete in one step or not at all, a new check replaces old results wholesale, and a failed check clears them with one plain-text dialog"
    requirement: SUB-04
    verification:
      - kind: automated_ui
        ref: "tests/gui/test_candidate_results.py#test_check_button_disabled_while_checking"
        status: pass
      - kind: automated_ui
        ref: "tests/gui/test_candidate_results.py#test_new_check_replaces_results"
        status: pass
      - kind: automated_ui
        ref: "tests/gui/test_candidate_results.py#test_failed_check_clears_results"
        status: pass
    human_judgment: false
  - id: D9
    description: "A human visually confirms the green/yellow/red cells are easy to tell apart and the legend matches the colors, in both light and dark mode, on a real folder and a real saved requirements file"
    human_judgment: true
    rationale: "Collected into the end-of-phase UAT per workflow.human_verify_mode = end-of-phase; the Task 3 human-check step was not executed by this worktree agent and requires a human looking at the actual rendered window."

duration: ~25min
completed: 2026-10-24
status: complete
---

# Phase 5 Plan 5: Substitution Scoring, Ranking and Readability Widening Summary

**Final single-folder read-only inventory scan with named failure rows, scoring pinned against all three Task 2 tolerance options at every edge (not just the chosen one), fairness-only ranking proven invariant to manufacturer/file-date/listing-order, and a plain-words legend with on-screen traffic-light colors verified in both light and dark themes.**

## Performance

- **Duration:** ~25 min
- **Completed:** 2026-10-24
- **Tasks:** 3 (1 tracer, 2 auto/tdd)
- **Files modified:** 5 (0 created, 5 modified)

## Accomplishments

- `core.substitution.scan_candidate_folder`/`scan_summary_message` finalized: a single, non-recursive, case-insensitive `.gdtf` listing that never writes, renames or creates anything in the inventory folder (proven by `test_folder_is_never_modified` comparing a full recursive byte+mtime snapshot before and after); duplicate files are kept as separate rows; empty-folder, nothing-readable and no-requirements-marked each get their own distinct wording built from five named templates (`NO_REQUIREMENTS_MESSAGE`, `NO_GDTF_FILES_TEMPLATE`, `NONE_READABLE_TEMPLATE`, `CHECKED_TEMPLATE`, `UNREADABLE_SUFFIX_TEMPLATE`) plus a private `_count()` pluralizer mirroring `core.mvr_repository._count`'s shape.
- `rank_key()` extracted from `rank()`: the sort key (red count, yellow count, file name casefold, file name, source path) is now independently documented and tested as the *only* fields SUB-04's fairness prohibition allows — `test_ranking_ignores_everything_but_lights` proves manufacturer, `os.listdir` order and file mtimes never change the result, and (on a case-sensitive filesystem) a case-only file-name tie breaks to exact spelling.
- `gui.candidate_results.CandidateResultsModel` now appends a failure row for every file that couldn't be read, below the ranked candidates: `FAILURE_ROW_ROLE`, `FAILURE_FIXTURE_TEXT`, a gray `ForegroundRole`, the full path as a tooltip on the file column, and explicitly no `BackgroundRole`/`MATCH_STATE_ROLE` on its requirement cells (there is nothing to color). Proven through the real `SubstitutionWindow` in `test_unreadable_files_listed_below_candidates`.
- Every scoring edge from 05-01's Task 2 decision is now pinned by tests, including the two tolerance options the user did *not* choose (`test_formula_for_each_option` monkeypatches all three option triples and asserts each one's worked examples) — the RED step confirmed 05-01's `score_value`/`_at_most`/`_tolerance_amount` already matched every edge exactly, so no production scoring logic changed; only `score_value`'s docstring was expanded to state the chosen option in the user's own three-light words plus the rules every option shares.
- `gui.candidate_results.LEGEND_TEXT` (the user's own words from 05-CONTEXT.md) now sits in `gui.substitution_window.SubstitutionWindow.legend_label`, directly above the results table on the Check Inventory tab. Requirement-cell tooltips and display text now share one `_display_or_not_listed()` helper, so a missing value reads "Not listed" consistently in both places (previously the tooltip fell back to `format_value(None)` == "N/A", disagreeing with the cell's own displayed text).
- `test_traffic_lights_paint_in_both_themes` (parametrized over `LIGHT_THEME`/`DARK_THEME`) proves the green/yellow/red `BackgroundRole` brushes actually render on screen — sampling real pixels through `view.viewport().grab()` — not just that model data carries the right role, closing the same qt-material-suppresses-BackgroundRole gap Phase 2's delegate finding first identified.
- SUB-04's concurrency guarantees (button disabled for the whole check, a second click starts no second scan, results appear complete in one step or not at all, a new check replaces old results wholesale, a failed check clears them with one plain-text dialog) were all already wired by 05-01/05-02; this plan added tests (`test_check_button_disabled_while_checking`, `test_new_check_replaces_results`, `test_failed_check_clears_results`) that pin the existing behavior rather than changing it.

## Task Commits

Each task was committed atomically:

1. **Task 1: End-to-end "a shop checks a messy real folder" (tracer)** - `c9f38a3` (feat)
2. **Task 2: Green/yellow/red follow the user's chosen rule exactly, ranking is fair** - `adf6981` (test)
3. **Task 3: Colors visible in both themes, words everywhere, one check at a time** - `6694d6c` (feat)

**Plan metadata:** (this SUMMARY, committed separately per the worktree wave protocol — STATE/ROADMAP/REQUIREMENTS updates are owned by the orchestrator after this plan's wave completes)

## Files Created/Modified

- `src/gdtf_comparer/core/substitution.py` - Final scan templates (`NO_REQUIREMENTS_MESSAGE`, `NO_GDTF_FILES_TEMPLATE`, `NONE_READABLE_TEMPLATE`, `CHECKED_TEMPLATE`, `UNREADABLE_SUFFIX_TEMPLATE`), private `_count()`, `rank_key()`, and an expanded `score_value` docstring
- `src/gdtf_comparer/gui/candidate_results.py` - Failure rows (`FAILURE_ROW_ROLE`, `FAILURE_FIXTURE_TEXT`), `LEGEND_TEXT`, and the shared `_display_or_not_listed()` helper fixing the tooltip/display-text "Not listed" mismatch
- `src/gdtf_comparer/gui/substitution_window.py` - `self.legend_label`, placed above `results_view` on the Check Inventory tab
- `tests/core/test_substitution.py` - New file: scan rules, read-only proof, duplicates, empty/nothing-readable/single-candidate/no-requirements edges, summary wording, missing-folder error, scoring pinned against all three Task 2 options, boundaries, zero tolerance, negative values, missing/mismatched values, beam-by-position matching, and fairness-only ranking
- `tests/gui/test_candidate_results.py` - New file: failure rows through the real window, empty-folder message, on-screen colors in both themes, word tooltips, Result-column word counts, the legend's position/text, and SUB-04's concurrency guarantees

## Decisions Made

See `key-decisions` in frontmatter. The most notable: Task 2's RED step required zero production scoring changes, because 05-01's `score_value`/`_at_most`/`_tolerance_amount` already implemented every edge this plan's tests probe — including the two tolerance options (b and c) the user did not choose, which this plan pins anyway so the arithmetic can never silently drift for an option a future plan might expose.

## Deviations from Plan

None — plan executed exactly as written. One wording fix was needed to satisfy the plan's own acceptance criteria: `scan_candidate_folder`'s docstring originally explained "never a recursive directory walk" using the literal phrase "os.walk", which the acceptance grep `! grep -n "os.walk" ...` treats as a hit regardless of whether it's code or prose. Reworded to "a single, non-recursive directory listing" with the identical meaning — not a behavior change, just docstring wording to pass the plan's own check.

## Issues Encountered

None. All three tasks' `<verify>` commands (the new/changed test files alone, and the full suite with `-W error::DeprecationWarning`) passed on the first attempt after implementation, and the full suite was run twice more after the final commit to rule out flakiness (462 passed both times, no change in count or outcome).

## User Setup Required

None — no external service configuration required; this plan only changed `core/substitution.py`, `gui/candidate_results.py` and `gui/substitution_window.py` plus their tests.

## Next Phase Readiness

This is the final plan in Phase 5 (MVR Import & Fixture Substitution). With 05-01 through 05-05 all complete, the phase is now feature-complete: MVR import collapsing fixture instances into unique types, hardened against every damaged/hostile file shape; a per-fixture-type requirements editor with per-type memory, smart defaults and units; an atomic, schema-versioned, cross-machine-safe requirements sidecar file; and a folder-scan Check Inventory view that is read-only, fair, and readable in both themes with failure rows and word explanations throughout.

Remaining before the phase can be marked verified: the end-of-phase UAT must collect Task 3's human-check (visual confirmation that green/yellow/red are distinguishable in both themes on a real folder and a real saved requirements file) — this is coverage item D9 above, deferred by design per `workflow.human_verify_mode = end-of-phase`, not a gap in this plan's own automated verification.

No blockers.

## Self-Check: PASSED

- FOUND: src/gdtf_comparer/core/substitution.py
- FOUND: src/gdtf_comparer/gui/candidate_results.py
- FOUND: src/gdtf_comparer/gui/substitution_window.py
- FOUND: tests/core/test_substitution.py
- FOUND: tests/gui/test_candidate_results.py
- FOUND commit: c9f38a3 (Task 1)
- FOUND commit: adf6981 (Task 2)
- FOUND commit: 6694d6c (Task 3)

---
*Phase: 05-mvr-import-fixture-substitution*
*Completed: 2026-10-24*
