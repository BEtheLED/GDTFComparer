---
status: complete
phase: 03-compare-profiles-export
source: [03-VERIFICATION.md]
started: 2026-10-05T12:05:00Z
updated: 2026-10-11T21:30:00Z
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

### 3. Re-test G-03-3 fix on the user's real fixture files in the live app
expected: |
  Re-run the exact comparison the user originally reported as broken: target
  Astera AF250 LeoFresnel vs. comparisons Prolights EclPendantTU_60 and Robe
  OnePATT (the user's own files from ~/Downloads). The Element column reads
  "Beam 1" for the first six rows, and every column now shows a real number
  instead of N/A -- Beam Angle 60 / 58.1 / 58, Field Angle 107 / 79.8 / 90,
  Power Consumption 250 / 200 / 40, Luminous Flux 7118 / 10981 / 240, Color
  Temperature 5500 / 3000 / 8000, Beam Type Wash / Wash / Wash. A second group
  of six "Beam 2" rows shows the Astera's values with N/A for the other two
  fixtures (genuinely correct -- the Astera has two light sources, the other
  two only have one). Physical Properties shows just one row, Weight (16.32 /
  7.3 / 12); the old lens/housing/pigtail width/height/length rows are gone.
  Both Compare-with dots are red.
result: pass

## Summary

total: 3
passed: 2
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
  status: resolved
  resolved_by: "03-05-PLAN.md"
  resolved_at: "2026-10-07"
  reason: "User reported: I don't think that it is actually looking at more than 1 GDTF file as any other file I add just says NA not what the value is in the file."
  severity: major
  test: 2
  root_cause: "Every file IS parsed correctly, but rows are matched across files by exact element name (the manufacturer's own internal geometry/model-part name inside each file's description.xml), per Phase 01 decision D-11. Two different fixtures almost never reuse the same internal names, so a row keyed to the target's 'Base 1 LED 1/1/1 Pixel 1' beam never matches a comparison file's 'Body/Beam' or 'One PATT/Patt beam' — the target cell shows its real value and every comparison column shows N/A on that row, while the comparison file's real value for the same logical attribute (e.g. BeamAngle) lands on a SEPARATE row further down the table where the target column is N/A. Reproduced directly against core.comparator.compare() with the user's three actual files (no GUI involved); confirmed not a parsing failure (all 3 files parsed with values), not a column-index bug (same-file-vs-itself comparison fills in correctly), and not the stale-window issue from G-03-1 (reproduced from current source). Existing tests never caught this because every test fixture reuses identical geometry/model names across target and comparison fixtures. This is also the reason the red match-indicator dots (G-03-2, phase 03 round 1) show 'different' for everything — every row looks like a total mismatch because the comparison side reads as N/A. This is a pre-existing design gap from Phase 01, not a phase 03 regression."
  artifacts:
    - path: "src/gdtf_comparer/core/extract.py"
      issue: "Lines ~413-415 key Beam attribute rows by each file's own geometry element path, and ~426-431 key model-dimension rows by each file's own model name — both become part of cross-file row identity even though these names are manufacturer-chosen and not comparable between different fixtures."
    - path: "src/gdtf_comparer/core/comparator.py"
      issue: "compare() (~L35-68) builds the row set from the union of exact (category, element_path, attribute) keys and does an exact dict lookup per file — there is no concept of matching rows across files by attribute meaning rather than by exact element name."
    - path: "src/gdtf_comparer/core/models.py"
      issue: "AttributeKey (~L47-72) includes element_path in equality/hash, which is correct for de-duplicating within one file (Phase 01 decision D-11) but is also what breaks cross-file matching."
    - path: "tests/core/test_comparator.py"
      issue: "Every cross-file test fixture reuses identical geometry/model element names for target and comparison fixtures, so this failure mode has no regression coverage."
  missing:
    - "Rework beam-level row matching (currently keyed by exact element_path) to match beams ACROSS files by POSITION: the target's 1st beam compares against each comparison file's 1st beam, 2nd vs 2nd, etc. (user decision, 2026-10-07). When one file has fewer beams than another, the missing side shows N/A for that beam index — that is a true per-file absence, not a matching failure."
    - "Drop per-model width/height/length rows (lens/housing/pigtail dimensions, keyed by mesh part name) from cross-file comparison entirely (user decision, 2026-10-07) — these have no meaningful counterpart between different manufacturers' fixtures. Scope this to the cross-file comparison table only; do not change how these are extracted/stored, only how(/whether) they're matched and shown across files."
    - "A regression test comparing two fixtures with different geometry/model names and different beam counts, including boundary cases (one beam vs two beams, zero beams vs one), asserting position-based matching lines up BeamAngle etc. on the same row and that dimension rows no longer appear in cross-file comparisons."
  debug_session: ".planning/debug/comparison-engine-only-reads-target-file.md"
  decision: "User decision (2026-10-07): beam-level attributes match by position across files (1st-to-1st, 2nd-to-2nd, ...); per-model physical-dimension rows are dropped from cross-file comparison entirely."
  status_update: "Fix implemented by gap-closure plan 03-05 (2026-10-08): core/comparator.py now matches Beam rows by position via a new _cross_file_attributes() helper and drops per-model dimension rows from cross-file comparison. Verified independently by 03-VERIFICATION.md (code read, 3 targeted tests + full 276-test suite re-run, scope-boundary git-diff gate on extract.py/models.py/repository.py/gui all exit 0). Human re-test (UAT test 3, 2026-10-11) confirmed in the live app against the user's own real fixture files: beam rows now populate real values across all three fixtures, dimension rows are gone, both Compare-with dots are red. Gap closed."

## Previous Round (closed)

The first UAT round (2026-10-04, source: 03-VERIFICATION.md) reported one
issue (G-03-1, toolbar clipping) and one approved new-scope request (G-03-2,
match indicator). Both were closed by gap-closure plan 03-04, and the
crash/power-loss resilience judgment call passed outright. See git history
for the original round's full content (commit a0f3c34 and prior).
