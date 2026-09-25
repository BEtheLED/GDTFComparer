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
- ✓ Parse `description.xml` out of a GDTF (zip) archive using `zipfile` + `xml.etree.ElementTree` — existing
- ✓ Display a side-by-side attribute comparison table (Tkinter `ttk.Treeview`) — existing
- ✓ Basic pytest coverage for `parse_gdtf()` parsing/error paths — existing

### Active

- [ ] User can run the app as a standalone package on macOS with no Python installed
- [ ] User can run the app as a standalone package on Windows with no Python installed
- [ ] App has a modernized UI (visual refresh, not just the stock Tkinter look)
- [ ] User can choose/search which GDTF attributes to compare, instead of being limited to the two hardcoded categories (Beam, Physical Properties)
- [ ] Differing attribute values are visually highlighted in the comparison table
- [ ] User can export comparison results (e.g. CSV) for sharing or records
- [ ] App parses GDTF files using MVRxchange's parsing logic/libraries instead of the current hand-rolled flat-attribute extraction
- [ ] App can participate in the MVRxchange network protocol to exchange/sync fixture and scene data with other lighting/visualization software
- [ ] Known crash bugs are fixed (missing `messagebox` import crashes error handling; no error handling around bad/corrupt GDTF files)

### Out of Scope

- Blender addon (`blender_addon/`, MVR/GDTF import into Blender) — parked; not part of this milestone, revisit separately
- Paid/commercial distribution — this stays a free community tool for now

## Context

- Existing codebase: a single-file Tkinter script (`BEtheLD`) plus a `parse_gdtf()` function, and an unrelated/parked Blender addon skeleton (`blender_addon/`). See `.planning/codebase/` for the full map (ARCHITECTURE.md, STACK.md, CONCERNS.md, etc.).
- Current parsing is naive: it walks the extracted XML tree and collects every element's attributes into one flat dict with no namespacing, so same-named attributes on different elements can collide. MVRxchange integration should replace this with more robust, spec-correct parsing.
- Current UI is GUI logic tightly coupled to parsing logic (`GDTFComparerApp.run_comparison()` calls `parse_gdtf()` directly and manipulates the Treeview inline) — the rebuild is an opportunity to separate parsing/comparison logic from presentation so a new UI can be layered on top.
- No dependency manifest exists today (no requirements.txt/pyproject.toml) — needed to add real dependencies (UI framework, MVRxchange libs, packaging tooling).
- Known bug: `run_comparison()` references `messagebox.showerror` but `messagebox` is never imported from `tkinter` — any validation error crashes the app instead of showing a message.

## Constraints

- **Tech stack**: Python-based today; open to swapping the GUI framework as part of the "better UI" work, but MVRxchange integration and standalone packaging need to work from whatever stack is chosen.
- **Distribution**: Must produce installable/runnable standalone builds for both macOS and Windows with no separate Python install required by the end user.
- **Compatibility**: Must continue to correctly read `.gdtf` (zip+XML) fixture files; MVRxchange integration must not break basic file-based comparison for users who aren't networked.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Rebuild UI and add MVRxchange parsing + network exchange in this milestone, rather than a smaller polish-only pass | User wants to "beef up" the tool significantly, not just reskin it | — Pending |
| Blender addon work stays parked | User wants focus on the standalone comparer app for this round | — Pending |
| Package as standalone macOS + Windows builds (no Python required) | Tool needs to be shareable with other lighting/AV pros who won't have Python set up | — Pending |

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
*Last updated: 2026-09-25 after initialization*
