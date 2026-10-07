---
status: complete
phase: 03-compare-profiles-export
source: [03-VERIFICATION.md]
started: 2026-10-05T12:05:00Z
updated: 2026-10-07T14:10:00Z
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
result: pass
note: |
  Re-tested against a freshly launched window on 2026-10-07. Screenshot
  confirms: dropdown sits on its own row above "Save…"/"Manage" (two-row
  layout, the G-03-1 fix is present), both labels fully readable, and both
  comparison-file dots are red after Run Comparison. Confirms the prior
  "issue" report (test 1, round 2) was indeed the stale-window false
  positive diagnosed below — closing G-03-1 as invalidated, not reopening it.

### 2. Comparison values populate for every compare file, not just the target
expected: |
  Actual attribute values read from each comparison file; genuine per-file
  N/A only when that file truly lacks the attribute.
result: issue
reported: "I don't think that it is actually looking at more than 1 GDTF file as any other file I add just says NA not what the value is in the file."
severity: major

## Summary

total: 2
passed: 1
issues: 1
pending: 0
skipped: 0
blocked: 0

## Gaps

- gap_id: G-03-1
  truth: "The dropdown, \"Save…\", and \"Manage\" controls stay fully readable at every Attributes-panel width down to the drag floor — never truncated to \"AVE.\", \"M...e\", or \"No si▾\"."
  status: invalidated
  reason: "User reported: when I widen I can read it all so I think that box just needs to be a little bigger"
  severity: cosmetic
  test: 1
  root_cause: "False positive, not a code defect. The window the user tested (PID 46645) launched 2026-10-04 20:19:26 PDT, 37 minutes before the G-03-1 fix was committed (8ab8516) and 46 minutes before it merged to main (c7b9e10). Python loads main_window.py once at startup, so that window kept running the old single-row toolbar for the whole session, including during this round-2 UAT. The pre-fix code was confirmed to reproduce the exact clipped strings (\"No s▾\", \"iAVE.\", \"M…e\") at the current default width. The current code (two-row toolbar, ATTRIBUTES_PANEL_MIN_WIDTH_PX = 240 in src/gdtf_comparer/gui/main_window.py lines 344-389/195) was measured clean at the default width, the 240px drag floor, and every 10px in between, on real macOS at both DPR 1.0 and 2.0, in both themes."
  debug_session: ".planning/debug/attributes-panel-toolbar-clipping-default-width.md"
  artifacts: []
  missing: []
  fix_needed: false
  resolved_by: "re-test confirmed fix (test 1 pass, 2026-10-07)"
  resolved_at: "2026-10-07"

- gap_id: G-03-3
  truth: "Every comparison file's actual attribute values are read and displayed; N/A appears only when a specific file genuinely lacks that attribute."
  status: failed
  reason: "User reported: I don't think that it is actually looking at more than 1 GDTF file as any other file I add just says NA not what the value is in the file."
  severity: major
  test: 2
  artifacts: []
  missing: []

## Previous Round (closed)

The first UAT round (2026-10-04, source: 03-VERIFICATION.md) reported one
issue (G-03-1, toolbar clipping) and one approved new-scope request (G-03-2,
match indicator). Both were closed by gap-closure plan 03-04, and the
crash/power-loss resilience judgment call passed outright. See git history
for the original round's full content (commit a0f3c34 and prior).
