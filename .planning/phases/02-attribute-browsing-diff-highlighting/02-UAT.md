---
status: partial
phase: 02-attribute-browsing-diff-highlighting
source: [02-VERIFICATION.md]
started: 2026-10-12T02:41:00Z
updated: 2026-10-12T02:49:23.555Z
---

## Current Test

[testing complete]

## Tests

### 1. Plan 02-01 Task 2 human-check: open the app, run a comparison, use the Attributes panel (untick/re-tick BeamAngle, type "angle" in search, clear it), and confirm the panel cannot be dragged shut.
expected: Attributes panel always visible, Beam + Physical Properties open and fully ticked by default; unticking/ticking BeamAngle removes/restores its rows; search narrows the panel list without changing the table; table has no horizontal scrollbar with 1-2 comparison files.
result: pass

### 2. Plan 02-02 Task 2 human-check: open the app with two real third-party moving-light .gdtf files, expand a 'DMX: ...' section, tick Pan, and search "gobo".
expected: Several naturally-named 'DMX: ...' sections below Beam/Physical Properties, closed and unticked, totalling 60+ attributes on a real fixture; ticking Pan adds its six rows; search narrows the panel without changing the table.
result: blocked
blocked_by: third-party
reason: "User does not currently have a real third-party manufacturer .gdtf file to test with."

### 3. Plan 02-03 Task 3 human-check: run a comparison, observe cell tinting, toggle 'Show differences only', then switch the OS between Light and Dark while the app is open.
expected: Differing comparison cells are tinted and easy to read/distinguish from the alternating-row stripe in both themes; the toggle hides/restores rows and explains an empty result; switching OS appearance re-tints the table live with no re-run.
result: pass

## Summary

total: 3
passed: 2
issues: 0
pending: 0
skipped: 0
blocked: 1

## Gaps

None yet — awaiting human test results. Note for triage context (not a gap in this phase's own requirements): `02-REVIEW.md`/`02-REVIEW-DISPOSITION.md` record one open critical finding (CR-01: stale comparison results can silently land on screen if the file selection changes while a worker is still in flight) plus two warnings and one info item, all tracked separately and not blocking this UAT.
