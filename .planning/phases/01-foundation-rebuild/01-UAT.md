---
status: complete
phase: 01-foundation-rebuild
source: [01-VERIFICATION.md]
started: 2026-09-26T23:01:03Z
updated: 2026-09-27T21:55:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Visual theme legibility (light/dark switching)
expected: |
  From the repo root run `PYTHONPATH=src .venv/bin/python -m gdtf_comparer.app` on macOS
  with System Settings > Appearance set to Light, then switch to Dark while the window is
  open. Flat Material-style widgets with blue accents (no stock Tk/native-legacy look);
  switching Appearance re-themes the open window within a second with no restart; table
  text, buttons and the error dialog stay clearly legible in both modes.
result: issue
reported: "Light/dark switching works fine, re-themes live without restart. But table column headers are visually cut off — CATEGORY shows as ATEGOR, ELEMENT and ATTRIBUTE also truncated (confirmed via screenshot)."
severity: minor

### 2. Real-file end-to-end run
expected: |
  Follow README Setup + Run from a fresh terminal; pick one real target .gdtf and two or
  more real comparison .gdtf files (e.g. from GDTF-Share or a manufacturer site), click Run
  Comparison, then add a non-GDTF file renamed to .gdtf and run again. The window stays
  responsive while parsing; the table shows Beam rows per beam geometry path, Physical
  Properties rows per model plus one 'Fixture' Weight row, with every comparison file as a
  column; the renamed file produces one friendly dialog naming it, the table is cleared, and
  a following valid run works without restarting.
result: issue
reported: "They all worked as designed. I do think we will need to look at the table layout some it is a littl hard to read"
severity: minor

## Summary

total: 2
passed: 0
issues: 2
pending: 0
skipped: 0
blocked: 0

## Gaps

- gap_id: G-01-1
  truth: "table text, buttons and the error dialog stay clearly legible in both modes"
  status: failed
  reason: "User reported: table column headers (CATEGORY, ELEMENT, ATTRIBUTE) are visually truncated/cut off — e.g. CATEGORY shows as ATEGOR — confirmed via screenshot"
  severity: minor
  test: 1
  root_cause: "qt-material's QHeaderView::section CSS applies text-transform: uppercase at paint time (qt_material/material.qss.template:1326-1336, applied via src/gdtf_comparer/gui/theme.py:64), but resizeColumnsToContents() (src/gdtf_comparer/gui/main_window.py:279) sizes columns from the original mixed-case label text (src/gdtf_comparer/gui/table_model.py:97-108), which Qt's size-hint calc doesn't know will be uppercased/widened. Center-aligned headers then clip symmetrically from both ends."
  artifacts:
    - path: "src/gdtf_comparer/gui/main_window.py"
      issue: "resizeColumnsToContents() at line 279 sizes columns from pre-transform label text"
    - path: "src/gdtf_comparer/gui/table_model.py"
      issue: "_header_label() (lines 97-108) returns mixed-case strings; width calc doesn't account for CSS uppercase transform"
  missing:
    - "After resizeColumnsToContents(), widen affected header columns using QFontMetrics.horizontalAdvance(label.upper()) plus the qt-material stylesheet's 24px x 2 padding"
  debug_session: ".planning/debug/g-01-1-header-clip.md"

- gap_id: G-01-2
  truth: "comparison results are presented in a clearly readable table, with every comparison file as a column"
  status: failed
  reason: "User reported: functionality all worked as designed, but the table layout is a little hard to read. Screenshot shows per-file column headers using the full filename (e.g. 'TARGET: ASTERA_LED_TECHNOLOGY@AF250_LEOFRESNEL@TESTED_BY_ASTERA___V3') truncated/cut off at the column edge instead of wrapping or being shortened, and a horizontal scrollbar is needed to see full headers/data."
  severity: minor
  test: 2
  root_cause: "_header_label() (table_model.py:97-112) uses the raw GDTF filename (os.path.basename, models.py:75-78) verbatim as the column header with no truncation, and resizeColumnsToContents() (main_window.py:279) sizes columns to fully fit that long text with no max-section cap. Oversized columns push total table width past the viewport, forcing a horizontal scrollbar; header scrolls in lockstep with the body, so at any scroll offset the start of the long header string is pushed off-screen, reading as clipping."
  artifacts:
    - path: "src/gdtf_comparer/gui/table_model.py"
      issue: "_header_label() (lines 97-112) builds headers from the raw filename with no truncation/elision"
    - path: "src/gdtf_comparer/core/models.py"
      issue: "file_name (lines 75-78) is the full Manufacturer@Model@Revision.gdtf basename; a shorter human-readable name/manufacturer already exists on the model (lines 70-71) but isn't used for headers"
    - path: "src/gdtf_comparer/gui/main_window.py"
      issue: "resizeColumnsToContents() (line 279) has no max-section-size cap, so long headers grow columns past the viewport instead of eliding"
  missing:
    - "Use FixtureModel's short name/manufacturer fields (models.py:70-71) for column header labels instead of the raw filename; keep the full filename in the existing _header_tooltip (table_model.py:114-125)"
    - "Cap column width via QHeaderView.setMaximumSectionSize (or clamp after resizeColumnsToContents()) so any still-long label elides natively at the end instead of forcing horizontal scroll"
  debug_session: ".planning/debug/g-01-2-filename-header-scroll.md"
