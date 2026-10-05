---
status: complete
phase: 03-compare-profiles-export
source: [03-VERIFICATION.md]
started: 2026-10-04T23:45:00Z
updated: 2026-10-05T03:25:00Z
---

## Current Test

[testing complete]

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
result: issue
reported: "We need to fix the UI — screenshots show the profile toolbar
  controls in the 260px Attributes panel are clipped/truncated: the profile
  dropdown reads 'No si▾' instead of 'No saved profiles yet', the Save
  button reads 'AVE.' instead of 'SAVE PROFILE', and the Manage button
  reads 'M...e' instead of 'MANAGE'. This fails the explicit acceptance
  criterion that the toolbar row fits the 260px panel without clipping."
severity: major

### 2. Crash / power-loss resilience of the saved-profiles file
expected: |
  This one is a judgment call, not a click-through: the way profiles are
  saved (write to a temp file, then atomically swap it in) is designed so
  that an interrupted save — a crash, power loss, or quitting mid-save —
  always leaves either the complete old file or the complete new file,
  never a half-written one. If you're comfortable judging this from a
  description (rather than literally pulling the plug), mark it passed;
  otherwise skip it.
result: pass

## Summary

total: 2
passed: 1
issues: 1
pending: 0
skipped: 0
blocked: 0

## Gaps

- gap_id: G-03-1
  truth: "The profile toolbar row fits the 260px Attributes panel without clipping, with every dialog/message reading clearly to a non-technical user."
  status: failed
  reason: "User reported: profile toolbar controls are clipped/truncated in the 260px Attributes panel — dropdown reads 'No si▾' instead of 'No saved profiles yet', Save button reads 'AVE.' instead of 'SAVE PROFILE', Manage button reads 'M...e' instead of 'MANAGE'."
  severity: major
  test: 1
  artifacts: []
  missing: []

- gap_id: G-03-2
  truth: "New scope approved during UAT (not an original Phase 03 acceptance criterion): the 'Compare with' file list shows a per-file indicator of whether that comparison file matches the target GDTF."
  status: failed
  reason: "User requested during UAT: \"we should have an indicator in the 'Compare with' that lets the use know if there is a match to the main GDTF file.\" User confirmed this should be added now, alongside the G-03-1 fix, rather than deferred."
  severity: minor
  test: 1
  artifacts: []
  missing: []
