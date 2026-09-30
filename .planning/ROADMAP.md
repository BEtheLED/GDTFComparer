# Roadmap: GDTF Comparer

## Overview

GDTF Comparer rebuilds a crash-prone Tkinter prototype into a polished, standalone desktop tool for lighting/AV professionals. The milestone starts by replacing the hand-rolled parser and tightly-coupled GUI with a spec-correct (`pygdtf`), decoupled foundation wrapped in a modernized interface — a fully working, demoable comparer from day one. From there it layers on full attribute browsing with visual diff highlighting, reusable compare profiles and CSV export, then standalone macOS/Windows packaging so it runs with no Python install. MVR-xchange LAN networking — the highest-risk, highest-complexity piece — ships last, as an optional add-on once the core parsing/UI/comparison experience is stable and shippable on its own.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation Rebuild** - Spec-correct parsing, decoupled architecture, and a modernized GUI shell replace the old hand-rolled/crash-prone comparer (completed 2026-09-29)
- [ ] **Phase 2: Attribute Browsing & Diff Highlighting** - Users can browse/search the full GDTF attribute set and see differing values visually highlighted
- [ ] **Phase 3: Compare Profiles & Export** - Users can save reusable attribute selections and export comparison results to CSV
- [ ] **Phase 4: Standalone Packaging** - Users can download and run signed/notarized standalone builds on macOS and Windows with no Python install
- [ ] **Phase 5: MVR-xchange Networking** - Users can discover LAN peers and pull MVR fixture data into the compare workflow, fully optional

## Phase Details

### Phase 1: Foundation Rebuild

**Goal**: Users can run the rebuilt app, pick a target and comparison `.gdtf` files, and get a correct, crash-free comparison in a modernized interface — replacing the old hand-rolled parser and tightly-coupled GUI end to end.
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: PARSE-01, UI-01, UI-02, RELI-01, RELI-02
**Success Criteria** (what must be TRUE):

  1. User selects a target GDTF and one or more comparison GDTFs and sees a comparison table populate without the app crashing.
  2. Attributes with the same name from different GDTF sections (e.g. two elements both named "Name") no longer collide or overwrite each other in the results.
  3. Selecting a corrupt or invalid GDTF/zip file shows a friendly error message instead of crashing the app.
  4. The app's interface has a modernized, visually refreshed look, not the stock Tkinter appearance.
  5. The GUI layer no longer calls parsing/comparison logic directly — that logic lives in a separate, independently testable service layer.

**Plans**: 9/9 plans executed (5 original + 4 gap closure)

Plans:
**Wave 1**

- [x] 01-01-PLAN.md — Walking skeleton scaffold: blocking-human package legitimacy gate, pinned src-layout pyproject, shared venv, pytest-qt harness + GDTF test-file builder (wave 1)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md — Tracer: pick files -> QThread worker -> Qt-free core.compare_files -> pygdtf -> ComparisonResult -> QTableView, runnable via `python -m gdtf_comparer.app` (wave 2)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 01-03-PLAN.md — PARSE-01: per-GeometryBeam and per-Model attributes namespaced by element path, no collisions (wave 3)
- [x] 01-04-PLAN.md — RELI-01/RELI-02: defusedxml + size-limit pre-validation, typed errors, friendly plain-text dialogs (wave 3)
- [x] 01-05-PLAN.md — UI-01/UI-02: qt-material theme following OS light/dark, AST import-boundary guard, delete BEtheLD, README (wave 3)

**Gap closure** *(from 01-VERIFICATION.md Truth 6 and 01-REVIEW.md findings)*

**Wave 4**

- [x] 01-06-PLAN.md — PARSE-01 correctness (CR-01/Truth 6): omitted GDTF attributes show N/A instead of pygdtf's spec defaults, detected by presence in the validated description.xml; closes 01-03's open prohibition (wave 4)
- [x] 01-07-PLAN.md — WR-02/IN-01/IN-02: a file can never be compared against itself; kept public surface tested; README states the Python 3.11+ floor (wave 4)

**Wave 5** *(blocked on 01-06 and 01-07)*

- [x] 01-08-PLAN.md — WR-01: folders/pipes/devices rejected before any read; closing the window never hangs on a stuck worker (wave 5)

