# Roadmap: GDTF Comparer

## Overview

GDTF Comparer rebuilds a crash-prone Tkinter prototype into a polished, standalone desktop tool for lighting/AV professionals. The milestone starts by replacing the hand-rolled parser and tightly-coupled GUI with a spec-correct (`pygdtf`), decoupled foundation wrapped in a modernized interface — a fully working, demoable comparer from day one. From there it layers on full attribute browsing with visual diff highlighting, reusable compare profiles and CSV export, then standalone macOS/Windows packaging so it runs with no Python install. MVR-xchange LAN networking — the highest-risk, highest-complexity piece — ships last, as an optional add-on once the core parsing/UI/comparison experience is stable and shippable on its own.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation Rebuild** - Spec-correct parsing, decoupled architecture, and a modernized GUI shell replace the old hand-rolled/crash-prone comparer (completed 2026-09-29)
- [x] **Phase 2: Attribute Browsing & Diff Highlighting** - Users can browse/search the full GDTF attribute set and see differing values visually highlighted (completed 2026-10-14)
- [x] **Phase 3: Compare Profiles** - Users can save and reload reusable attribute selections ("compare profiles") for future comparisons (completed 2026-10-11)
- [ ] **Phase 4: Standalone Packaging** - Users can download and run signed/notarized standalone builds on macOS and Windows with no Python install
- [ ] **Phase 5: MVR Import & Fixture Substitution** - Users can import an MVR show file, mark which attributes matter per fixture, and find substitute fixtures from a local inventory folder that meet those requirements

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

**Plans**: 3/3 plans complete

Plans:
**Wave 1**

- [x] 02-01-PLAN.md — Tracer: category-agnostic compare() + always-visible Attributes side panel (collapsible category sections, per-attribute checkboxes, search narrows visibility only) filtering the table through an attribute-selection proxy; D-04 default = Beam + Physical Properties (ATTR-01, ATTR-02) (wave 1)

**Wave 2** *(blocked on 02-01)*

- [x] 02-02-PLAN.md — Full 60+ attribute set: extract every GDTF AttributeDefinitions entry into "DMX: <feature group>" picker sections (unchecked by default) via one shared presence-check helper; DMX modes/channels out of scope (ATTR-01) (wave 2)

**Wave 3** *(blocked on 02-01 and 02-02)*

- [x] 02-03-PLAN.md — DIFF-01: theme-aware tint on each differing comparison cell (delegate-painted, since qt-material suppresses BackgroundRole), live light/dark re-tint, and a "Show differences only" toggle proxy with an empty-result status message (wave 3)

### Phase 3: Compare Profiles

**Goal**: Users can save and reload reusable attribute selections ("compare profiles") for future comparisons.
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: ATTR-03
**Success Criteria** (what must be TRUE):

  1. User can save a named subset of selected attributes as a "compare profile" and reload it for a future comparison.

**Plans**: 5/5 plans complete (3 original + 2 gap closure)

Plans:
**Wave 1**

- [x] 03-01-PLAN.md — Tracer: Save… the checked attributes as a named profile into one atomic, Qt-free profiles.json (core/profile_repository.py), reopen the app, pick it from the Profiles dropdown in the Attributes panel, and it replaces the checked set (D-02, D-03, D-07); D-04 overwrite confirm, name rules, damaged-file / failed-write safety (wave 1)

**Wave 2** *(blocked on 03-01)*

- [x] 03-02-PLAN.md — D-06: a loaded profile's spec items that no current file has are named in the status bar ("N of M spec items … weren't found in these files: …"), re-checked after every re-run, honest before a comparison, with "Show differences only" and for empty profiles (wave 2)

**Wave 3** *(blocked on 03-02)*

- [x] 03-03-PLAN.md — D-05: Manage menu in the same row (D-07) with Rename… (conflicts refused) and Delete… (asks first, default No); selection and comparison never touched; end-of-phase human check (wave 3)

**Scope note (2026-10-04):** CSV export (formerly EXPORT-01/EXPORT-02) was dropped from this phase per the Phase 3 discussion scope flag — see REQUIREMENTS.md "Out of Scope".

**Gap closure** *(from 03-UAT.md G-03-1 and G-03-2)*

**Wave 4** *(blocked on 03-03)*

- [x] 03-04-PLAN.md — G-03-1/G-03-2: two-row profile toolbar so the dropdown, Save… and Manage never clip in the 260 px Attributes panel, plus a green/red/gray match-indicator dot on each "Compare with" file reusing ComparisonRow.differs (wave 4)

**Gap closure** *(from 03-UAT.md G-03-3)*

**Wave 5** *(blocked on 03-04)*

