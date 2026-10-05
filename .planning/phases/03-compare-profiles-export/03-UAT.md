---
status: complete
phase: 03-compare-profiles-export
source: [03-VERIFICATION.md]
started: 2026-10-05T12:05:00Z
updated: 2026-10-05T13:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Real-app confirmation of the G-03-1 layout fix and G-03-2 match-indicator feature
expected: |
  Gray dots before any run; green/red dots with explanatory tooltips after
  Run Comparison; the dropdown, "Save…" and "Manage" fully readable at every
  width down to the drag floor; all dots turn gray again when nothing is
  checked, and again when a new file is added.
result: issue
reported: "when I widen I can read it all so I think that box just needs to be a little bigger"
severity: cosmetic

## Summary

total: 1
passed: 0
issues: 1
pending: 0
skipped: 0
blocked: 0

## Gaps

- gap_id: G-03-1
  truth: "The dropdown, \"Save…\", and \"Manage\" controls stay fully readable at every Attributes-panel width down to the drag floor — never truncated to \"AVE.\", \"M...e\", or \"No si▾\"."
  status: failed
  reason: "User reported: when I widen I can read it all so I think that box just needs to be a little bigger"
  severity: cosmetic
  test: 1
  artifacts: []
  missing: []

## Previous Round (closed)

The first UAT round (2026-10-04, source: 03-VERIFICATION.md) reported one
issue (G-03-1, toolbar clipping) and one approved new-scope request (G-03-2,
match indicator). Both were closed by gap-closure plan 03-04, and the
crash/power-loss resilience judgment call passed outright. See git history
for the original round's full content (commit a0f3c34 and prior).
