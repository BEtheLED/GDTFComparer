---
gsd_state_version: "1.0"
milestone: v0.1.0
current_phase: 04
current_phase_name: Standalone Packaging
status: executing
stopped_at: "Halted 04-02-PLAN.md: user answered Task 1 publish decision with 'hold'. No push, no workflow file."
last_updated: "2026-10-15T00:31:23.617Z"
last_activity: 2026-10-14
last_activity_desc: Phase 04 execution started
state_head: 4b6442ca1de48f34868908c7cf8b58ad9a10cfb1
progress:
  total_phases: 5
  completed_phases: 3
  total_plans: 21
  completed_plans: 20
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-11)

**Core value:** You can pick a target GDTF file and any number of comparison files and immediately see which fixture attributes actually differ — without needing Python, dependencies, or command-line knowledge to run the tool.
**Current focus:** Phase 04 — Standalone Packaging

## Current Position

Phase: 04 (Standalone Packaging) — EXECUTING
Plan: 4 of 4 (04-02 HALTED — awaiting user's "publish" decision; 04-04 blocked on it)
Status: Halted at Task 1's blocking-human decision (user answered "hold")
Last activity: 2026-10-14 — Plan 04-02 halted by user's "hold" answer

Progress: [██████░░░░] 60%

## Performance Metrics

**Velocity:**

- Total plans completed: 17
- Average duration: - min
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 9 | - | - |
| 03 | 5 | - | - |
| 02 | 3 | - | - |

**Recent Trend:**

- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 02 P01 | 14 | 2 tasks | 8 files |
| Phase 02 P02 | ~15min | 2 tasks | 5 files |
| Phase 02 P03 | 15min | 3 tasks | 5 files |
| Phase 03 P05 | 6m | 2 tasks | 7 files |
| Phase 04 P01 | 47min | 3 tasks | 4 files |
| Phase 04 P03 | 5min | 2 tasks | 3 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Milestone: Rebuild UI + spec-correct parsing (`pygdtf`/`pymvr`) + MVR-xchange networking in one milestone, not a polish-only pass.
- Milestone: MVR-xchange wire protocol reimplemented from the public spec, not ported from BlenderDMX's GPLv3 reference code.
- Roadmap: MVR-xchange networking (Phase 5) sequenced last, after core parsing/UI/comparison work (Phases 1-3) and packaging (Phase 4) are stable — explicit user decision during research review.
- [Phase 02]: Split DISPLAY_CATEGORIES into LEADING_CATEGORIES (compare() row-order anchor) and DEFAULT_SELECTED_CATEGORIES (picker's D-04 first-use seed) so they can never silently drift together
- [Phase 02]: Attribute selection state lives entirely in the GUI layer (AttributePicker); core.comparator.compare() stays a pure, selection-unaware function
- [Phase 02]: [Phase 02] DMX attribute definitions become one (category, attribute) picker entry each: category is 'DMX: ' + the Feature link's group, attribute is the definition's Name, with a fixed collision-proof prefix so a file-supplied name can never land in or default-check the legacy Beam/Physical Properties categories
- [Phase 02]: [Phase 02] Beam and Model attribute extraction were converted to route through the same shared presence-check helper (_declared_values) as the new DMX attribute-definition extraction, removing a hand-written per-category presence loop
- [Phase 02]: [Phase 02]: Confirmed by measurement that qt-material's QTableView::item stylesheet rule suppresses BackgroundRole painting -- a dedicated BackgroundBrushDelegate is required for DIFF-01's highlight to be visible on screen, not just present in model data
- [Phase 02]: [Phase 02]: ComparisonTableModel stays theme-agnostic (no gui.theme or QApplication import); MainWindow is the sole place that resolves a theme name to a color and hands the model a ready QBrush, recomputed once per theme change and cached, never per painted cell
- [Phase 03 gap G-03-3]: Cross-file beam-attribute rows match by POSITION (1st beam vs 1st beam, 2nd vs 2nd, ...) rather than by each file's own internal element name — user decision 2026-10-07, after diagnosis found exact-name matching (Phase 01 D-11) means different manufacturers' fixtures almost never line up, showing N/A everywhere instead of real comparison values.
- [Phase 03 gap G-03-3]: Per-model physical-dimension rows (lens/housing/pigtail width/height/length) are dropped from cross-file comparison entirely — user decision 2026-10-07; these mesh part names have no meaningful counterpart between different fixtures.
- [Phase 02]: UAT test 2 (real third-party .gdtf DMX check, 02-02 coverage D5) descoped 2026-10-14 by user decision - no real third-party .gdtf fixture file available for testing in this environment. It is recorded as a deferred follow-up in 02-UAT.md, and ATTR-01's 60+ evidence remains the automated synthetic 66-definition suite.
- [Phase 04]: [Phase 04] PyInstaller 6.22.3 and helper packages approved at blocking-human legitimacy checkpoint before install
- [Phase 04]: [Phase 04] Local macOS builds on this machine need DEVELOPER_DIR=/Library/Developer/CommandLineTools (Xcode 16.0 vs macOS 26.6.2 mismatch breaks lipo); env-var-only workaround, not expected to recur in CI
- [Phase 04]: [Phase 04] qt-material's own PyInstaller hook supplies all theme/icon data; packaging/app.spec datas stays empty
- [Phase 04]: [Phase 04]: Corrected D-01's bypass wording per RESEARCH Pitfall P1 — macOS right-click->Open is removed since Sequoia; shipped README/release-notes steps use System Settings > Privacy & Security > Open Anyway plus a scoped xattr -cr fallback
- [Phase 04]: [Phase 04]: packaging/release-notes.md keeps a releases/latest link even on the release page itself, so one shared pytest suite can enforce every first-launch step identically across README.md and release-notes.md with no doc-specific exemptions
- [Phase 04]: Plan 04-02 Task 1 publish decision answered: hold. No file created, nothing pushed to GitHub; plan halted (status: halted) until user later says publish.

### Pending Todos

- [2026-10-07] [general] Add min/max output-percentage filter for comparisons — [todo file](.planning/todos/pending/2026-10-07-add-min-max-output-percentage-filter-for-comparisons.md)

### Blockers/Concerns

- Phase 5 (MVR-xchange Networking): wire-protocol specifics (message framing, mDNS service-type string, port numbers) are only MEDIUM/LOW confidence per research — recommend `/gsd-plan-phase --research-phase 5` to re-verify against `mvrdevelopment/spec` before implementation.
- Phase 4 (Standalone Packaging): RESOLVED 2026-10-14 — user decided to ship both macOS and Windows builds unsigned (no Apple Developer account, no code-signing cert) with bypass instructions, per 04-CONTEXT.md D-01.
- Phase 04 Plan 04-02 is halted (user chose 'hold' on the Task 1 publish decision). No .github/workflows/release.yml exists, nothing was pushed. Plan 04-04 (publish GitHub Release v0.1.0) is blocked until the user resumes 04-02 and answers 'publish'.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 261014-a1i | Formally descope the Phase 02 UAT requirement that a real third-party manufacturer .gdtf file be used to verify the Attributes panel DMX section | 2026-10-14 | d9bcb4e | [261014-a1i-formally-descope-the-phase-02-uat-requir](./quick/261014-a1i-formally-descope-the-phase-02-uat-requir/) |

## Deferred Items

Items acknowledged and deferred at milestone close, most recent first:

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| *(none)* | | | | |

## Session Continuity

Last session: 2026-10-15T00:31:23.578Z
Stopped at: Halted 04-02-PLAN.md: user answered Task 1 publish decision with 'hold'. No push, no workflow file.
Resume file: None

Last activity: 2026-10-14 - Completed quick task 261014-a1i: Formally descope the Phase 02 UAT requirement that a real third-party manufacturer .gdtf file be used to verify the Attributes panel DMX section
