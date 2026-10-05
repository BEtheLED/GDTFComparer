---
status: testing
phase: 03-compare-profiles-export
source: [03-VERIFICATION.md]
started: 2026-10-05T12:05:00Z
updated: 2026-10-05T12:05:00Z
---

## Current Test

number: 1
name: Real-app confirmation of the G-03-1 layout fix and G-03-2 match-indicator feature
expected: |
  Pick a target GDTF file. Add two comparison files (one you expect close to
  the target, one you expect different). Look at "Compare with" before
  clicking anything — both files should show a small gray dot.

  Click Run Comparison. Look at "Compare with" again, and hover each file:
  the dot colors should update to green (close to target) / red (different),
  and hovering should show the file's path plus a plain-language sentence
  explaining the color.

  In the Attributes panel on the left, look at the row with the dropdown,
  "Save…" and "Manage" at the top. Try dragging the Attributes-panel divider
  as far left as it will go, then back. The dropdown, "Save…" and "Manage"
  should stay fully readable the whole time — never "AVE.", "M...e", or
  "No si▾".

  Untick every checked attribute — both dots should turn gray again (nothing
  is currently being checked, so there's nothing to report).

  Click Add Files… and add one more comparison file — every dot, including
  the two pre-existing ones, should turn gray again until you click Run
  Comparison again.
awaiting: user response

## Tests

### 1. Real-app confirmation of the G-03-1 layout fix and G-03-2 match-indicator feature
expected: |
  Gray dots before any run; green/red dots with explanatory tooltips after
  Run Comparison; the dropdown, "Save…" and "Manage" fully readable at every
  width down to the drag floor; all dots turn gray again when nothing is
  checked, and again when a new file is added.
result: [pending]

## Summary

total: 1
passed: 0
issues: 0
pending: 1
skipped: 0
blocked: 0

## Gaps

## Previous Round (closed)

The first UAT round (2026-10-04, source: 03-VERIFICATION.md) reported one
issue (G-03-1, toolbar clipping) and one approved new-scope request (G-03-2,
match indicator). Both were closed by gap-closure plan 03-04, and the
crash/power-loss resilience judgment call passed outright. See git history
for the original round's full content (commit a0f3c34 and prior).
