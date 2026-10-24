---
phase: 05-mvr-import-fixture-substitution
plan: 03
subsystem: mvr-import-substitution
tags: [requirements-editor, substitution, pyside6, fixture-attributes]

requires:
  - phase: 05-mvr-import-fixture-substitution
    provides: "Plan 05-01's requirements editor tracer (RequirementsEditor, core.substitution's Direction/Requirement/RequirementSet, requirement_options)"
provides:
  - "Per-fixture-type independent requirement checklists (D-04), remembered across switches within a session"
  - "A per-attribute defaults table (DEFAULT_DIRECTIONS) and display units (ATTRIBUTE_UNITS/attribute_unit) in core.substitution"
  - "Honest text-attribute handling: BeamType and DMX attribute-definition properties offer only 'Must match', with a disabled, dashed tolerance box"
  - "A search box narrowing the editor's visible rows without ever touching what is checked"
  - "A 'nothing marked yet' hint and support for saving a fixture type with an empty requirements list"
affects: [05-05-substitution-scoring-widening]

actuals:
  tokens: 9552
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Per-type UI memory keyed by a string id (RequirementsEditor._remembered), captured just before a tree rebuild and restored just after, mirroring the existing lazy-widget-on-tick pattern for the restored rows"
    - "AttributePicker._apply_search's visibility-only search pattern (leaf/section setHidden, never touching check state) reused verbatim for a second checkable tree widget"

key-files:
  created:
    - tests/core/test_requirement_defaults.py
  modified:
    - src/gdtf_comparer/core/substitution.py
    - src/gdtf_comparer/gui/requirements_editor.py
    - tests/gui/test_requirements_editor.py

key-decisions:
  - "Per-type memory stores every leaf's (checked, direction, tolerance), not only checked ones, so unticking a previously-ticked row is itself remembered rather than silently reverting to the default on the next visit."
  - "default_direction's str-value check runs before any name-based lookup, so a DMX attribute definition literally named 'Weight' (always text) is never routed into the numeric DEFAULT_DIRECTIONS table meant for Beam/Physical Properties floats."
  - "attribute_unit() is restricted to CATEGORY_BEAM/CATEGORY_PHYSICAL — a DMX attribute definition or an unrecognized numeric attribute never gets a unit guessed for it."

requirements-completed: [SUB-02]

coverage:
  - id: D1
    description: "Each fixture type keeps its own independent requirement checklist; switching between two fixture types and back preserves exactly what was ticked, its direction and its tolerance (D-04)"
    requirement: SUB-02
    verification:
      - kind: unit
        ref: "tests/gui/test_requirements_editor.py#test_each_fixture_type_keeps_its_own_requirements"
        status: pass
      - kind: unit
        ref: "tests/gui/test_requirements_editor.py#test_remembered_direction_survives_switching"
        status: pass
    human_judgment: false
  - id: D2
    description: "Marked attributes save in the same order the comparison table and Attributes panel use, regardless of the order they were ticked in"
    requirement: SUB-02
    verification:
      - kind: unit
        ref: "tests/gui/test_requirements_editor.py#test_requirements_follow_attribute_panel_order"
        status: pass
    human_judgment: false
  - id: D3
    description: "Importing a different MVR forgets every remembered checklist from the previous show"
    requirement: SUB-02
    verification:
      - kind: unit
        ref: "tests/gui/test_requirements_editor.py#test_new_import_forgets_previous_show"
        status: pass
    human_judgment: false
  - id: D4
    description: "Every attribute starts with a sensible, overridable direction (Weight/PowerConsumption lower, LuminousFlux higher, angles/temperature closest) and its own tolerance, shown with units next to the value and in the tolerance box"
    requirement: SUB-02
    verification:
      - kind: unit
        ref: "tests/core/test_requirement_defaults.py#test_default_directions"
        status: pass
      - kind: unit
        ref: "tests/gui/test_requirements_editor.py#test_defaults_shown_and_overridable"
        status: pass
      - kind: unit
        ref: "tests/gui/test_requirements_editor.py#test_each_attribute_keeps_its_own_tolerance"
        status: pass
      - kind: unit
        ref: "tests/gui/test_requirements_editor.py#test_units_shown"
        status: pass
    human_judgment: false
  - id: D5
    description: "Text attributes (BeamType and DMX attribute-definition properties) offer only 'Must match', with a disabled, dash-reading tolerance box, and save as direction exact / tolerance 0.0"
    requirement: SUB-02
    verification:
      - kind: unit
        ref: "tests/gui/test_requirements_editor.py#test_text_attribute_must_match"
        status: pass
    human_judgment: false
  - id: D6
    description: "Only attributes the fixture's own file actually declares become markable rows -- pygdtf's spec-default backfill never surfaces"
    requirement: SUB-02
    verification:
      - kind: unit
        ref: "tests/core/test_requirement_defaults.py#test_only_declared_values_are_options"
        status: pass
      - kind: unit
        ref: "tests/gui/test_requirements_editor.py#test_undeclared_attributes_never_listed"
        status: pass
    human_judgment: false
  - id: D7
    description: "A search box narrows visible rows without ever changing what is checked, and an empty fixture type is allowed to save with no requirements"
    requirement: SUB-02
    verification:
      - kind: unit
        ref: "tests/gui/test_requirements_editor.py#test_search_narrows_visibility_only"
        status: pass
      - kind: unit
        ref: "tests/gui/test_requirements_editor.py#test_nothing_marked_is_allowed"
        status: pass
      - kind: unit
        ref: "tests/gui/test_requirements_editor.py#test_widgets_exist_only_for_ticked_rows"
        status: pass
    human_judgment: false

