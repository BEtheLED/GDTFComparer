---
phase: 02-attribute-browsing-diff-highlighting
plan: 01
subsystem: ui
tags: [pyside6, qt, gdtf, attribute-picker, proxy-model, qsortfilterproxymodel]

# Dependency graph
requires:
  - phase: 01-foundation-rebuild
    provides: "ComparisonResult/ComparisonRow contract (D-13), core/GUI import boundary (D-16), the UppercaseHeaderProxyModel single-purpose-proxy convention this plan's new proxy follows"
provides:
  - "core.comparator.compare() returns rows for every category (no DISPLAY_CATEGORIES filter); GUI decides what is shown"
  - "core.comparator.attribute_catalog(result) -- the (category, attribute-names) catalog the picker builds sections from"
  - "core.models.LEADING_CATEGORIES (row-order anchor) and DEFAULT_SELECTED_CATEGORIES (D-04 first-use seed)"
  - "gui.attribute_picker.AttributePicker: collapsible, checkable, searchable attribute picker widget"
  - "gui.table_model.AttributeSelectionProxyModel + SELECTION_KEY_ROLE: view-only row filter by checked (category, attribute)"
  - "gui.main_window: always-visible, non-collapsible Attributes side panel wired into the table's proxy chain"
affects: ["02-02 (full attribute set will flow through attribute_catalog/AttributePicker unchanged)", "02-03 (differences-only proxy chains after AttributeSelectionProxyModel, same pattern)"]

# Actuals (#2632) — pairs with the plan's estimate to calibrate future estimates.
actuals:
  tokens: 10855
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "AttributeSelectionProxyModel: a QSortFilterProxyModel that reads row identity through a custom data role (SELECTION_KEY_ROLE) instead of calling sourceModel().result(), so it works at any position in a proxy chain"
    - "Selection unit is (category, attribute), never a full AttributeKey -- one checkbox covers every element path sharing that attribute name"
    - "Picker keeps _known/_checked sets; set_catalog() seeds new pairs by category membership (D-04) and always preserves the user's prior choice, including for pairs temporarily missing from the current result"

key-files:
  created:
    - src/gdtf_comparer/gui/attribute_picker.py
    - tests/gui/test_attribute_selection.py
    - tests/gui/test_attribute_picker.py
  modified:
    - src/gdtf_comparer/core/models.py
    - src/gdtf_comparer/core/comparator.py
    - src/gdtf_comparer/gui/table_model.py
    - src/gdtf_comparer/gui/main_window.py
    - tests/core/test_comparator.py

key-decisions:
  - "Split the old dual-purpose DISPLAY_CATEGORIES into LEADING_CATEGORIES (compare()'s row-order anchor) and DEFAULT_SELECTED_CATEGORIES (the picker's D-04 first-use seed) so a future change to one can never silently affect the other"
  - "Selection state lives entirely in the GUI layer (AttributePicker); core.comparator.compare() stays a pure, selection-unaware function per 02-CONTEXT.md's Integration Points"

patterns-established:
  - "View-only proxy reads a custom Qt data role rather than the source model's typed accessor, so later proxies (Plan 02-03's differences-only filter) can chain after this one without knowing about ComparisonResult"
  - "Google-style docstrings on every new class/function cross-reference the decision IDs they satisfy (D-01..D-04)"

requirements-completed: [ATTR-01, ATTR-02]

