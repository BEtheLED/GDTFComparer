---
phase: 02
review: 02-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: open
    title: "A comparison result can be applied after the user has already changed the file selection, silently showing a stale comparison"
  - id: WR-01
    severity: warning
    disposition: open
    title: "Identical NaN values on both sides are reported as a difference"
  - id: WR-02
    severity: warning
    disposition: open
    title: "Two comparison files can render with identical, indistinguishable column headers"
  - id: IN-01
    severity: info
    disposition: open
    title: "`format_value` can fall back to scientific notation for large magnitudes"
open: 4
total: 4
recorded: 2026-10-12T02:36:10.520Z
---

# Phase 02: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | open | - |
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| IN-01 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
