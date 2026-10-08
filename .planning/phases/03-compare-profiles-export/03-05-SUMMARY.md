---
phase: 03-compare-profiles-export
plan: 05
subsystem: core-comparator
tags: [gap-closure, comparator, cross-file-matching, gui-tests]

requires:
  - 03-04 (G-03-2 match indicator, D-06 profile status message)
provides:
  - Positional cross-file Beam row matching (compare()/_cross_file_attributes)
  - Per-model dimension row exclusion from cross-file comparison
affects:
  - src/gdtf_comparer/core/comparator.py
  - every GUI test fixture whose target/comparison files have different geometry or model names

actuals:
  tokens: 9293
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Per-file cross-file view built once per compare() call (_cross_file_attributes), never mutating FixtureModel.attributes or replacing the model carried on ComparisonResult"
    - "Position-based re-keying driven by first-seen order over an existing dict's .items(), reusing extraction's own document-order insertion rather than re-deriving it"

key-files:
  created:
    - tests/gui/test_cross_fixture_rows.py
  modified:
    - src/gdtf_comparer/core/comparator.py
    - tests/core/test_comparator.py
    - tests/gui/test_namespaced_rows.py
    - tests/gui/test_attribute_selection.py
    - tests/gui/test_unspecified_values.py
    - tests/gui/test_differences_only_toggle.py

key-decisions:
  - "Beam-level rows match across files by POSITION (1st beam vs 1st beam, 2nd vs 2nd, ...), never by name/fuzzy-matching/beam type -- user decision 2026-10-07, implemented exactly as specified, no alternative considered"
  - "Per-model Width/Height/Length rows are dropped from the cross-file comparison table and picker entirely, while extraction and FixtureModel.attributes keep storing them unchanged -- user decision 2026-10-07"
  - "The fix lives entirely in core/comparator.py's new _cross_file_attributes() helper, never in core/extract.py or core/models.py -- keeps AttributeKey's within-file semantics (D-11) and extraction's documented element_path meaning untouched, per the plan's explicit scope prohibition"

patterns-established:
  - "A per-file 'cross-file view' dict, built fresh inside compare() from a model's namespaced attributes, is the pattern for any future case where a row's cross-file identity needs to differ from its within-file identity"

requirements-completed: [ATTR-03]

