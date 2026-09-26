---
status: testing
phase: 01-foundation-rebuild
source: [01-VERIFICATION.md]
started: 2026-09-26T23:01:03Z
updated: 2026-09-26T23:01:03Z
---

## Current Test

number: 1
name: Visual theme legibility (light/dark switching)
expected: |
  Flat Material-style widgets with blue accents (no stock Tk/native-legacy look);
  switching OS Appearance re-themes the open window within a second with no restart;
  table text, buttons and the error dialog stay clearly legible in both modes.
awaiting: user response

## Tests

### 1. Visual theme legibility (light/dark switching)
expected: |
  From the repo root run `PYTHONPATH=src .venv/bin/python -m gdtf_comparer.app` on macOS
  with System Settings > Appearance set to Light, then switch to Dark while the window is
  open. Flat Material-style widgets with blue accents (no stock Tk/native-legacy look);
  switching Appearance re-themes the open window within a second with no restart; table
  text, buttons and the error dialog stay clearly legible in both modes.
result: [pending]

### 2. Real-file end-to-end run
expected: |
  Follow README Setup + Run from a fresh terminal; pick one real target .gdtf and two or
  more real comparison .gdtf files (e.g. from GDTF-Share or a manufacturer site), click Run
  Comparison, then add a non-GDTF file renamed to .gdtf and run again. The window stays
  responsive while parsing; the table shows Beam rows per beam geometry path, Physical
  Properties rows per model plus one 'Fixture' Weight row, with every comparison file as a
  column; the renamed file produces one friendly dialog naming it, the table is cleared, and
  a following valid run works without restarting.
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