coverage:
  - id: D1
    description: "core.comparator.compare() returns rows for every category (Beam/Physical Properties first, then first-seen order) and attribute_catalog() groups them into (category, attribute-names) picker sections"
    requirement: "ATTR-01"
    verification:
      - kind: unit
        ref: "tests/core/test_comparator.py#test_all_categories_are_compared"
        status: pass
      - kind: unit
        ref: "tests/core/test_comparator.py#test_leading_categories_first_then_first_seen"
        status: pass
      - kind: unit
        ref: "tests/core/test_comparator.py#test_attribute_catalog_groups_distinct_attributes"
        status: pass
      - kind: unit
        ref: "tests/core/test_comparator.py#test_attribute_catalog_empty_result"
        status: pass
    human_judgment: false
  - id: D2
    description: "Always-visible Attributes side panel with collapsible category sections and per-attribute checkboxes; unchecking an attribute removes all its rows from the results table and re-checking restores them; the choice survives re-running a comparison; default selection is Beam + Physical Properties (D-04)"
    requirement: "ATTR-02"
    verification:
      - kind: integration
        ref: "tests/gui/test_attribute_selection.py#test_picker_lists_default_categories_checked"
        status: pass
      - kind: integration
        ref: "tests/gui/test_attribute_selection.py#test_unchecking_attribute_hides_its_rows"
        status: pass
      - kind: integration
        ref: "tests/gui/test_attribute_selection.py#test_side_panel_is_always_visible"
        status: pass
      - kind: integration
        ref: "tests/gui/test_attribute_selection.py#test_selection_survives_rerun"
        status: pass
      - kind: unit
        ref: "tests/gui/test_attribute_picker.py#test_default_seed_checks_only_default_categories"
        status: pass
      - kind: unit
        ref: "tests/gui/test_attribute_picker.py#test_rebuild_keeps_choices_and_seeds_new_pairs"
        status: pass
    human_judgment: false
  - id: D3
    description: "Search box narrows what the picker shows (case-insensitive, by attribute or category name) without ever changing which attributes are checked or which table rows show; unchecking every attribute leaves an empty table with a plain-language status-bar hint"
    requirement: "ATTR-02"
    verification:
      - kind: unit
        ref: "tests/gui/test_attribute_picker.py#test_search_hides_non_matching_without_changing_checks"
        status: pass
      - kind: unit
        ref: "tests/gui/test_attribute_picker.py#test_search_is_case_insensitive_and_matches_category_names"
        status: pass
      - kind: unit
        ref: "tests/gui/test_attribute_picker.py#test_section_click_is_one_coalesced_change"
        status: pass
      - kind: integration
        ref: "tests/gui/test_attribute_selection.py#test_no_attributes_checked_shows_empty_table_and_hint"
        status: pass
      - kind: integration
        ref: "tests/gui/test_attribute_selection.py#test_search_does_not_change_table_rows"
        status: pass
    human_judgment: true
    rationale: "Task 2's <human-check> (real macOS rendering of the tree's checkboxes under qt-material, and whether the 260px panel width feels right) cannot be judged on the offscreen test platform and is deferred to end-of-phase per workflow.human_verify_mode=end-of-phase."

duration: ~14min
completed: 2026-09-30
status: complete
---

# Phase 2 Plan 1: Attribute Selection Side Panel Summary

**Replaced the hardcoded Beam/Physical Properties display filter with a user-controlled, searchable Attributes side panel wired end-to-end into the comparison table via a new QSortFilterProxyModel.**

## Performance

- **Duration:** ~14 min
- **Started:** 2026-09-30T12:13:32Z (STATE.md last activity before this plan)
- **Completed:** 2026-09-30T12:27:07Z
- **Tasks:** 2 (Task 1: tracer slice; Task 2: search box + empty-selection hint, tdd=true)
- **Files modified:** 8 (5 modified, 3 created)

## Accomplishments

- `core.comparator.compare()` no longer filters rows to a two-category allow-list; it returns every category present, Beam then Physical Properties first (`LEADING_CATEGORIES`), then every other category in first-seen order
- New `core.comparator.attribute_catalog(result)` collapses rows into (category, attribute-names) pairs for the picker -- the selection unit is the attribute name within a category, never a full per-element-path `AttributeKey`
- New `gui.attribute_picker.AttributePicker` widget: a `QTreeWidget` of collapsible category sections with per-attribute checkboxes, a case-insensitive search box that only narrows visibility (D-03), and a coalesced `selection_changed` signal so a section-click's cascade of per-leaf `itemChanged` events refilters the table once, not once per leaf
- New `gui.table_model.AttributeSelectionProxyModel`: a view-only `QSortFilterProxyModel` that shows only rows whose (category, attribute) is checked, reading the row's identity through a new `SELECTION_KEY_ROLE` data role rather than calling `sourceModel().result()`
- `gui.main_window.MainWindow` now has a non-collapsible `QSplitter` with the Attributes panel beside the results table (D-02), the proxy chain `table_model -> selection_proxy -> header_proxy -> table_view`, and a `NO_ATTRIBUTES_SELECTED_MESSAGE` status hint when every attribute is unchecked
- On first use, only Beam and Physical Properties are checked (D-04) -- the default table looks the same as it did before this plan

## Task Commits

Each task was committed atomically (Task 2 followed TDD RED -> GREEN):

1. **Task 1: End-to-end "untick an attribute in the side panel and its rows leave the results table"** - `a5f2d36` (feat)
2. **Task 2 RED: Search box narrows the picker without changing what is compared, and an empty selection is explained** - `8433aac` (test)
3. **Task 2 GREEN: same** - `aef14ec` (feat)

_Task 2 had no separate refactor commit -- nothing needed changing after GREEN passed._

## Files Created/Modified