coverage:
  - id: G-03-3-beam-position-matching
    description: "Beam-level attribute rows (BeamAngle, FieldAngle, PowerConsumption, LuminousFlux, ColorTemperature, BeamType) are matched across files by position (1st beam vs 1st beam, 2nd vs 2nd, ...) instead of by each file's own geometry element name, with document-order position assignment and true per-file N/A when a file has fewer beams at a position"
    requirement: ATTR-03
    verification:
      - kind: unit
        ref: "tests/core/test_comparator.py::test_beams_match_by_position_across_different_geometry_names"
        status: pass
      - kind: unit
        ref: "tests/core/test_comparator.py::test_one_beam_vs_two_beams"
        status: pass
      - kind: unit
        ref: "tests/core/test_comparator.py::test_two_beams_vs_one_beam"
        status: pass
      - kind: unit
        ref: "tests/core/test_comparator.py::test_zero_beams_vs_one_beam"
        status: pass
      - kind: unit
        ref: "tests/core/test_comparator.py::test_one_beam_vs_zero_beams"
        status: pass
      - kind: unit
        ref: "tests/core/test_comparator.py::test_positions_align_independently_per_comparison_file"
        status: pass
      - kind: unit
        ref: "tests/core/test_comparator.py::test_beam_position_follows_document_order_not_name"
        status: pass
      - kind: unit
        ref: "tests/core/test_comparator.py::test_duplicate_beam_names_still_get_separate_positions"
        status: pass
      - kind: integration
        ref: "tests/gui/test_cross_fixture_rows.py::test_differently_named_comparisons_show_real_beam_values"
        status: pass
      - kind: integration
        ref: "tests/gui/test_cross_fixture_rows.py::test_missing_beam_position_reads_na_only_for_that_file"
        status: pass
    human_judgment: false
  - id: G-03-3-dimension-rows-dropped
    description: "Per-model Width/Height/Length rows no longer appear in the cross-file comparison table or the Attributes picker (whether or not model names match across files), while every FixtureModel still extracts and stores those values unchanged"
    requirement: ATTR-03
    verification:
      - kind: unit
        ref: "tests/core/test_comparator.py::test_model_dimension_rows_are_not_compared"
        status: pass
      - kind: unit
        ref: "tests/core/test_comparator.py::test_model_dimension_rows_dropped_even_with_identical_model_names"
        status: pass
      - kind: unit
        ref: "tests/core/test_comparator.py::test_attribute_catalog_groups_distinct_attributes"
        status: pass
      - kind: integration
        ref: "tests/gui/test_namespaced_rows.py::test_table_shows_distinct_element_paths"
        status: pass
    human_judgment: false
  - id: G-03-3-match-dot-and-d06-still-correct
    description: "G-03-2's match dots become meaningful for differently-named fixtures (green when values genuinely match, red when they genuinely differ), and Phase 3 D-06's status message still reports a saved profile's dropped dimension items as not found rather than silently hiding them -- both as direct consequences of correct row alignment, with zero code changes to either feature"
    requirement: ATTR-03
    verification:
      - kind: integration
        ref: "tests/gui/test_cross_fixture_rows.py::test_match_dot_meaningful_for_differently_named_fixtures"
        status: pass
      - kind: integration
        ref: "tests/gui/test_cross_fixture_rows.py::test_profile_listing_a_dimension_item_reports_it_not_found"
        status: pass
    human_judgment: false
  - id: G-03-3-non-mutation-and-scope-boundary
    description: "compare() never mutates a FixtureModel's attributes or replaces the models carried on ComparisonResult while building cross-file views; extraction (core/extract.py), AttributeKey/models.py semantics, and every GUI module are unchanged -- the fix is scoped entirely to core/comparator.py"
    requirement: ATTR-03
    verification:
      - kind: unit
        ref: "tests/core/test_comparator.py::test_compare_leaves_models_untouched"
        status: pass
      - kind: other
        ref: "git diff --quiet HEAD -- src/gdtf_comparer/core/extract.py src/gdtf_comparer/core/models.py src/gdtf_comparer/core/repository.py src/gdtf_comparer/gui (exit 0, checked after Task 1 and again after Task 2)"
        status: pass
    human_judgment: false
  - id: G-03-3-real-files-human-verification
    description: "Re-running the exact comparison the user reported (Astera AF250 LeoFresnel target against Prolights EclPendantTU_60 and Robe OnePATT) in the live macOS app shows real beam values on 'Beam 1' rows for all three files, a genuine N/A-only 'Beam 2' row for the two single-beam comparison files, a single Weight row under Physical Properties with the old lens/housing/pigtail dimension rows gone, and both Compare-with dots red"
    requirement: ATTR-03
    verification: []
    human_judgment: true
    rationale: "Requires the user's own three real GDTF files from ~/Downloads (Astera AF250 LeoFresnel, Prolights EclPendantTU_60, Robe OnePATT), which are not part of the repository's test data and cannot be driven by an automated test in this plan. This is Task 2's <human-check> block, carried verbatim into 03-UAT.md as the re-test of UAT round-2 test 2 by /gsd-verify-work."

duration: 6m
completed: 2026-10-08
status: complete
---

# Phase 3 Plan 5: Cross-file beam rows now match by geometry position instead of exact element name, so differently-manufactured fixtures compare correctly; per-model dimension rows dropped from the comparison table Summary

**Closed gap G-03-3: comparing a target against fixtures from other manufacturers now shows each file's real BeamAngle/FieldAngle/PowerConsumption/LuminousFlux/ColorTemperature/BeamType values on the same "Beam 1"/"Beam 2" rows instead of N/A everywhere, and per-model Width/Height/Length rows are gone from the comparison table entirely while extraction keeps storing them.**

## Performance

- Duration: 6 minutes (2026-10-07T23:14:40Z start, metrics recorded same day)
- Started: 2026-10-07T23:14:40Z
- Completed: 2026-10-08T00:20:47Z
- Tasks: 2/2
- Files modified: 7 (1 created, 6 modified)

## Accomplishments

