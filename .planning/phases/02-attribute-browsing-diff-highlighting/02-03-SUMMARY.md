---
phase: 02-attribute-browsing-diff-highlighting
plan: 03
subsystem: ui
tags: [pyside6, qt, qt-material, diff-highlighting, proxy-model, tdd]

# Dependency graph
requires:
  - phase: 02-attribute-browsing-diff-highlighting
    provides: "Plan 02-01's AttributeSelectionProxyModel / proxy-chain pattern and Plan 02-02's full DMX attribute-definition row set -- this plan tints and filters that same row set with no core or picker change"
provides:
  - "gui.theme.diff_highlight_color(theme_name)/current_theme_name(app): theme-derived, lru_cached diff-highlight color helpers"
  - "gui.table_model.ComparisonTableModel BackgroundRole branch + set_highlight_color/highlight_color, driven by ComparisonRow.differs only"
  - "gui.table_model.BackgroundBrushDelegate: paints the BackgroundRole brush qt-material's stylesheet otherwise suppresses"
  - "gui.table_model.DifferencesOnlyProxyModel + ANY_DIFFERS_ROLE: view-only 'show differences only' filter"
  - "gui.main_window.MainWindow: differences_only_checkbox, _apply_highlight_theme, _apply_differences_only, _on_color_scheme_changed wired into the results panel and proxy chain"
affects: ["Phase 3 (EXPORT-02 diff-only export can reuse ComparisonRow.any_differs the same way this plan's toggle does)"]

# Actuals (#2632) — pairs with the plan's estimate to calibrate future estimates.
actuals:
  tokens: 12222
  tasks: 3
  commits: 5
  plan_head_before: 57d8c88cb3ecfb88691d2d099f05101937736236

tech-stack:
  added: []
  patterns:
    - "BackgroundBrushDelegate: a one-purpose QStyledItemDelegate that fills option.rect with the index's BackgroundRole brush before super().paint() -- required because qt-material's QTableView::item stylesheet rule otherwise makes Qt ignore an item's own BackgroundRole brush (measured at planning time, not assumed)"
    - "DifferencesOnlyProxyModel reads ANY_DIFFERS_ROLE from the source, mirroring AttributeSelectionProxyModel's SELECTION_KEY_ROLE pattern -- a proxy never calls sourceModel().result() directly, so it works at any position in the chain"
    - "diff_highlight_color(theme_name) is a pure function returning a fresh QColor; the expensive qt_material.get_theme() lookup is isolated behind a functools.lru_cache keyed by (theme_name, key) inside _theme_color_hex, called once per theme change (construction, and MainWindow._on_color_scheme_changed), never inside data()"

key-files:
  created:
    - tests/gui/test_diff_highlighting.py
    - tests/gui/test_differences_only_toggle.py
  modified:
    - src/gdtf_comparer/gui/theme.py
    - src/gdtf_comparer/gui/table_model.py
    - src/gdtf_comparer/gui/main_window.py

key-decisions:
  - "Confirmed the plan's assumption_delta_decision: a BackgroundRole QColor alone does not paint under qt-material (verified with test_highlight_is_painted_under_qt_material's pixel sampling before and after adding BackgroundBrushDelegate); the delegate is required, not optional, for DIFF-01 to be true on screen"
  - "Highlight color computed once per theme name (construction, live OS switch) and cached as a QBrush on the model -- never recomputed in data(), verified by test_theme_file_parsed_once_per_theme monkeypatching qt_material.get_theme and counting calls"
  - "DifferencesOnlyProxyModel inserted between AttributeSelectionProxyModel and UppercaseHeaderProxyModel (table_model -> selection_proxy -> differences_proxy -> header_proxy -> table_view), matching the chain position 02-01-PLAN.md's design notes reserved for it"

patterns-established:
  - "A render-level (pixel) test proves a Qt highlighting feature is visible on screen, not just present in model data -- data()-only tests would have passed against qt-material's suppression bug undetected"

requirements-completed: [DIFF-01]

