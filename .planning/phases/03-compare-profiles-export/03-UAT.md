---
status: testing
phase: 03-compare-profiles-export
source: [03-VERIFICATION.md]
started: 2026-10-04T23:45:00Z
updated: 2026-10-04T23:45:00Z
---

## Current Test

number: 1
name: Whole-phase real-app walkthrough
expected: |
  The saved-confirmation message, the overwrite question (and that No truly
  changes nothing), persistence of "My Test Spec" in the dropdown across a
  genuine app restart using the real per-user profiles folder, exactly the
  previously-ticked attributes re-checked (D-03) with the unticked Beam
  attribute staying unticked, the not-found message appearing when the new
  fixtures lack spec items (D-06), the dropdown reflecting the rename, and
  delete's No-keeps/Yes-removes-everywhere behavior — plus that the toolbar
  row fits the 260px Attributes panel without clipping and every
  dialog/message reads clearly to a non-technical user.
awaiting: user response

## Tests

### 1. Whole-phase real-app walkthrough
expected: |
  Save a profile named "My Test Spec". Attempt to overwrite it with a
  case-different name and answer No (nothing should change). Quit the app
  completely (Cmd+Q — a real quit, not just closing a window). Reopen it.
  Load "My Test Spec" from the dropdown. Run a comparison against different
  fixture files — ideally ones missing some of the spec items you saved.
  Rename the profile. Then delete it: answer No first (profile stays), then
  Yes (profile is gone from the dropdown).
result: [pending]

### 2. Crash / power-loss resilience of the saved-profiles file
expected: |
  This one is a judgment call, not a click-through: the way profiles are
  saved (write to a temp file, then atomically swap it in) is designed so
  that an interrupted save — a crash, power loss, or quitting mid-save —
  always leaves either the complete old file or the complete new file,
  never a half-written one. If you're comfortable judging this from a
  description (rather than literally pulling the plug), mark it passed;
  otherwise skip it.
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
