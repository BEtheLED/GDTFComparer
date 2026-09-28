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
  artifacts: []
  missing: []

- gap_id: G-01-2
  truth: "comparison results are presented in a clearly readable table, with every comparison file as a column"
  status: failed
  reason: "User reported: functionality all worked as designed, but the table layout is a little hard to read. Screenshot shows per-file column headers using the full filename (e.g. 'TARGET: ASTERA_LED_TECHNOLOGY@AF250_LEOFRESNEL@TESTED_BY_ASTERA___V3') truncated/cut off at the column edge instead of wrapping or being shortened, and a horizontal scrollbar is needed to see full headers/data."
  severity: minor
  test: 2
  artifacts: []
  missing: []