- [x] 03-05-PLAN.md — G-03-3: comparison files' real values line up with the target's rows — beams matched across files by position ("Beam 1", "Beam 2", …), per-model width/height/length rows dropped from the cross-file comparison (both per the user's 2026-10-07 decisions); regression tests with differently named fixtures and unequal beam counts (wave 5)

### Phase 4: Standalone Packaging

**Goal**: Users other than the creator can download and run the app on macOS or Windows without installing Python or fighting OS security warnings.
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: PKG-01, PKG-02, PKG-03
**Success Criteria** (what must be TRUE):

  1. A macOS user can download and run the packaged app with no separate Python install.
  2. A Windows user can download and run the packaged app with no separate Python install.
  3. The macOS build launches without a Gatekeeper "damaged app" block, and the Windows build launches without being flagged/blocked by SmartScreen on first run.

**Plans**: 2/4 plans executed

Plans:
**Wave 1**

- [x] 04-01-PLAN.md — Tracer: blocking-human legitimacy gate for pyinstaller==6.22.3, then one shared packaging/app.spec builds a standalone macOS GDTF Comparer.app on this Mac, and packaging/smoke_check.py proves it launches, themes itself and stays up with no Python environment (valid ad-hoc signature, qt-material bundled by its own hook); negative-path tests prove the check isn't vacuous (PKG-01, PKG-02) (wave 1)
- [x] 04-03-PLAN.md — First-launch instructions: README "Download and run (no Python needed)" plus packaging/release-notes.md (the release description) with the current macOS Privacy & Security → Open Anyway flow, the "is damaged" fallback, Windows Extract All → More info → Run anyway, the unsigned explanation and the official-Releases-page scope; tests/test_release_docs.py keeps both correct and safe (PKG-03, D-01) (wave 1)

**Wave 2** *(blocked on 04-01)*

- [ ] 04-02-PLAN.md — HALTED: Task 1's blocking-human "publish?" decision was answered "hold" (2026-10-14). No .github/workflows/release.yml was created, nothing was pushed to GitHub, no CI build ran. Tasks 2-3 (build-macos/build-windows jobs, zip and smoke-check, tag-only version-guarded release job) do not exist yet. See 04-02-SUMMARY.md (status: halted). Resume by re-running this plan once the user answers "publish" (PKG-01, PKG-02, D-02/D-03/D-04) (wave 2)

**Wave 3** *(blocked on 04-02 and 04-03 — BLOCKED: 04-02 is halted, so 04-04 cannot proceed until the user answers "publish")*

- [ ] 04-04-PLAN.md — Write packaging/RELEASING.md and follow it to publish GitHub Release v0.1.0 with GDTF-Comparer-macos.zip and GDTF-Comparer-windows.zip; fetch the published files back and check them; end-of-phase human checks walk the documented first launch on a real Mac and a real Windows PC (PKG-01, PKG-02, PKG-03) (wave 3)

### Phase 5: MVR Import & Fixture Substitution

**Scope redefined 2026-10-24** (see `05-CONTEXT.md`): this phase originally covered live LAN discovery between MVR-xchange stations (NET-01/02/03). That framing is deferred — see REQUIREMENTS.md v2. The phase now covers file-based MVR import and a two-role fixture-substitution workflow (an LD sets per-fixture requirements; a shop matches their own inventory against them).

**Goal**: A lighting designer can import an MVR show file, mark which attributes matter most for each fixture type, and share those requirements so anyone — including a rental shop checking their own inventory — can find substitute fixtures that meet them.
**Mode:** mvp
**Depends on**: Phase 4
**Requirements**: PARSE-02, SUB-01, SUB-02, SUB-03, SUB-04
**Success Criteria** (what must be TRUE):

  1. User can import an MVR file (parsed via `pymvr`) and see one entry per unique GDTF fixture type it references — not one entry per physical fixture instance — which becomes the fixture list for this workflow instead of manually browsing to files one at a time.
  2. For each fixture type, user can mark specific attributes as "important," each with a higher/lower/closer-to-target direction (smart default per attribute, overridable) and its own tolerance (not one global tolerance for everything).
  3. User can export one fixture's marked requirements to a separate shareable file (never embedded inside the MVR itself) and a different user, in a different session, can load that file back in.
  4. User can point the app at a local folder of candidate GDTF files they maintain and see each candidate scored against an imported fixture's requirements with a three-state per-attribute result (green = meets/exceeds, yellow = close, red = out of range), with candidates ranked best match first.

**Plans**: 1/5 plans executed

Plans:
**Wave 1**

- [x] 05-01-PLAN.md — Tracer: blocking-human legitimacy gate for pymvr==1.0.7, then a blocking-human decision on what the shared requirements file records and how one tolerance becomes green/yellow/red (D-08 one-way, D-10), then the thin LD-to-shop round trip: hardened MVR import (generalized core/hardening.py, pymvr on validated in-memory bytes, embedded GDTFs through the existing pipeline) → one fixture-type row → mark one attribute → save a one-fixture sidecar file → a fresh Find Substitutes window opens it, scans an inventory folder and ranks green/yellow/red through BackgroundBrushDelegate (PARSE-02, SUB-01..04) (wave 1)

**Wave 2** *(blocked on 05-01; the three plans share no files)*

- [ ] 05-02-PLAN.md — MVR import depth: fixtures found wherever the scene nests them, accented GDTF names (cp437 recovery), missing/broken embedded GDTFs named, empty-state messages, every hostile or wrong file ends in one friendly message, one import at a time, clean shutdown with a stuck worker (PARSE-02, SUB-01) (wave 2)
- [ ] 05-03-PLAN.md — Requirements editor depth: each fixture type keeps its own checklist (D-04), smart overridable directions (D-05), per-attribute tolerances with units (D-06), text attributes "Must match", declared-only rows, search, nothing-marked allowed (SUB-02) (wave 2)
- [ ] 05-04-PLAN.md — Requirements file trust boundary: identical round trip in a separate process, exactly one fixture per file (D-09), strict refuse-never-coerce validation, safe read, atomic writes (SUB-03) (wave 2)

**Wave 3** *(blocked on 05-02 and 05-03)*

- [ ] 05-05-PLAN.md — Inventory check depth: single-folder read-only scan, duplicates kept, unreadable files listed, empty states, scoring pinned to the user's chosen rule at every edge, lights-only fair ranking, colors visible in both themes with words and a legend, one check at a time (SUB-04) (wave 3)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation Rebuild | 9/9 | Complete    | 2026-09-29 |
| 2. Attribute Browsing & Diff Highlighting | 3/3 | Complete    | 2026-10-14 |
| 3. Compare Profiles & Export | 5/5 | Complete    | 2026-10-11 |
| 4. Standalone Packaging | 2/4 | In Progress | - |
| 5. MVR Import & Fixture Substitution | 1/5 | In Progress | - |