**Gap closure** *(from 01-UAT.md G-01-1 and G-01-2)*

**Wave 6** *(blocked on 01-08)*

- [x] 01-09-PLAN.md — G-01-1/G-01-2 (UI-01): results-table headers read in full in both themes via an uppercase header proxy; per-file headers show fixture names (file names when names collide); 280 px column cap with middle elision (wave 6)

**UI hint**: yes

### Phase 2: Attribute Browsing & Diff Highlighting

**Goal**: Users can browse and filter the complete set of GDTF attributes and see which values differ, instead of being limited to two hardcoded categories.
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: ATTR-01, ATTR-02, DIFF-01
**Success Criteria** (what must be TRUE):

  1. User can browse the full set of GDTF attributes (60+ properties) for a fixture, not just Beam and Physical Properties.
  2. User can search/filter the attribute list and choose which attributes are included in a comparison.
  3. Values that differ between the target and any comparison file are visually highlighted in the comparison results.

**Plans**: 3 plans

Plans:
**Wave 1**

- [ ] 02-01-PLAN.md — Tracer: category-agnostic compare() + always-visible Attributes side panel (collapsible category sections, per-attribute checkboxes, search narrows visibility only) filtering the table through an attribute-selection proxy; D-04 default = Beam + Physical Properties (ATTR-01, ATTR-02) (wave 1)

**Wave 2** *(blocked on 02-01)*

- [ ] 02-02-PLAN.md — Full 60+ attribute set: extract every GDTF AttributeDefinitions entry into "DMX: <feature group>" picker sections (unchecked by default) via one shared presence-check helper; DMX modes/channels out of scope (ATTR-01) (wave 2)

**Wave 3** *(blocked on 02-01 and 02-02)*

- [ ] 02-03-PLAN.md — DIFF-01: theme-aware tint on each differing comparison cell (delegate-painted, since qt-material suppresses BackgroundRole), live light/dark re-tint, and a "Show differences only" toggle proxy with an empty-result status message (wave 3)

### Phase 3: Compare Profiles & Export

**Goal**: Users can save reusable attribute selections and get comparison results out of the app for sharing or records.
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: ATTR-03, EXPORT-01, EXPORT-02
**Success Criteria** (what must be TRUE):

  1. User can save a named subset of selected attributes as a "compare profile" and reload it for a future comparison.
  2. User can export the full comparison table to CSV.
  3. User can export a diff-only CSV containing just the rows where values actually differ.

**Plans**: TBD

### Phase 4: Standalone Packaging

**Goal**: Users other than the creator can download and run the app on macOS or Windows without installing Python or fighting OS security warnings.
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: PKG-01, PKG-02, PKG-03
**Success Criteria** (what must be TRUE):

  1. A macOS user can download and run the packaged app with no separate Python install.
  2. A Windows user can download and run the packaged app with no separate Python install.
  3. The macOS build launches without a Gatekeeper "damaged app" block, and the Windows build launches without being flagged/blocked by SmartScreen on first run.

**Plans**: TBD

### Phase 5: MVR-xchange Networking

**Goal**: Users can pull live fixture data from other MVR-xchange stations on their local network directly into the same compare workflow, entirely optionally.
**Mode:** mvp
**Depends on**: Phase 4
**Requirements**: PARSE-02, NET-01, NET-02, NET-03
**Success Criteria** (what must be TRUE):

  1. User can see other MVR-xchange stations discovered on the local network (mDNS) inside the app.
  2. User can pull/receive an MVR file from a discovered station, parsed via `pymvr`, and have its fixtures appear in the existing compare workflow.
  3. With networking disabled or unavailable, the app still works normally for file-based GDTF comparison.
  4. The MVR-xchange protocol handling is implemented from the public spec, not ported from GPLv3 reference code.

**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation Rebuild | 9/9 | Complete    | 2026-09-29 |
| 2. Attribute Browsing & Diff Highlighting | 0/3 | Planned | - |
| 3. Compare Profiles & Export | 0/TBD | Not started | - |
| 4. Standalone Packaging | 0/TBD | Not started | - |
| 5. MVR-xchange Networking | 0/TBD | Not started | - |