- `src/gdtf_comparer/core/models.py` - Split `DISPLAY_CATEGORIES` into `LEADING_CATEGORIES` (row-order anchor) and `DEFAULT_SELECTED_CATEGORIES` (D-04 seed); relaxed `AttributeKey`/`FixtureModel` docstrings to no longer imply a fixed two-category set
- `src/gdtf_comparer/core/comparator.py` - `compare()` drops the category filter, tracks first-seen category index for a tolerant sort key; new `attribute_catalog(result)` function
- `src/gdtf_comparer/gui/table_model.py` - `SELECTION_KEY_ROLE` data role on `ComparisonTableModel.data()`; new `AttributeSelectionProxyModel` next to `UppercaseHeaderProxyModel`
- `src/gdtf_comparer/gui/attribute_picker.py` - New module: `AttributePicker(QWidget)` with `search_edit`, `tree`, `set_catalog`, `checked_attributes`, `visible_attributes`, `section_item`, `leaf_item`
- `src/gdtf_comparer/gui/main_window.py` - `QSplitter` side-panel layout (`attributes_group`, `attribute_picker`, `results_panel`, `content_splitter`), proxy chain wiring, `_apply_attribute_selection()`, `_show_result_status()`, `NO_ATTRIBUTES_SELECTED_MESSAGE`, window resized to 1280x720
- `tests/core/test_comparator.py` - Replaced `test_only_display_categories` with four tests covering all-category compare, ordering, and `attribute_catalog`
- `tests/gui/test_attribute_selection.py` - New: 6 real-run tests (default selection, unchecking hides rows, always-visible panel, selection survives re-run, empty-selection hint, search leaves table rows unchanged)
- `tests/gui/test_attribute_picker.py` - New: 9 widget-level tests (default seeding, search semantics, coalesced section-click, rebuild preserves/seeds choices)

## Decisions Made

- Promoted the checked (category, attribute) set to be the primary thing deciding which rows show, per the plan's `assumption_delta_decision`: GUI-layer state owned by `AttributePicker`, core stays unaware of it.
- Kept `LEADING_CATEGORIES` and `DEFAULT_SELECTED_CATEGORIES` as two separate constants with the same initial value rather than one dual-purpose name, so a future change to the D-04 default can never silently reorder or filter `compare()`'s output.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected an internally-inconsistent test expectation in the plan's own Task 2 behavior spec**
- **Found during:** Task 2 (writing the RED test `test_search_hides_non_matching_without_changing_checks`)
- **Issue:** The plan specifies substring matching on the casefolded attribute name (`_apply_search`'s action text) and a test catalog where Beam has both `BeamAngle` and `FieldAngle`, then asserts that searching `"angle"` should show only `("Beam", "BeamAngle")`. But `"FieldAngle".casefold()` (`"fieldangle"`) genuinely contains `"angle"` as a substring (verified with a scratch Python check), so a correct substring-match implementation also matches `FieldAngle` -- the plan's expected single-result assertion cannot be true simultaneously with its own stated matching rule.
- **Fix:** Implemented `_apply_search` exactly as specified (case-insensitive substring match on attribute or category text). Corrected the test assertion to `visible_attributes() == {("Beam", "BeamAngle"), ("Beam", "FieldAngle")}` (both genuinely match), keeping every other assertion in that test (Physical Properties and Extra Category sections hidden, checked set unchanged, no stray emission) exactly as specified.
- **Files modified:** `tests/gui/test_attribute_picker.py`
- **Verification:** `pytest tests/gui/test_attribute_picker.py -q -W error::DeprecationWarning` passes; confirmed the substring fact independently with a one-off Python check before changing the assertion.
- **Committed in:** `aef14ec` (Task 2 GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 bug, in a test's expected value rather than in application code)
**Impact on plan:** No scope creep. The implementation matches the plan's `_apply_search` spec verbatim; only the test's own internally-inconsistent expected value was corrected.

## Issues Encountered

None beyond the deviation above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `attribute_catalog()` and `AttributePicker` are ready for Plan 02-02 to feed the full 60+ attribute set through unchanged -- no picker-side change needed, just a richer catalog.
- `AttributeSelectionProxyModel` establishes the exact proxy pattern (view-only, reads a data role, chains after the source model) Plan 02-03's differences-only proxy will follow, inserted at the same point in the `table_model -> ... -> header_proxy` chain.
- Task 2's `<human-check>` (real qt-material rendering of the checkable tree, panel-width feel) is deferred to end-of-phase per `workflow.human_verify_mode=end-of-phase` and is carried into `/gsd-verify-work` (see coverage entry D3).
- **REQUIREMENTS.md traceability note:** ATTR-01 ("browse/search the full set of GDTF attributes, 60+ properties") is claimed by both this plan's frontmatter and 02-02-PLAN.md's. `requirements.ready-ids` correctly reported ATTR-01 as still `blocked` (02-02 hasn't executed yet) even though this plan delivers the browsing/search mechanism itself -- REQUIREMENTS.md marks only ATTR-02 Complete for now; ATTR-01 stays Pending until 02-02 lands the full attribute set. `requirements-completed` in this SUMMARY's frontmatter still lists both IDs verbatim from the plan's `requirements` field, per the executor's field-population contract.

---
*Phase: 02-attribute-browsing-diff-highlighting*
*Completed: 2026-09-30*

## Self-Check: PASSED

All created files verified present on disk; all task commit hashes (`a5f2d36`, `8433aac`, `aef14ec`) verified present in git history.
