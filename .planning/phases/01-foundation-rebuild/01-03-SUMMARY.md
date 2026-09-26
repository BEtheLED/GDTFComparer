---
phase: 01-foundation-rebuild
plan: 03
subsystem: parsing
tags: [pygdtf, namespaced-keys, tdd, comparator]

requires:
  - phase: 01-02
    provides: "core.extract.extract_attributes(fixture_type) stub (Weight-only), core.models.AttributeKey scheme, core.comparator.compare/compare_files, gui.table_model.ComparisonTableModel.find_row, gui.main_window.MainWindow"
provides:
  - "core.extract.iter_geometry_paths(fixture_type) -> Iterator[tuple[str, Any]]: iterative explicit-stack walk of the geometry tree in document order, never following GeometryReference targets"
  - "core.extract._unique_path(path, used) -> str: #N suffixing for duplicate element paths"
  - "core.extract.BEAM_ATTRIBUTES / MODEL_ATTRIBUTES constants"
  - "extract_attributes now emits per-GeometryBeam Beam keys and per-Model Physical Properties keys, alongside the existing fixture-level Weight key"
affects: ["01-04 (typed-error wrapping around the same extract_attributes call site)", "01-05 (end-of-phase human-check runs the app against real multi-model/multi-beam GDTF files)"]

actuals:
  tokens: 5086
  tasks: 2
  commits: 2
  plan_head_before: d82c0d5304f7434629b1e418a42c81205b265e72

tech-stack:
  added: []
  patterns:
    - "Iterative (explicit-stack) tree walk instead of recursion for geometry traversal (T-01-07 DoS mitigation)"
    - "GeometryReference targets are never expanded when walking fixture_type.geometries -- each defined beam appears exactly once regardless of DMX mode, unlike pygdtf's own get_geometry_tree()/iter_tree() helpers"
    - "_unique_path #N suffixing for any namespaced element path (beams and models share the pattern but use independent used-sets)"

key-files:
  created:
    - tests/core/test_extract.py
    - tests/core/test_comparator.py
    - tests/gui/test_namespaced_rows.py
  modified:
    - src/gdtf_comparer/core/extract.py
  deleted: []

key-decisions:
  - "Confirmed against the installed pygdtf 1.4.5 source (geometries.py:516-590) that GeometryBeam is a direct Geometry subclass (not GeometryReference), so `isinstance(node, GeometryBeam)` naturally excludes references without extra filtering"
  - "BeamType's underlying pygdtf Enum defaults to 'Wash' when the XML attribute is omitted (never None in practice for XML-parsed fixtures) -- the None-guard in extract.py is defensive for directly-constructed nodes, not exercised by real-world files"
  - "Split the originally-drafted single test_extract.py (all 10 tests written up front) into a Task 1 RED/GREEN pass (6 beam tests) and a Task 2 RED/GREEN pass (4 model tests) to keep each task's TDD commit atomic and its own tests failing-then-passing, per the plan's tdd=\"true\" execution contract"

requirements-completed: [PARSE-01]

coverage:
  - id: D1
    description: "Every GeometryBeam node contributes its own BeamAngle/FieldAngle/PowerConsumption/LuminousFlux/ColorTemperature/BeamType row, namespaced by its full geometry path, so same-named beam attributes on different geometries never collide"
    requirement: "PARSE-01"
    verification:
      - kind: unit
        ref: "tests/core/test_extract.py::test_two_beams_same_names_do_not_collide"
        status: pass
      - kind: unit
        ref: "tests/core/test_extract.py::test_beam_attribute_set_and_order"
        status: pass
      - kind: unit
        ref: "tests/core/test_extract.py::test_duplicate_geometry_paths_get_suffix"
        status: pass
      - kind: unit
        ref: "tests/core/test_extract.py::test_nested_beam_path_includes_every_ancestor"
        status: pass
      - kind: unit
        ref: "tests/core/test_comparator.py::test_no_attribute_collision"
        status: pass
    human_judgment: false
  - id: D2
    description: "Every Model entry contributes its own Width/Height/Length row keyed by model name, Weight stays the single fixture-level row, and the running app renders both per-beam and per-model rows with distinct Element-column labels"
    requirement: "PARSE-01"
    verification:
      - kind: unit
        ref: "tests/core/test_extract.py::test_models_dimensions_namespaced_per_model"
        status: pass
      - kind: unit
        ref: "tests/core/test_extract.py::test_duplicate_model_names_get_suffix"
        status: pass
      - kind: unit
        ref: "tests/core/test_extract.py::test_unnamed_model_label"
        status: pass
      - kind: automated_ui
        ref: "tests/gui/test_namespaced_rows.py::test_table_shows_distinct_element_paths"
        status: pass
    human_judgment: false