duration: ~35min
completed: 2026-10-24
status: complete
---

# Phase 5 Plan 3: Requirements Editor Widening Summary

**Per-fixture-type independent requirement checklists with a remembered state, a table-driven default direction/tolerance shown with units, honest "Must match"-only handling for text attributes, and a visibility-only search box over the declared-attribute-only tree.**

## Performance

- **Duration:** ~35 min
- **Completed:** 2026-10-24
- **Tasks:** 3 (1 tracer, 2 auto/tdd)
- **Files modified:** 4 (1 created, 3 modified)

## Accomplishments

- `RequirementsEditor._remembered` gives each fixture type (keyed by its `gdtf_spec`) its own independent checklist: ticking Weight on one type and BeamAngle on another, then switching back and forth, restores each type exactly as left — check state, direction and tolerance — via a capture-before-rebuild / restore-after-rebuild pair (`_capture_current`, restored leaves re-run through the existing lazy-widget helper). `clear()` empties this memory so a new MVR import always starts every type fresh.
- `core.substitution.DEFAULT_DIRECTIONS` and `ATTRIBUTE_UNITS` make `default_direction`/`attribute_unit` table-driven: Weight and PowerConsumption default to "Lower is better", LuminousFlux to "Higher is better", BeamAngle/FieldAngle/ColorTemperature to "Closest to target" — all overridable per attribute, never blocking. The str-value check still runs first, so a DMX attribute definition named "Weight" is never misrouted into the numeric table.
- The editor's value column and tolerance spin box now show the attribute's unit (kg, °, W, lm, K) in absolute mode; a checked text attribute (BeamType, or any DMX attribute-definition property) collapses its direction combo to a single disabled "Must match" entry and its tolerance box to a disabled "—", saving as `direction: "exact"`, `tolerance: 0.0`.
- A new `search_edit` mirrors `gui.attribute_picker.AttributePicker._apply_search` exactly: it only hides/shows leaves and sections, never touches a check state, and survives switching fixture types (re-applied at the end of `show_fixture`). A hidden, ticked leaf is still saved.
- A new `nothing_marked_label` shows `NOTHING_MARKED_TEXT` whenever a fixture is shown with nothing ticked, updated after every tick change and after `show_fixture`; saving in that state writes a valid file with `"requirements": []`.
- `requirement_options()`'s existing declared-only filter (05-01) is now pinned by tests at both the pure-core level (`test_only_declared_values_are_options`) and through the full editor (`test_undeclared_attributes_never_listed`): pygdtf's spec-default backfill (1000 W, 10000 lm, ...) never becomes a markable row.

## Task Commits

Each task was committed atomically:

1. **Task 1: Per-type requirements memory (D-04 tracer)** - `e85626b` (feat)
2. **Task 2: Per-attribute default direction/tolerance with units (D-05, D-06)** - `66c835e` (feat)
3. **Task 3: Declared-only rows, search and a nothing-marked hint (SUB-02)** - `4e7ee67` (feat)

