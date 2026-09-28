# Requirements: GDTF Comparer

**Defined:** 2026-09-25
**Core Value:** You can pick a target GDTF file and any number of comparison files and immediately see which fixture attributes actually differ — without needing Python, dependencies, or command-line knowledge to run the tool.

## v1 Requirements

This milestone is a POC/proof-of-concept for the rebuilt comparer — everything below ships in one shot, with a v2 planned after user feedback. Each maps to a roadmap phase.

### Parsing

- [x] **PARSE-01**: App parses GDTF files using the `pygdtf` library instead of the current hand-rolled flat-attribute extraction, preserving element path/namespace so same-named attributes on different elements don't collide
- [ ] **PARSE-02**: App parses MVR files using the `pymvr` library

### Attribute Selection

- [ ] **ATTR-01**: User can browse/search the full set of GDTF attributes (60+ properties) for a fixture, not just the two hardcoded categories (Beam, Physical Properties)
- [ ] **ATTR-02**: User can select which attributes to include in a comparison via search/filter
- [ ] **ATTR-03**: User can save/name a subset of selected attributes as a reusable "compare profile" and reload it for future comparisons

### Comparison

- [ ] **DIFF-01**: The comparison table visually highlights which attribute values differ between the target and each comparison file

### Export

- [ ] **EXPORT-01**: User can export the full comparison table results to CSV
- [ ] **EXPORT-02**: User can export a diff-only CSV containing just the rows where values actually differ

### Interface

- [x] **UI-01**: App has a modernized, visually refreshed interface (not the stock Tkinter look)
- [ ] **UI-02**: App's GUI layer is decoupled from parsing/comparison logic (via a comparator/service layer), replacing the current tightly-coupled design

### Reliability

- [x] **RELI-01**: App shows a user-friendly error message (not a crash) when a selected file is not a valid GDTF/zip or contains malformed XML
- [x] **RELI-02**: App guards against oversized or malicious zip/XML input (zip bombs, XXE) using `defusedxml` and size limits

### Packaging

- [ ] **PKG-01**: User can download and run a standalone macOS build of the app with no separate Python install
- [ ] **PKG-02**: User can download and run a standalone Windows build of the app with no separate Python install
- [ ] **PKG-03**: Standalone builds are signed/notarized (macOS) or otherwise configured to avoid being blocked by Gatekeeper/SmartScreen on first launch

### MVR-xchange Networking

- [ ] **NET-01**: User can discover other MVR-xchange stations on the local network (LAN, mDNS-based discovery)
- [ ] **NET-02**: User can pull/receive an MVR file from a discovered MVR-xchange station and have its fixtures fed into the existing compare workflow
- [ ] **NET-03**: MVR-xchange networking is implemented from the public protocol spec (not ported from GPLv3 reference code) and remains fully optional — the app functions normally for file-based comparison with networking disabled/unavailable

## v2 Requirements

None planned yet — this milestone intentionally ships the full comparer feature set as a POC. v2 scope will be defined after user feedback on this release.

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

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PARSE-01 | Phase 1 | Complete |
| PARSE-02 | Phase 5 | Pending |
| ATTR-01 | Phase 2 | Pending |
| ATTR-02 | Phase 2 | Pending |
| ATTR-03 | Phase 3 | Pending |
| DIFF-01 | Phase 2 | Pending |
| EXPORT-01 | Phase 3 | Pending |
| EXPORT-02 | Phase 3 | Pending |
| UI-01 | Phase 1 | Complete |
| UI-02 | Phase 1 | Pending |
| RELI-01 | Phase 1 | Complete |
| RELI-02 | Phase 1 | Complete |
| PKG-01 | Phase 4 | Pending |
| PKG-02 | Phase 4 | Pending |
| PKG-03 | Phase 4 | Pending |
| NET-01 | Phase 5 | Pending |
| NET-02 | Phase 5 | Pending |
| NET-03 | Phase 5 | Pending |

**Coverage:**

- v1 requirements: 18 total
- Mapped to phases: 18 (Phase 1: 5, Phase 2: 3, Phase 3: 3, Phase 4: 3, Phase 5: 4)
- Unmapped: 0 ✓

---
*Requirements defined: 2026-09-25*
*Last updated: 2026-09-25 after roadmap creation*