duration: ~25min
completed: 2026-09-26
status: complete
---

# Phase 01 Plan 03: Namespaced Beam & Model Attribute Extraction Summary

**`extract_attributes` now walks the real pygdtf geometry tree iteratively to emit one row per GeometryBeam and one row per Model, replacing the Weight-only tracer with the full Phase-1 display scope (Beam + Physical Properties) while guaranteeing same-named attributes on different elements never overwrite each other.**

## Performance

- **Duration:** ~25 min
- **Tasks:** 2 completed
- **Files modified:** 4 (1 production, 3 test)

## Accomplishments

- `iter_geometry_paths(fixture_type)` walks `fixture_type.geometries` with an explicit stack (no recursion), yielding every geometry node in document order with its full ancestor-joined path; `GeometryReference` targets are never followed, so each defined beam appears exactly once regardless of DMX mode
- `_unique_path(path, used)` suffixes any repeated element path with `#2`, `#3`, ... so duplicate geometry or model names never collide
- `extract_attributes` now emits, per `GeometryBeam` node found in the walk, six namespaced keys (`BeamAngle`, `FieldAngle`, `PowerConsumption`, `LuminousFlux`, `ColorTemperature`, `BeamType`) under `CATEGORY_BEAM`, keyed by that beam's unique geometry path (e.g. `Body/Head1/Beam`); `BeamType`'s pygdtf enum value is unwrapped to a plain string
- `extract_attributes` also emits, per `fixture_type.models` entry, three namespaced keys (`Width`, `Height`, `Length`) under `CATEGORY_PHYSICAL`, keyed by model name (or `(unnamed model N)` when the model has no name) — every model gets its own three rows, none dropped or merged; the fixture-level `Weight` key from Plan 01-02 remains the only single-scalar Physical Properties row
- Verified in the running app (`tests/gui/test_namespaced_rows.py`): two beams sharing the name "Beam" under different parent geometries render as two distinct rows with different `BeamAngle` values and correct `Body/Head1/Beam` / `Body/Head2/Beam` Element labels; a `Head` model's `Width` row and the fixture's `Weight` row (labeled "Fixture") both appear correctly

## Task Commits

Each task was committed atomically (TDD RED confirmed before each GREEN):

1. **Task 1: Every beam's Beam attributes appear as separate, path-namespaced rows** - `3d4d9f5` (feat)
2. **Task 2: Every model's Width/Height/Length and the single fixture Weight appear under Physical Properties in the app** - `74aa0f1` (feat)

_Note: both tasks carried `tdd="true"`; RED was confirmed (11 failing beam/model tests against the Weight-only tracer for Task 1, then 4 failing model/GUI tests against the beam-only extract.py for Task 2) before each GREEN implementation, all within the single commit per task as scoped by the plan's `files` list._

## Files Created/Modified

