---
phase: 01-foundation-rebuild
plan: 09
subsystem: ui
tags: [pyside6, qt-material, qheaderview, qidentityproxymodel, gap-closure]

# Dependency graph
requires:
  - phase: 01-foundation-rebuild
    provides: ComparisonTableModel, MainWindow, qt-material theming (Plans 01-01..01-08)
provides:
  - "UppercaseHeaderProxyModel: a QIdentityProxyModel that uppercases horizontal DisplayRole header text, so Qt measures/elides exactly what qt-material paints"
  - "Per-file header labels derived from FixtureModel.name with a file_name fallback on blank/colliding names"
  - "MAX_COLUMN_WIDTH_PX (280) column-width cap with middle elision after resizeColumnsToContents()"
affects: [any future phase touching gui/table_model.py or gui/main_window.py's table setup]

# Actuals (#2632)
actuals:
  tokens: 5152
  tasks: 2
  commits: 3

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "View-only QIdentityProxyModel to make Qt's own size-hint/elision logic agree with CSS text-transform, instead of a stylesheet override or duplicated padding math"
    - "Per-section resizeSection() clamp after resizeColumnsToContents(), instead of a header-wide maximum section size, to preserve manual column drag and stretch-last-section behavior"

key-files:
  created:
    - tests/gui/test_table_headers.py
  modified:
    - src/gdtf_comparer/gui/table_model.py
    - src/gdtf_comparer/gui/main_window.py
    - tests/test_walking_skeleton.py

key-decisions:
  - "Fixed the G-01-1 header clipping with a QIdentityProxyModel between the table model and the view (uppercases DisplayRole header text) rather than widening columns by a hardcoded 24px padding constant or setting an uppercase font -- the proxy approach also correctly handles G-01-2's elided long labels and survives a live light/dark re-theme, per the plan's Design notes"
  - "Per-file header labels use the fixture's Name, falling back to file_name when the name is blank or collides (case/whitespace-insensitive) with another compared fixture's name -- keeps two revisions of one fixture distinguishable by their file name's revision suffix"
  - "Column width capped at 280px via a per-section resizeSection() clamp (not QHeaderView.setMaximumSectionSize), so the user can still manually drag a column wider to read a full elided name"
  - "Manufacturer moved into the header tooltip (next to the existing full path) rather than into the label itself, to keep most fixture names inside the 280px cap without eliding"

requirements-completed: [UI-01]

coverage:
  - id: D1
    description: "CATEGORY, ELEMENT and ATTRIBUTE fixed headers are never clipped in either qt-material theme (G-01-1)"
    requirement: "UI-01"
    verification:
      - kind: automated_ui
        ref: "tests/gui/test_table_headers.py#test_fixed_headers_fit_uppercased_labels"
        status: pass
      - kind: automated_ui
        ref: "tests/gui/test_table_headers.py#test_view_uppercases_header_text_only"
        status: pass
    human_judgment: true
    rationale: "Offscreen tests reproduce the clipping numerically and in rendered grabs, but real macOS font rendering and live OS light/dark appearance switching cannot be observed on the offscreen test platform (flagged as this plan's end-of-phase human-check, re-running UAT tests 1 and 2)"
  - id: D2
    description: "Per-file column headers show the fixture's name instead of the raw Manufacturer@Model@Revision.gdtf file name, with a file-name fallback when names collide or are blank (G-01-2)"
    requirement: "UI-01"
    verification:
      - kind: automated_ui
        ref: "tests/gui/test_table_headers.py#test_value_headers_use_fixture_names"
        status: pass
      - kind: unit
        ref: "tests/gui/test_table_headers.py#test_colliding_or_blank_names_fall_back_to_file_names"
        status: pass
      - kind: e2e
        ref: "tests/test_walking_skeleton.py#test_gui_run_comparison_populates_table"
        status: pass
    human_judgment: false
  - id: D3
    description: "No column exceeds 280px after a comparison; long labels elide in the middle so a revision suffix stays visible; a target plus one comparison fit the default 1000px window with no horizontal scrollbar; a column can still be dragged wider"
    requirement: "UI-01"
    verification:
      - kind: automated_ui
        ref: "tests/gui/test_table_headers.py#test_long_headers_are_capped_and_elided"
        status: pass
    human_judgment: true
    rationale: "Real macOS font rendering of the elided/capped headers is part of this plan's end-of-phase human-check re-running UAT tests 1 and 2"

# Metrics
duration: 25min
completed: 2026-09-27
status: complete
---

# Phase 01 Plan 09: Gap Closure -- Table Header Readability Summary

**Uppercase-aware header sizing via a QIdentityProxyModel plus fixture-name column headers with a 280px width cap and middle elision, closing UAT gaps G-01-1 and G-01-2.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-09-27
- **Completed:** 2026-09-27
- **Tasks:** 2
- **Files modified:** 4 (2 source, 1 new test file, 1 existing test edited)

## Accomplishments

- Fixed CATEGORY/ELEMENT/ATTRIBUTE header clipping (G-01-1) with `UppercaseHeaderProxyModel`, a `QIdentityProxyModel` sitting between `ComparisonTableModel` and the `QTableView`: it returns horizontal `DisplayRole` header text already uppercased, so Qt's own size-hint and elision logic measures exactly the text qt-material paints, in both themes and across a live light/dark switch. No custom stylesheet, no edits to the vendored qt-material template.
- Per-file column headers now show the fixture's `name` ("Target: {name}" / "{name}") instead of the raw `Manufacturer@Model@Revision.gdtf` file name (G-01-2). When two or more compared fixtures share a name (ignoring case and surrounding whitespace) or a name is blank, those columns fall back to their file name so revisions stay distinguishable.
- Column width is capped at 280px (`MAX_COLUMN_WIDTH_PX`) via a per-section clamp applied after `resizeColumnsToContents()`, and the header now elides long labels in the middle -- keeping a GDTF revision suffix (`...@V3.gdtf`) visible instead of forcing a horizontal scrollbar. The stretched last section still fills the window, and the user can still manually drag a column wider than the cap.
- The header tooltip now includes the manufacturer alongside the fixture name and full source path.

## Task Commits

Each task was committed atomically (Task 2 followed the RED/GREEN cycle since it carries `tdd="true"`; no REFACTOR commit was needed -- the GREEN implementation was already clean):

1. **Task 1: Uppercase header proxy (tracer)** - `4333110` (feat)
2. **Task 2 RED: failing tests for fixture-name headers and width cap** - `fc0e90a` (test)
2. **Task 2 GREEN: fixture-name headers with width cap and middle elision** - `1ede3d5` (feat)

**Plan metadata:** committed alongside this SUMMARY.

## Files Created/Modified

- `src/gdtf_comparer/gui/table_model.py` - `UppercaseHeaderProxyModel`; `_value_column_labels()` (fixture-name labels with collision/blank fallback); `_header_tooltip()` now includes manufacturer
- `src/gdtf_comparer/gui/main_window.py` - wires `header_proxy` as the view's model; `MAX_COLUMN_WIDTH_PX = 280`; `ElideMiddle` on the horizontal header; `_fit_columns_to_contents()` replacing the bare `resizeColumnsToContents()` call
- `tests/gui/test_table_headers.py` - new: 5 tests covering both header-sizing gaps in both qt-material themes
- `tests/test_walking_skeleton.py` - target-header tracer assertion updated to expect the target's fixture name (`"Target: Target Fixture"`) instead of its file name

## Decisions Made

See `key-decisions` in frontmatter. In short: a view-only `QIdentityProxyModel` fixes G-01-1 at the measurement layer (rather than a hardcoded padding constant or an uppercase font, both of which the plan's Design notes show fail to fully close the gap or survive a live theme switch); G-01-2 uses the existing `FixtureModel.name`/`manufacturer` fields with a collision-safe fallback to `file_name`, and a per-section width clamp that preserves manual column dragging.

## Deviations from Plan

None - plan executed exactly as written. One test authoring adjustment within the plan's own spec: `test_fixed_headers_fit_uppercased_labels` is implemented as a `pytest.mark.parametrize` over `(LIGHT_THEME, DARK_THEME)` (as the plan's task 1 `<behavior>` names it: "parametrized over LIGHT_THEME and DARK_THEME") rather than an inline `for theme in (...)` loop, so the two themes surface as two distinct test IDs -- this is what makes the Task 1 verify command's "3 passed" summary line match exactly.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Both G-01-1 and G-01-2 are closed at the automated-test level; the full suite (95 tests, up from the 89-test baseline) passes.
- This plan's end-of-phase human-check re-runs UAT tests 1 and 2 on a real macOS display with real fixture files (two revisions of the same fixture plus one different fixture), verifying font rendering and live OS light/dark appearance switching that the offscreen test platform cannot observe.
- `requirements-completed: [UI-01]` is recorded in this SUMMARY's frontmatter per the plan's `requirements` field. This executor ran in an isolated worktree without `gsd-core` tooling available, so it did not run the shared-ID readiness check (`requirements.ready-ids`) against sibling Phase 1 plans before touching `.planning/REQUIREMENTS.md` -- left to the orchestrator to reconcile, consistent with STATE.md/ROADMAP.md being orchestrator-owned in this dispatch.

## Self-Check: PASSED

- `tests/gui/test_table_headers.py` exists: FOUND
- `src/gdtf_comparer/gui/table_model.py` contains `UppercaseHeaderProxyModel` and `_value_column_labels`: FOUND
- `src/gdtf_comparer/gui/main_window.py` contains `MAX_COLUMN_WIDTH_PX = 280`, `ElideMiddle`, `_fit_columns_to_contents`: FOUND
- Commits `4333110`, `fc0e90a`, `1ede3d5` present in `git log --oneline --all`: FOUND
- All task `<acceptance_criteria>` re-verified: PASS (see task execution log)
- Plan-level `<verification>` (`pytest -q`, full suite): 95 passed
- `plan_head_before: 35846bbe96c6ef929563ee74a6d9b8c6d4e2c7df`, measured `commits: 3` via `git rev-list --count`

---
*Phase: 01-foundation-rebuild*
*Completed: 2026-09-27*