coverage:
  - id: D1
    description: "Every comparison-file cell whose value differs from the target is tinted with the theme's highlight color, painted on screen (proven with pixel sampling in the light theme), while the Target column, fixed columns and equal cells stay untinted; two calls to diff_highlight_color for the same theme return equal but distinct QColor objects"
    requirement: "DIFF-01"
    verification:
      - kind: unit
        ref: "tests/gui/test_diff_highlighting.py#test_differing_comparison_cell_is_highlighted"
        status: pass
      - kind: unit
        ref: "tests/gui/test_diff_highlighting.py#test_highlight_color_is_theme_primary_tint"
        status: pass
      - kind: automated_ui
        ref: "tests/gui/test_diff_highlighting.py#test_highlight_is_painted_under_qt_material"
        status: pass
      - kind: unit
        ref: "tests/gui/test_diff_highlighting.py#test_highlight_follows_differs_flags_not_text"
        status: pass
    human_judgment: false
  - id: D2
    description: "'Show differences only' sits above the table (unticked by default), hides every row where no comparison value differs while keeping cell highlights and row order, explains an empty result in the status bar, survives re-runs, never mutates the ComparisonResult, and defers correctly to the no-attributes-selected message"
    requirement: "DIFF-01"
    verification:
      - kind: integration
        ref: "tests/gui/test_differences_only_toggle.py#test_toggle_starts_unticked_above_table"
        status: pass
      - kind: integration
        ref: "tests/gui/test_differences_only_toggle.py#test_toggle_hides_rows_without_differences"
        status: pass
      - kind: integration
        ref: "tests/gui/test_differences_only_toggle.py#test_toggle_state_survives_rerun"
        status: pass
      - kind: integration
        ref: "tests/gui/test_differences_only_toggle.py#test_all_equal_shows_no_differences_message"
        status: pass
      - kind: integration
        ref: "tests/gui/test_differences_only_toggle.py#test_no_attributes_selected_message_takes_precedence"
        status: pass
      - kind: integration
        ref: "tests/gui/test_differences_only_toggle.py#test_toggle_without_result_is_harmless"
        status: pass
      - kind: integration
        ref: "tests/gui/test_differences_only_toggle.py#test_toggle_never_mutates_result"
        status: pass
      - kind: unit
        ref: "tests/gui/test_differences_only_toggle.py#test_differences_proxy_edge_results"
        status: pass
    human_judgment: false
  - id: D3
    description: "A live OS light/dark switch re-tints differing cells without re-running the comparison, the theme lookup runs at most once per theme (not per cell), and with several comparison files each column is tinted exactly where its own differs flag is True (including a short differs tuple and an out-of-range column, which never raise)"
    requirement: "DIFF-01"
    verification:
      - kind: automated_ui
        ref: "tests/gui/test_diff_highlighting.py#test_live_dark_switch_retints_without_rerun"
        status: pass
      - kind: unit
        ref: "tests/gui/test_diff_highlighting.py#test_theme_file_parsed_once_per_theme"
        status: pass
      - kind: unit
        ref: "tests/gui/test_diff_highlighting.py#test_three_comparisons_boundaries"
        status: pass
      - kind: unit
        ref: "tests/gui/test_diff_highlighting.py#test_short_differs_tuple_never_raises"
        status: pass
    human_judgment: false
  - id: D4
    description: "On real macOS rendering in both light and dark theme, the tint is comfortably readable and easy to tell apart from qt-material's alternating-row and selected-row colours; 'Show differences only' behaves as expected in the live app; a live System Settings Light/Dark switch re-tints the table without clicking Run Comparison again"
    verification: []
    human_judgment: true
    rationale: "Task 3's <human-check> requires real macOS rendering and human judgment of color readability/distinguishability, which the offscreen test platform cannot provide (backstop truth per must_haves). Deferred to end-of-phase per workflow.human_verify_mode=end-of-phase and carried into /gsd-verify-work, same pattern as 02-01's D3 and 02-02's D5."

duration: ~15min
completed: 2026-09-30
status: complete
---

# Phase 2 Plan 3: Diff Highlighting & Differences-Only Toggle Summary

**Differing comparison cells are tinted with the live qt-material theme's primaryColor via a new BackgroundBrushDelegate (required because qt-material's own stylesheet otherwise suppresses BackgroundRole painting), plus a "Show differences only" toggle and a live OS light/dark re-tint, both reading only `ComparisonRow.differs`/`any_differs`.**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-09-30T11:08:27-05:00 (STATE.md last activity before this plan)
- **Completed:** 2026-09-30T11:18:01-05:00
- **Tasks:** 3 (Task 1: tracer slice; Task 2: differences-only toggle, tdd=true; Task 3: live theme switch + boundaries, tdd=true)
- **Files modified:** 5 (3 modified, 2 created)

## Accomplishments

- `gui.theme` gained `DIFF_HIGHLIGHT_ALPHA`/`DIFF_HIGHLIGHT_THEME_KEY` constants, an `lru_cache`d `_theme_color_hex()` and `diff_highlight_color()`/`current_theme_name()` -- the theme XML is parsed at most once per theme name, never per painted cell
- `gui.table_model.ComparisonTableModel` answers `BackgroundRole` from `ComparisonRow.differs` alone (never display text), with `set_highlight_color`/`highlight_color` and a bounds-checked `_background()` that never raises on a short `differs` tuple or an out-of-range column
- New `BackgroundBrushDelegate` fills a cell's `BackgroundRole` brush before Qt's own item painting -- proven necessary, not assumed, by a pixel-sampling test that failed before the delegate existed and passes after
- New `DifferencesOnlyProxyModel` + `ANY_DIFFERS_ROLE` hide rows where nothing differs, inserted into the proxy chain as `table_model -> selection_proxy -> differences_proxy -> header_proxy -> table_view`
- `gui.main_window.MainWindow` gained a "Show differences only" checkbox above the table (unticked by default), `NO_DIFFERENCES_MESSAGE` in `_show_result_status()` (deferring correctly to `NO_ATTRIBUTES_SELECTED_MESSAGE`), and `_on_color_scheme_changed` connected to `QApplication.styleHints().colorSchemeChanged` so a live OS switch re-tints the table with no re-run

