# GDTF Comparer

## What This Is

A desktop application for lighting/AV professionals that compares GDTF (General Device Type Format) fixture files side-by-side, showing which attributes differ between a target fixture and one or more comparison fixtures. Originally prototyped with ChatGPT as a Tkinter script; this milestone rebuilds it into a polished, standalone application that runs without a Python install, for the creator and other lighting/AV professionals to use.

## Core Value

You can pick a target GDTF file and any number of comparison files and immediately see which fixture attributes actually differ — without needing Python, dependencies, or command-line knowledge to run the tool.

## Business Context

- **Customer**: Lighting and AV professionals working with GDTF/MVR fixture libraries (the creator, plus community/colleagues).
- **Revenue model**: None — free tool for personal and community use.
- **Success metric**: People other than the creator can download and run the packaged app without installing Python.

## Requirements

### Validated

- ✓ Select one target `.gdtf` file and multiple comparison `.gdtf` files via file dialogs — existing
- ✓ Display a side-by-side attribute comparison table — existing, rebuilt on a Qt `QTableView` in Phase 1
- ✓ App parses GDTF files using the `pygdtf` library (spec-correct, MIT-licensed), replacing the old hand-rolled flat-attribute extraction — Phase 1
- ✓ Known crash bugs fixed: typed errors (`defusedxml` + size-limit pre-validation) and friendly plain-text dialogs replace the old silent crashes on bad/corrupt GDTF files or the missing-`messagebox`-import bug — Phase 1
- ✓ App has a modernized UI (qt-material theme following OS light/dark) — Phase 1
- ✓ User can choose/search which GDTF attributes to compare, across the full 60+ GDTF attribute set grouped by feature, instead of being limited to two hardcoded categories — Phase 2
- ✓ Differing attribute values are visually highlighted in the comparison table (theme-aware tint, live re-tint on theme change, "Show differences only" toggle) — Phase 2
- ✓ User can save/name a subset of selected attributes as a reusable "compare profile" and reload it for future comparisons, with rename/delete management and a match-indicator dot per comparison file — Phase 3 (emerged as ATTR-03 during Phase 2/3 discussion, not in the original Active list below)

### Active

- [ ] User can run the app as a standalone package on macOS with no Python installed
- [ ] User can run the app as a standalone package on Windows with no Python installed
- [ ] User can export comparison results (e.g. CSV) for sharing or records
- [ ] App can participate in the MVR-xchange network protocol (reimplemented from the public spec, not ported from GPLv3 reference code) to exchange/sync fixture and scene data with other lighting/visualization software, as a later, additive phase after the core rebuild ships

### Out of Scope

- Blender addon (`blender_addon/`, MVR/GDTF import into Blender) — parked; not part of this milestone, revisit separately
- Paid/commercial distribution — this stays a free community tool for now

## Context

- Existing codebase: a single-file Tkinter script (`BEtheLD`) plus a `parse_gdtf()` function, and an unrelated/parked Blender addon skeleton (`blender_addon/`). See `.planning/codebase/` for the full map (ARCHITECTURE.md, STACK.md, CONCERNS.md, etc.).
- Current parsing is naive: it walks the extracted XML tree and collects every element's attributes into one flat dict with no namespacing, so same-named attributes on different elements can collide.
- Current UI is GUI logic tightly coupled to parsing logic (`GDTFComparerApp.run_comparison()` calls `parse_gdtf()` directly and manipulates the Treeview inline) — the rebuild is an opportunity to separate parsing/comparison logic from presentation so a new UI can be layered on top.
- No dependency manifest exists today (no requirements.txt/pyproject.toml) — needed to add real dependencies (UI framework, parsing libs, packaging tooling).
- Known bug: `run_comparison()` references `messagebox.showerror` but `messagebox` is never imported from `tkinter` — any validation error crashes the app instead of showing a message.
- **Research correction:** `github.com/mvrdevelopment/tools` (the repo originally referenced for "MVRxchange integration") contains no parsing library or network client — only schemas, GDTF-Share API docs, and a Wireshark dissector. The real GDTF/MVR parsing libraries are `pygdtf`/`pymvr` (open-stage org, MIT-licensed). The only known working MVR-xchange network protocol implementation is inside BlenderDMX (GPLv3) — this project will reimplement the wire protocol from the public spec rather than adopt GPLv3. See `.planning/research/SUMMARY.md` for full findings.

## Constraints

- **Tech stack**: Python-based today; open to swapping the GUI framework as part of the "better UI" work, but MVRxchange integration and standalone packaging need to work from whatever stack is chosen.
- **Distribution**: Must produce installable/runnable standalone builds for both macOS and Windows with no separate Python install required by the end user.
- **Compatibility**: Must continue to correctly read `.gdtf` (zip+XML) fixture files; MVRxchange integration must not break basic file-based comparison for users who aren't networked.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Rebuild UI and add spec-correct parsing + MVR-xchange network exchange in this milestone, rather than a smaller polish-only pass | User wants to "beef up" the tool significantly, not just reskin it | — Pending |
| Blender addon work stays parked | User wants focus on the standalone comparer app for this round | — Pending |
| Package as standalone macOS + Windows builds (no Python required) | Tool needs to be shareable with other lighting/AV pros who won't have Python set up | — Pending |
| Reimplement MVR-xchange wire protocol from the public spec, not from BlenderDMX's GPLv3 reference code | Keeps the project's license open; avoids the whole app inheriting GPLv3 | — Pending |
| Sequence MVR-xchange networking as its own later phase, after the core rebuild (parsing, UI, diff highlighting, export, packaging) ships | It's the highest-risk/complexity component; core app should be solid and offline-usable first | — Pending |
| Attribute profiles are a single atomic `profiles.json` file (not per-profile files), loading a profile *replaces* the current checked-attribute set rather than merging with it | Keeps one source of truth per user and matches the "load a saved subset" mental model (Phase 3 D-02/D-03/D-07) | ✓ Shipped — Phase 3 |
| Cross-file comparison rows match beams by position (1st-to-1st, 2nd-to-2nd, …) across files, not by each file's own manufacturer-chosen element name; per-model physical-dimension rows are dropped from cross-file comparison entirely | Different fixtures almost never reuse the same internal geometry names, so exact-name matching showed N/A for every other file's real values — a major bug the user caught in UAT (G-03-3) | ✓ Shipped — Phase 3 (gap-closure plan 03-05) |
| Added a green/red/gray match-indicator dot on each "Compare with" file (not in the original Phase 3 scope) | Approved as new scope during Phase 3 UAT once the user saw the toolbar layout fix and asked for an at-a-glance match signal (G-03-2) | ✓ Shipped — Phase 3 |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-10-11 after Phase 3*