- Added `core.comparator._cross_file_attributes(model)`: a private per-file view that re-keys Beam rows by 1-based position (`beam_position_label`, "Beam 1", "Beam 2", ...) in geometry document order, and omits per-model Width/Height/Length rows entirely -- built fresh per `compare()` call, never mutating `FixtureModel.attributes` or replacing the models carried on `ComparisonResult`.
- `compare()` now builds the target's and every comparison's cross-file view once and runs its existing first-seen union/sort loop over those views instead of over each model's raw `attributes` -- `compare_files()` and `attribute_catalog()` needed zero changes, since both already operate on `result.rows`.
- 12 new core tests cover the user's exact symptom (differently-named geometry across all three real-file shapes), both count-boundary directions (1 vs 2, 2 vs 1, 0 vs 1, 1 vs 0 beams), independent per-comparison-file alignment, document-order (not name-order) position assignment, duplicate-name position distinctness, the dimension-row drop (including when model names DO match), pass-through of other categories, and a non-mutation guarantee.
- A new `tests/gui/test_cross_fixture_rows.py` module proves the fix at the app level: three differently-built fixtures (mirroring the user's Astera/Prolights/Robe files) show real values on "Beam 1", a genuinely-missing "Beam 2" position reads N/A only for the file that lacks it, the G-03-2 match dot is green for a same-values/different-names file and red for a genuinely different one, and a saved profile listing a now-dropped dimension item still gets the Phase 3 D-06 "weren't found" status message.
- Three existing core tests and five existing GUI tests across four files, which pinned the old exact-element-name assumption (the "why-not-caught" finding from the debug session), were rebaselined to the positional contract: lookups by `"Beam 1"`/`"Beam 2"` instead of geometry paths, and row counts reduced from 19/17 to 13/11 now that dimension rows are excluded.
- Full suite: 276 tests pass (`-W error::DeprecationWarning`), up from 258 before this plan (18 new: 14 core + 4 GUI).

## Task Commits

1. `56784e1` — test(03-05): add G-03-3 positional beam-matching regression tests (RED)
2. `b65ddc3` — feat(03-05): match beam rows across files by position, drop dimension rows (GREEN)
3. `cdda8c2` — test(03-05): rebaseline GUI tests to the positional cross-file contract

## Files Created/Modified

- `src/gdtf_comparer/core/comparator.py` (modified) — `BEAM_POSITION_LABEL_TEMPLATE`, `beam_position_label()`, `_cross_file_attributes()`, `compare()` updated to build rows from cross-file views.
- `tests/core/test_comparator.py` (modified) — 3 existing tests rebaselined, 14 new tests added.
- `tests/gui/test_cross_fixture_rows.py` (created) — 4 new app-level regression tests.
- `tests/gui/test_namespaced_rows.py` (modified) — positional lookups, dimension-row-absence assertion.
- `tests/gui/test_attribute_selection.py` (modified) — row counts 19→13, 17→11; positional lookup.
- `tests/gui/test_unspecified_values.py` (modified) — positional lookup.
- `tests/gui/test_differences_only_toggle.py` (modified) — positional lookup in expected triples.

## Decisions Made

- Beam rows match across files strictly by position (1st vs 1st, 2nd vs 2nd, ...), never by name, fuzzy matching, or beam type -- the user's 2026-10-07 decision, implemented with no deviation.
- Per-model dimension rows are dropped from cross-file comparison entirely (not shown under any naming scheme), while extraction and storage stay untouched -- the user's second 2026-10-07 decision.
- The fix is scoped entirely to `core/comparator.py`; `core/extract.py`, `core/models.py`, `core/repository.py`, and every GUI module are unchanged, verified by a `git diff --quiet` gate run after both tasks.

## Deviations from Plan

None - plan executed exactly as written. The RED run failed every new/rebaselined assertion for the documented value/row-count/KeyError/StopIteration/ImportError reasons (no collection errors), the GREEN implementation needed no REFACTOR step (no behavior or structure changes were needed after the initial implementation passed both verify commands), and every acceptance-criteria grep and `git diff --quiet` gate specified in the plan passed on the first attempt.

**Total deviations:** 0. **Impact:** None — the plan's design notes (measured at planning time) matched the actual implementation and blast radius exactly: 3 core tests and 5 GUI tests across 4 files needed rebaselining, and no other test in the 276-test suite was affected.

## Issues Encountered

None.

## User Setup Required

None — no USER-SETUP.md for this plan.

## Next Phase Readiness

This was the last incomplete plan in Phase 03 (Compare Profiles Export). Phase complete pending end-of-phase human verification: Task 2's `<human-check>` item (re-testing the exact Astera AF250 / Prolights EclPendantTU_60 / Robe OnePATT comparison in the live app, the user's own files from `~/Downloads`) is recorded verbatim in this SUMMARY's coverage block and must be carried into `03-UAT.md` as the re-test of UAT round 2 test 2. Ready for `/gsd-verify-work`.

*Phase: 03-compare-profiles-export*
*Completed: 2026-10-08*
