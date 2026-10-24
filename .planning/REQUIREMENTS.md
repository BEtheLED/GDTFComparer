# Requirements: GDTF Comparer

**Defined:** 2026-09-25
**Core Value:** You can pick a target GDTF file and any number of comparison files and immediately see which fixture attributes actually differ — without needing Python, dependencies, or command-line knowledge to run the tool.

## v1 Requirements

This milestone is a POC/proof-of-concept for the rebuilt comparer — everything below ships in one shot, with a v2 planned after user feedback. Each maps to a roadmap phase.

### Parsing

- [x] **PARSE-01**: App parses GDTF files using the `pygdtf` library instead of the current hand-rolled flat-attribute extraction, preserving element path/namespace so same-named attributes on different elements don't collide
- [x] **PARSE-02**: App parses MVR files using the `pymvr` library

### Attribute Selection

- [x] **ATTR-01**: User can browse/search the full set of GDTF attributes (60+ properties) for a fixture, not just the two hardcoded categories (Beam, Physical Properties)
- [x] **ATTR-02**: User can select which attributes to include in a comparison via search/filter
- [x] **ATTR-03**: User can save/name a subset of selected attributes as a reusable "compare profile" and reload it for future comparisons

### Comparison

- [x] **DIFF-01**: The comparison table visually highlights which attribute values differ between the target and each comparison file

### Interface

- [x] **UI-01**: App has a modernized, visually refreshed interface (not the stock Tkinter look)
- [x] **UI-02**: App's GUI layer is decoupled from parsing/comparison logic (via a comparator/service layer), replacing the current tightly-coupled design

### Reliability

- [x] **RELI-01**: App shows a user-friendly error message (not a crash) when a selected file is not a valid GDTF/zip or contains malformed XML
- [x] **RELI-02**: App guards against oversized or malicious zip/XML input (zip bombs, XXE) using `defusedxml` and size limits

### Packaging

- [x] **PKG-01**: User can download and run a standalone macOS build of the app with no separate Python install
- [x] **PKG-02**: User can download and run a standalone Windows build of the app with no separate Python install
- [x] **PKG-03**: Standalone builds are signed/notarized (macOS) or otherwise configured to avoid being blocked by Gatekeeper/SmartScreen on first launch

### Fixture Substitution (Phase 5, redefined 2026-10-24 — see 05-CONTEXT.md)

- [x] **SUB-01**: User can import an MVR file (parsed via `pymvr`) and see one entry per unique GDTF fixture type it references, which becomes the fixture list for this workflow instead of browsing to GDTF files one at a time
- [x] **SUB-02**: For each fixture type, user can mark specific attributes as "important," each with a direction (higher/lower/closer-to-target is better — smart default, overridable per attribute) and its own tolerance
- [x] **SUB-03**: User can export one fixture's marked requirements to a separate shareable file (never embedded inside the MVR itself), and a different user in a different session can load that file back in
- [x] **SUB-04**: User can point the app at a local folder of candidate GDTF files and see each candidate scored against an imported fixture's requirements with a three-state per-attribute result (green = meets/exceeds, yellow = close, red = out of range), ranked best match first

## v2 Requirements

Deferred during the Phase 5 scope redefinition (2026-10-24) — may return as their own phase if there's demand:

- **Live LAN discovery** (formerly NET-01): discover other MVR-xchange stations on the local network via mDNS
- **Live MVR pull from a discovered station** (formerly NET-02): pull/receive an MVR file over the network rather than importing a local file
- **Protocol-implementation constraint** (formerly NET-03): if live networking returns, it must be implemented from the public MVR-xchange protocol spec, not ported from GPLv3 reference code, and must remain fully optional

## Out of Scope

Explicitly excluded from this project. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| 3D visualization / previz of fixtures and rigs | This is the core, multi-year product of Capture/Vectorworks Spotlight/Depence — building even a basic viewer massively out-scopes a comparison tool |
| GDTF/fixture authoring or editing (building new GDTF profiles) | Duplicates existing spec-validated tools (GDTF Builder, Fixture Builder) — a multi-month project on its own, off this tool's core value |
| Full bidirectional MVRxchange peer (broadcasting/hosting a group, pushing edited scenes back out) | This tool compares files, it doesn't author/edit scenes — a full read/write peer duplicates huge scope (session hosting, conflict resolution) owned by dedicated design platforms |
| Full DMX patching / show control | Safety/show-critical functionality owned by consoles and previz tools; wrong output has real production consequences and needs a live, stateful, console-synced UX this tool doesn't provide |
| MVRxchange internet/coordinator-server mode | Requires standing up/trusting a coordinator server plus auth/NAT-traversal complexity; local-network mode covers the stated collaboration use case (professionals on the same show network) |
| Raw XML diff as the primary comparison UX | Unreadable to the non-developer target audience; structured attribute-table diffing is the whole point of this tool |
| Blender addon (MVR/GDTF import into Blender) | Parked — separate milestone, not part of this rebuild |
| CSV export of comparison results (formerly EXPORT-01/EXPORT-02) | Dropped during Phase 3 discussion (2026-09-30) — user had no clear use case ("I don't even know why I would need to export") and chose to flag it for removal rather than build it speculatively |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PARSE-01 | Phase 1 | Complete |
| PARSE-02 | Phase 5 | Complete |
| ATTR-01 | Phase 2 | Complete |
| ATTR-02 | Phase 2 | Complete |
| ATTR-03 | Phase 3 | Complete |
| DIFF-01 | Phase 2 | Complete |
| UI-01 | Phase 1 | Complete |
| UI-02 | Phase 1 | Complete |
| RELI-01 | Phase 1 | Complete |
| RELI-02 | Phase 1 | Complete |
| PKG-01 | Phase 4 | Complete |
| PKG-02 | Phase 4 | Complete |
| PKG-03 | Phase 4 | Complete |
| SUB-01 | Phase 5 | Complete |
| SUB-02 | Phase 5 | Complete |
| SUB-03 | Phase 5 | Complete |
| SUB-04 | Phase 5 | Complete |

**Coverage:**

- v1 requirements: 17 total
- Mapped to phases: 17 (Phase 1: 5, Phase 2: 3, Phase 3: 1, Phase 4: 3, Phase 5: 5)
- Unmapped: 0 ✓

---
*Requirements defined: 2026-09-25*
*Last updated: 2026-10-24 — Phase 5 redefined from live LAN discovery (NET-01/02/03) to file-based MVR import + fixture substitution (SUB-01..04); NET-01/02/03 deferred to v2*