**Plan metadata:** (this SUMMARY, committed separately per the worktree wave protocol — STATE/ROADMAP/REQUIREMENTS updates are owned by the orchestrator after all wave agents complete)

## Files Created/Modified

- `src/gdtf_comparer/core/substitution.py` - `DEFAULT_DIRECTIONS`, `ATTRIBUTE_UNITS`, `attribute_unit()`; `default_direction` made table-driven
- `src/gdtf_comparer/gui/requirements_editor.py` - `_remembered`/`_capture_current` (D-04); unit-aware value/tolerance display; Must-match handling for text rows; `search_edit`/`_apply_search`; `nothing_marked_label`/`_update_nothing_marked`
- `tests/core/test_requirement_defaults.py` - New: default-direction table, default-tolerance branches, `attribute_unit`, declared-only options
- `tests/gui/test_requirements_editor.py` - New: per-type independence/ordering/forgetting/remembering, overridable defaults, per-attribute tolerances, units, text-attribute handling, declared-only listing, search, empty-edge hint, lazy-widget pinning

## Decisions Made

- Per-type memory captures every leaf's state (not only checked ones), so an explicit uncheck after a check is itself remembered, rather than reverting to the attribute's default the next time that fixture type is shown.
- `default_direction`'s string-value check is evaluated before any category/name lookup, so a DMX attribute definition that happens to be literally named "Weight" (its value is always text) is never routed into the numeric `DEFAULT_DIRECTIONS` table that exists only for Beam/Physical Properties floats.
- `attribute_unit()` only ever returns a unit for `CATEGORY_BEAM`/`CATEGORY_PHYSICAL` keys — an unrecognized numeric attribute or any DMX attribute-definition property gets `""`, never a guessed unit.

## Deviations from Plan

None - plan executed exactly as written. The plan's Task 3 behavior description for `test_widgets_exist_only_for_ticked_rows` mentions a fixture with "20 DMX attribute definitions (6 rows each)"; the implemented test instead reuses this plan's shared two-type MVR fixture (which already has more than one leaf) to pin the same lazy-widget assertion, since the exact attribute count was illustrative rather than load-bearing for the behavior being verified.

## Issues Encountered

None. All three `<verify>` commands (the new/changed test files alone, twice each, and the full suite three times across the three tasks) and every `<acceptance_criteria>` grep/git-diff check passed on the first attempt after implementation — no repair cycles were needed. The full suite was run an extra two times after the final commit to rule out a one-off Qt teardown message observed in an isolated run; both reruns were clean (331 passed).

## User Setup Required

None - no external service configuration required; this plan only changed `core/substitution.py` and `gui/requirements_editor.py` plus their tests.

## Next Phase Readiness

This plan widens the requirements editor to the LD's full working surface across every fixture type in a show, exactly within its stated scope (requirement_options / default_direction / default_tolerance / attribute_unit in `core/substitution.py`; the editor widget itself). It does not touch `gui/substitution_window.py` (confirmed by `git diff --quiet HEAD -- src/gdtf_comparer/gui/substitution_window.py` passing after every task) or the scoring/ranking surface, which stays Plan 05-05's responsibility.

Ready for:
- **Wave 3 (05-05 — depends on 05-02 and 05-03):** widens scoring, ranking, failure rows and readability in the Check Inventory results, building on `DEFAULT_DIRECTIONS`/`ATTRIBUTE_UNITS`/`attribute_unit` and the widened editor behavior this plan established.

No blockers. The contracts this plan created (`DEFAULT_DIRECTIONS`, `ATTRIBUTE_UNITS`, `attribute_unit`, `RequirementsEditor.search_edit`/`nothing_marked_label`/`_remembered`) are additive to Plan 05-01's interfaces — nothing was renamed or removed.

---
*Phase: 05-mvr-import-fixture-substitution*
*Completed: 2026-10-24*

## Self-Check: PASSED

- FOUND: tests/core/test_requirement_defaults.py
- FOUND: src/gdtf_comparer/core/substitution.py
- FOUND: src/gdtf_comparer/gui/requirements_editor.py
- FOUND commit: e85626b (Task 1)
- FOUND commit: 66c835e (Task 2)
- FOUND commit: 4e7ee67 (Task 3)