## Task Commits

Each task was committed atomically (Tasks 2 and 3 followed TDD RED -> GREEN):

1. **Task 1: End-to-end "run a comparison and see each differing comparison cell tinted"** - `c40f0d1` (feat)
2. **Task 2 RED: "Show differences only" toggle tests** - `7295bb9` (test)
3. **Task 2 GREEN: DifferencesOnlyProxyModel + checkbox wiring** - `fcaa323` (feat)
4. **Task 3 RED: live theme switch, parse-once cache, three-comparison edges** - `a021042` (test)
5. **Task 3 GREEN: `_on_color_scheme_changed`** - `8b58467` (feat)

_No task needed a separate refactor commit -- every GREEN implementation matched the plan's spec with nothing left to clean up._

## Files Created/Modified

- `src/gdtf_comparer/gui/theme.py` - `DIFF_HIGHLIGHT_ALPHA`, `DIFF_HIGHLIGHT_THEME_KEY`, `_theme_color_hex` (lru_cached), `diff_highlight_color`, `current_theme_name`
- `src/gdtf_comparer/gui/table_model.py` - `ANY_DIFFERS_ROLE`, `ComparisonTableModel.set_highlight_color`/`highlight_color`/`_background`, `BackgroundRole` branch in `data()`, `DifferencesOnlyProxyModel`, `BackgroundBrushDelegate`
- `src/gdtf_comparer/gui/main_window.py` - delegate installed on the table view, `_apply_highlight_theme`, `differences_only_checkbox` + `_apply_differences_only`, `differences_proxy` inserted into the proxy chain, `NO_DIFFERENCES_MESSAGE` case in `_show_result_status`, `_on_color_scheme_changed` connected to the live OS scheme signal
- `tests/gui/test_diff_highlighting.py` - New: model-level, pixel-level (light and dark theme), flags-not-text precision, live-switch, parse-once-cache, and three-comparison boundary tests
- `tests/gui/test_differences_only_toggle.py` - New: toggle placement/order, multi-category filtering, re-run persistence, status messages, no-result/zero-comparison edges, result-never-mutated

## Decisions Made

- Confirmed the plan's `assumption_delta_decision` by measurement: a `BackgroundRole` `QColor` alone does not render under qt-material's stylesheet (a data()-only test would have passed while the user saw nothing); `BackgroundBrushDelegate` is required, and the pixel test proves it on screen, not just in model data
- Kept the highlight color entirely GUI-owned: `ComparisonTableModel` never imports `gui.theme` or `QApplication` (verified by the plan's `grep -cE "QApplication|gui\.theme"` acceptance check printing 0) -- `MainWindow` is the only place that resolves a theme name to a color and hands the model a ready `QBrush`

## Deviations from Plan

None - plan executed exactly as written across all three tasks.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- DIFF-01 is now fully delivered: cell highlighting (Task 1), the differences-only toggle (Task 2), and the live theme switch plus multi-file boundary correctness (Task 3) are all in place and reuse only `ComparisonRow.differs`/`any_differs` -- no new diff-computation logic exists anywhere in the GUI layer.
- Task 3's `<human-check>` (real macOS rendering, readability, live Light/Dark switch, "Show differences only" in the live app) is deferred to end-of-phase per `workflow.human_verify_mode=end-of-phase` and is carried into `/gsd-verify-work` (see coverage entry D4), the same pattern 02-01's D3 and 02-02's D5 already established.
- This is the last plan in Phase 2. All three plans (02-01, 02-02, 02-03) are now complete; the phase is ready for `/gsd-verify-work`, which should collect the deferred human checks from all three SUMMARYs (D3 in 02-01, D5 in 02-02, D4 here) in one pass.
- Phase 3's `EXPORT-02` ("diff-only export") can reuse `ComparisonRow.any_differs` the exact way `DifferencesOnlyProxyModel` does here -- no new core logic needed there either.

---
*Phase: 02-attribute-browsing-diff-highlighting*
*Completed: 2026-09-30*

## Self-Check: PASSED

All modified/created files verified present on disk; all task commit hashes (`c40f0d1`, `7295bb9`, `fcaa323`, `a021042`, `8b58467`) verified present in git history.