- `src/gdtf_comparer/core/extract.py` - Extended with `BEAM_ATTRIBUTES`, `MODEL_ATTRIBUTES`, `PATH_SEPARATOR`, `UNNAMED_GEOMETRY` constants; `iter_geometry_paths` and `_unique_path` functions; `extract_attributes` now emits per-beam and per-model keys alongside the existing fixture-level Weight key
- `tests/core/test_extract.py` - 10 tests: 6 beam-namespacing tests (collision-free keys, attribute order, BeamType string coercion, duplicate-path suffixing, 100-deep nesting, no-beams-present) + 4 model-namespacing tests (per-model dimensions, single fixture-level Weight, duplicate-name suffixing, unnamed-model labeling)
- `tests/core/test_comparator.py` - 4 tests: no-collision beam-attribute comparison, missing-key N/A + differs, Beam-before-Physical-Properties row ordering, all rows restricted to `DISPLAY_CATEGORIES`
- `tests/gui/test_namespaced_rows.py` - 1 end-to-end test proving the running `MainWindow` renders distinct per-beam and per-model rows with correct Element-column labels, including the Weight row's "Fixture" label

## Decisions Made

- Confirmed `GeometryBeam` is a direct `Geometry` subclass (not `GeometryReference`) in the installed pygdtf 1.4.5 source before writing the `isinstance` check, per the plan's `read_first` instruction
- Kept the path-builder (`iter_geometry_paths`, `_unique_path`) inside `core/extract.py` rather than `core/models.py`, matching the RESEARCH.md Open Question 1 resolution recorded in the plan
- Split the test-writing work into two RED/GREEN passes (beam tests for Task 1, model tests for Task 2) rather than writing all 10 `test_extract.py` tests up front, so each task's commit reflects its own atomic TDD cycle as the plan's `tdd="true"` tasks require

## Deviations from Plan

None — plan executed exactly as written. Both pygdtf facts flagged "confirm against the installed pygdtf" in the plan's `read_first`/interfaces (GeometryBeam class location, Model field names) were verified directly against `/Users/brandon/GDTFComparer/.venv/lib/python3.12/site-packages/pygdtf/geometries.py` and `pygdtf/__init__.py` before implementation; both matched the plan's assumptions.

## Known Stubs

None. Every namespaced key produced by `extract_attributes` flows from a real pygdtf-parsed value (or `None` when the source field is genuinely absent, rendered as "N/A" by the existing `format_value`); no hardcoded placeholder values were introduced.

## Threat Flags

None beyond what the plan's own threat model already tracks and mitigates in this plan's own code: T-01-07 (DoS via pathologically deep trees) is mitigated by the iterative explicit-stack walk with zero recursion in `iter_geometry_paths`; T-01-08 (duplicate names hiding/overwriting values) is mitigated by `_unique_path` suffixing; T-01-09 (markup in element names) is accepted per the plan (QTableView renders plain text). No new trust-boundary surface introduced.

## Issues Encountered

None.

## Next Phase Readiness

- `core/extract.py` now covers the full Phase-1 display scope (Beam + Physical Properties); Plan 01-04 can add pre-validation/typed-error wrapping around the same `extract_attributes` call site without touching this plan's logic
- The unresolved prohibition (pygdtf silently substitutes GDTF-spec defaults for omitted beam attributes, e.g. `PowerConsumption` 1000) remains flagged for a future user decision — not implemented here because pygdtf exposes no explicit/defaulted provenance distinction
- Plan 01-05's end-of-phase human-check should validate multi-model/multi-beam rendering against real GDTF-Share/manufacturer files, as originally planned

## Self-Check: PASSED

- FOUND: src/gdtf_comparer/core/extract.py
- FOUND: tests/core/test_extract.py
- FOUND: tests/core/test_comparator.py
- FOUND: tests/gui/test_namespaced_rows.py
- FOUND: .planning/phases/01-foundation-rebuild/01-03-SUMMARY.md
- FOUND commit: 3d4d9f5 (feat(01-03): namespaced per-beam attribute extraction)
- FOUND commit: 74aa0f1 (feat(01-03): namespaced per-model dimension extraction)
- FOUND commit: 3a0b17b (docs(01-03): complete namespaced beam & model extraction plan)

---
*Phase: 01-foundation-rebuild*
*Completed: 2026-09-26*
