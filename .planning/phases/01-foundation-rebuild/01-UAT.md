---
status: testing
phase: 01-foundation-rebuild
source: [01-VERIFICATION.md]
started: 2026-09-28T04:20:00Z
updated: 2026-09-28T04:20:00Z
---

## Current Test

number: 1
name: Visual theme legibility and header readability (re-check after fixes)
expected: |
  CATEGORY, ELEMENT and ATTRIBUTE read in full in both Light and Dark mode.
  The different fixture's column shows its fixture name. The two same-named
  revisions show their file names, elided in the middle so the revision
  ending (...V2.gdtf / ...V3.gdtf) stays visible. No header is cut off at
  its start, and no column grows wide just because a file name is long.
  Hovering a header shows the manufacturer, the fixture name and the full
  file path.
awaiting: user response

## Tests

### 1. Visual theme legibility and header readability (re-check after fixes)
expected: |
  On macOS, from the repo root, run
  `PYTHONPATH=src .venv/bin/python -m gdtf_comparer.app` with System
  Settings > Appearance set to Light. Pick a real target .gdtf and two
  comparison files: two revisions of the same fixture (e.g. ...@V2 and
  ...@V3 from GDTF-Share) and one different fixture. Click Run Comparison,
  hover each per-file header, then switch Appearance to Dark with the
  window still open. CATEGORY, ELEMENT and ATTRIBUTE read in full in both
  modes. The different fixture's column shows its fixture name. The two
  same-named revisions show their file names, elided in the middle so the
  revision ending stays visible. No header is cut off at its start, and no
  column grows wide just because a file name is long. Hovering a header
  shows the manufacturer, the fixture name and the full file path.
result: [pending]

### 2. Real multi-file end-to-end run with no forced horizontal scroll
expected: |
  Follow README Setup + Run from a fresh terminal; pick a real target
  .gdtf and 3+ real comparison .gdtf files with realistically long
  manufacturer/model names, click Run Comparison, and confirm no
  horizontal scrollbar is needed at the default window size; then add a
  non-GDTF file renamed to .gdtf and run again. The window stays
  responsive while parsing; every comparison file renders as a readable,
  non-overlapping column with no forced scroll; the renamed file produces
  one friendly dialog naming it, the table is cleared, and a following
  valid run works without restarting.
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
