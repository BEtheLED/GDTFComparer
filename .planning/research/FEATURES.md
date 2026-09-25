# Feature Research

**Domain:** GDTF/MVR fixture comparison tool (desktop, lighting/AV professionals)
**Researched:** 2026-09-25
**Confidence:** MEDIUM (web search only, no paid research providers configured; several claims cross-verified across 2+ independent sources — see Sources)

## Feature Landscape

The GDTF/MVR tooling ecosystem splits into three tiers this project should position itself against:

1. **Full lighting design/control platforms** (Vectorworks Spotlight, grandMA3, Capture, Depence) — patch, 3D previz, DMX control. Massive scope; not the comparison target.
2. **Browser-based GDTF/MVR utility suites** (GDTF Bench Online, MVR Artist Online at gdtf-share.com) — 3D Viewer, Overview, **Differ**, GDTF updater, Patch viewer, Power Planner, Benchmark. This is the closest sibling to this project's core value: a focused, multi-tool "workbench" around GDTF/MVR files rather than a full design suite. Notably, "Differ" (raw XML diff) is already a first-class, named feature in this ecosystem — validating that comparison/diffing is an expected, discrete capability, not a nice-to-have bolted onto a viewer.
3. **Open-source parsing/interop layer** (open-stage's pygdtf, pymvr, BlenderDMX) — libraries and a reference client, not end-user comparison tools themselves.

This project's positioning: a focused, standalone, offline-first **comparison** tool — narrower than GDTF Bench (single browser-based multi-tool suite) but packaged as a native app, and eventually networked via MVRxchange rather than purely file-based.

### Table Stakes (Users Expect These)

Features users assume exist in any modern GDTF/MVR-adjacent desktop tool. Missing these makes the tool feel like a hobby script, not a professional tool.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Native standalone app, no runtime install | Lighting/AV pros are not developers; existing competing tools (Vectorworks, grandMA3, Capture, GDTF Bench) are all install-and-run or browser-based, never "install Python first" | MEDIUM | Already an active requirement (PyInstaller/Briefcase/Tauri-class packaging — covered by STACK research, not here) |
| Multi-select comparison (1 target vs N others) | Already validated in the existing prototype; standard for any "compare" tool | LOW | Keep and polish, don't regress |
| Full attribute/property coverage, not a curated subset | GDTF Bench Online advertises comparing on "more than 60 utilized GDTF properties" — professionals expect to inspect *any* attribute, not just 2 hardcoded categories (Beam, Physical) | MEDIUM | Directly matches the active requirement to replace hardcoded categories with searchable selection |
| Search/filter within attribute list | With 60+ possible properties across geometry, DMX channels, wheels, physical, etc., an unfiltered flat list is unusable | LOW-MEDIUM | Simple text filter over attribute names/paths is sufficient for v1; category grouping is a nice add, not required |
| Visual highlighting of differences | The dedicated "Differ" tool in GDTF Bench proves this is a named, expected capability in this niche, not just generic table styling | LOW-MEDIUM | Table-cell color coding (changed/same) is the standard pattern; see Architecture notes below |
| Handle malformed/corrupt files gracefully | Current app crashes on bad files (missing `messagebox` import, no error handling) — this is a known bug, and any pro tool that crashes on a bad zip/XML loses trust immediately | LOW | Already an active requirement; table-stakes bar, not a differentiator |
| Export results (CSV at minimum) | Every comparable "compare/diff" utility (spreadsheet diff tools, MVR Differ, GDTF Bench) assumes results leave the tool — for reports, emails, spec sheets | LOW-MEDIUM | CSV is the universal baseline; don't over-engineer export formats for v1 |
| Correct GDTF parsing (namespaced, spec-aware) | Current hand-rolled parser flattens all XML attributes into one dict with name collisions across elements — this produces silently wrong comparisons, the worst failure mode for a comparison tool | MEDIUM-HIGH | Motivates replacing the naive parser with a spec-correct library (pygdtf, not literally "MVRxchange's" parsing — see Pitfall note below) |
| Modern, clean visual UI | Current app is stock Tkinter; every competing tool in this space (Vectorworks, GDTF Bench web UI, Capture) has a considered, professional visual layer | MEDIUM | "Modernized UI" is explicitly requested; covered by dedicated UI research/phase, not detailed here |

### Differentiators (Competitive Advantage)

Features that set this tool apart from both the naive prototype and from the broader (heavier) ecosystem tools.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Standalone native packaging for both macOS AND Windows with zero dependencies | The closest sibling (GDTF Bench Online) is browser-based; grandMA3/Vectorworks/Capture are large paid platforms. A free, lightweight, native, double-click comparison tool fills a real gap | MEDIUM-HIGH | This is the single most distinctive claim: "the small free tool that just compares fixtures, no install, no browser, no console license" |
| MVRxchange live network participation (receive fixture/scene updates from other running MVRxchange-capable software on the LAN) | Lets a user compare against what's *live* in another tool's session (e.g., what a colleague's Vectorworks or BlenderDMX session currently has patched) instead of only pre-exported files | HIGH | Real differentiator vs. every file-based-only GDTF compare tool; but scope carefully — "join a group and receive/pull an MVR" is very different from becoming a full bidirectional MVRxchange peer (see Anti-Features) |
| Configurable/saved attribute selection sets ("compare profiles") | Power users doing repeated comparisons (e.g., always checking DMX footprint + beam angle + weight) benefit from saving a named subset instead of re-searching every time | LOW-MEDIUM | Natural extension of the "searchable attribute selection" table-stakes feature; genuinely differentiates from GDTF Bench's one-shot Differ | 
| Multi-way (not just target-vs-one) diff highlighting across many comparison fixtures at once | Existing prototype already does 1-target-vs-N; polishing this into a clean visual (not just a flat table) is more usable than most competitors, which are typically pairwise (A vs B) diff-only | MEDIUM | GDTF Bench's Differ is pairwise XML diff; a clean N-way attribute matrix is a genuine UX improvement over that |
| Attribute-level diff export (CSV showing only differing rows, or all rows with a diff column) | Turns the tool into a shareable "spec deviation report" for a team, not just an on-screen aid | LOW | Cheap add-on once CSV export + diff highlighting both exist |

### Anti-Features (Commonly Requested, Often Problematic)

Features that sound good given the MVRxchange integration ask, but would blow up scope or duplicate what full platforms already do far better.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|------------------|-------------|
| Full bidirectional MVRxchange peer (broadcasting/hosting a group, editing and pushing scenes back out to other stations) | "Integration with MVRxchange" in the requirement could be read as "become a full participant like grandMA3/Vectorworks/BlenderDMX" | This tool doesn't edit or author scenes — it compares files. A full read/write MVRxchange peer duplicates huge scope (scene editing, conflict resolution, session hosting) that exists in dedicated design tools, for a feature that doesn't serve the comparison use case | Implement MVRxchange as a **receive-only client**: join a group, list available stations/MVR versions, pull one to feed into the existing compare workflow. That satisfies "sync fixture/scene data with other software" without building a scene editor |
| 3D visualization / previz of fixtures and rigs | Natural adjacent feature once MVR (which carries 3D position data) is being parsed | This is the core value proposition of Capture, Vectorworks Spotlight, Depence, and grandMA3 3D — multi-year efforts. Building even a basic 3D viewer massively out-scopes a comparison tool and won't compete on quality | Stay 2D/tabular. If 3D context is ever wanted, treat the MVR/GDTF file as an *input* the user opens in an existing viewer (GDTF Bench Online, BlenderDMX) alongside this tool |
| Full DMX patching / show control | MVR files contain DMX address/patch data, so "why not let me patch from here" is a plausible ask | Patch management is safety/show-critical functionality owned by consoles (grandMA3, etc.) and previz tools; getting it wrong has real production consequences, and it's a completely different UX (live, stateful, console-synced) | Read patch data for display/comparison only; never write/re-patch from this tool |
| GDTF/fixture authoring or editing (building new GDTF profiles) | Once you're parsing GDTF deeply, "let me fix a wrong value and re-export" feels like a small step | GDTF Builder / Fixture Builder (gdtf-build.com, fixturebuilder.gdtf-share.com) already exist, are spec-validated, and are non-trivial (3D model editing, DMX mode builder, LED spectral data). Duplicating this is a multi-month project on its own and off the stated core value | If a user finds a fixture error, point them to the existing GDTF Share / Fixture Builder tools, or at most support export of the current parsed data as a starting point |
| Raw XML diff view as the primary comparison UX | GDTF Bench's "Differ" does raw XML diffing, so it's a tempting shortcut to reuse | Raw XML diff is unreadable to non-developers (the exact audience here) and defeats the purpose of "configurable/searchable attribute selection" — it shows structural noise, not meaningful attribute-level differences | Keep the primary UX as structured attribute-table diffing; an XML/raw view can be an optional secondary/debug panel at most, not the headline feature |
| "Live" always-on internet-wide MVRxchange (via the wss:// coordinating-server mode) as a v1 requirement | The protocol supports both local-network mode and an internet mode via a coordinating server | Internet mode requires standing up or trusting a coordinator server, adds auth/security/NAT-traversal complexity, and isn't needed to satisfy "sync with other lighting/visualization software" for the stated use case (professionals working together, typically on the same show network) | Implement local-network MVRxchange (mDNS discovery on LAN) first; treat internet/coordinator mode as a clearly separate future phase, not bundled into this milestone |

## Feature Dependencies

```
Correct GDTF/MVR parsing (spec-aware library, e.g. pygdtf/pymvr)
    └──requires──> [replaces current naive parser]
    └──enables───> Full attribute/property coverage (60+ properties)
                       └──enables──> Searchable/configurable attribute selection
                                         └──enables──> Saved compare profiles (differentiator)
                       └──enables──> Visual diff highlighting (needs a stable, typed attribute
                                      model to diff against, not an unnamespaced flat dict)
                                         └──enables──> CSV export of diff results

MVRxchange network participation (receive-only client)
    └──requires──> MVR parsing (pymvr-equivalent) [shares the "correct parsing" dependency above]
    └──requires──> mDNS/local network discovery + TCP or WebSocket client
    └──feeds-into──> existing compare workflow (a pulled MVR's fixtures become "comparison files"
                       exactly like locally opened ones — do not build a second, parallel UI)

Standalone packaging (macOS + Windows) ──constrains──> UI framework and parsing library choice
    (must be choices that package cleanly with PyInstaller/similar; this affects STACK, not
     FEATURES, but the dependency runs through here: features above must work fully offline/
     packaged, so any parsing library dependency needs to bundle cleanly)

Modernized UI ──enhances──> Visual diff highlighting, Searchable attribute selection
    (a redesigned UI is what makes color-coded diffing and a filterable attribute list usable;
     bolting these onto the existing stock Tkinter Treeview would work but look/feel dated)
```

### Dependency Notes

- **Correct parsing requires replacing the current naive parser:** The existing `parse_gdtf()` flattens all XML element attributes into one unnamespaced dict, so same-named attributes on different elements collide. Full attribute coverage and reliable diffing both depend on parsing that preserves structure (element path / namespace), which the current approach cannot support without a rewrite.
- **MVRxchange networking shares its parsing dependency with the core comparison feature:** Both need spec-correct MVR/GDTF parsing. Do this once, well, and both the "networked" and "file-based" paths consume the same internal fixture model — don't build separate parsing paths for local files vs. network-received files.
- **MVRxchange should feed the existing compare workflow, not create a parallel one:** A fixture/scene received over the network should just become another "comparison file" in the same UI a locally-opened `.gdtf`/`.mvr` would use. This avoids doubling the UI surface and keeps the network feature additive rather than a second app mode.
- **Packaging constrains technology choices upstream of features:** Whatever UI framework and parsing/network libraries are chosen must be proven to package into single-file/installer builds for both OSes without a Python runtime. This doesn't block feature design, but it is a hard filter on *how* each feature above gets implemented (covered fully in STACK.md).
- **Modernized UI enhances rather than blocks the diffing/search features:** Diff highlighting and searchable attribute lists are functionally achievable in a plain UI, but the requested "modernized UI" is what makes them pleasant and discoverable — sequence UI framework decisions before or alongside these features, not after.

## MVP Definition

### Launch With (v1)

Minimum viable product — validates the "beefed up" comparer without full network scope.

- [ ] Standalone packaged builds for macOS and Windows (no Python required) — the core distribution requirement; without this, nothing else matters for sharing with colleagues
- [ ] Spec-correct GDTF parsing via an existing library (not further hand-rolled XML flattening) — fixes silent-collision bug and unblocks everything else
- [ ] Full attribute set exposed with search/filter (not just Beam + Physical) — the headline "configurable attribute selection" requirement
- [ ] Visual diff highlighting on the comparison table — the headline "make differences obvious" requirement
- [ ] CSV export of the comparison table — cheap, expected, unblocks sharing results outside the app
- [ ] Modernized UI shell (visual refresh over the existing 1-target-vs-N compare flow) — table stakes for anything to feel "beefed up" rather than reskinned
- [ ] Crash-bug fixes: proper error handling for corrupt/invalid files, no more unimported-`messagebox` crash — non-negotiable baseline reliability

### Add After Validation (v1.x)

Features to add once the core rebuilt comparer is working and stable.

- [ ] MVRxchange local-network receive-only client (discover stations, pull an MVR, feed its fixtures into the existing compare workflow) — trigger: core parsing/compare/UI is solid and the parsing library swap has proven reliable
- [ ] Saved/named attribute-selection profiles — trigger: users report re-selecting the same attribute subsets repeatedly
- [ ] Diff-only export mode (CSV limited to rows that actually differ) — trigger: users report the full-table CSV export as noisy for large fixture sets

### Future Consideration (v2+)

Features to defer well beyond this milestone.

- [ ] MVRxchange internet/coordinator-server mode — defer until local-network mode is proven and there's a concrete cross-venue use case
- [ ] Broadcasting/hosting an MVRxchange group (becoming a full peer, not just a receiver) — defer until/unless there's a real need for this tool to be a source of truth other software pulls from, not just a consumer
- [ ] Any 3D visualization — explicitly out of this tool's lane (see Anti-Features); only reconsider if the product's core value pivots away from "comparison" toward "previz"

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|----------------------|----------|
| Standalone macOS + Windows packaging | HIGH | MEDIUM | P1 |
| Spec-correct GDTF parsing (replace naive parser) | HIGH | MEDIUM-HIGH | P1 |
| Searchable/configurable attribute selection | HIGH | MEDIUM | P1 |
| Visual diff highlighting | HIGH | LOW-MEDIUM | P1 |
| CSV export | MEDIUM | LOW | P1 |
| Modernized UI | HIGH | MEDIUM | P1 |
| Crash-bug fixes / error handling | HIGH | LOW | P1 |
| MVRxchange receive-only client | MEDIUM-HIGH | HIGH | P2 |
| Saved attribute-selection profiles | MEDIUM | LOW-MEDIUM | P2 |
| Diff-only CSV export | LOW-MEDIUM | LOW | P3 |
| MVRxchange internet/coordinator mode | LOW (for stated use case) | HIGH | P3 |
| MVRxchange hosting/broadcast (full peer) | LOW (for stated use case) | HIGH | P3 |
| 3D visualization | LOW (out of lane) | HIGH | Not planned |
| GDTF authoring/editing | LOW (out of lane) | HIGH | Not planned |

**Priority key:**
- P1: Must have for launch (this milestone)
- P2: Should have, add when possible (later in this milestone or immediately after)
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | GDTF Bench Online / MVR Artist Online (browser-based) | Vectorworks Spotlight / grandMA3 (full platforms) | This Project's Approach |
|---------|--------------------------------------------------------|------------------------------------------------------|--------------------------|
| File comparison / diffing | "Differ" tool does raw XML diff between two files | No dedicated compare feature; comparison is implicit in patch/update workflows | Structured, attribute-level N-way diff with visual highlighting — more readable than raw XML, more explicit than "check what changed after import" |
| Attribute coverage | 60+ GDTF properties exposed across its toolset | Full spec support, but buried in general fixture/patch editing UI, not framed as "compare" | Same full spec coverage, but purpose-built for comparison with search/filter, not general editing |
| Distribution | Browser-based, no install, but requires being online and using their site | Paid, heavy installs (console software or CAD platform) | Free, native, standalone installer/app — no browser dependency, no purchase, no license |
| MVRxchange | Not applicable (these are single-file tools, not live network participants) | Full bidirectional MVRxchange support (both are reference-class implementations) | Receive-only client — lighter than a full platform, but still networked, which no lightweight/free tool currently offers |
| Export | Unclear/limited public documentation on export beyond viewing | Native export to their own formats + MVR | CSV export of comparison results, explicitly for sharing outside the tool |
| GDTF authoring | Separate dedicated tool (GDTF Fixture Builder) | Supported via integration with the same builder | Explicitly out of scope — link out to existing builder tools instead |

## Sources

- [GDTF Hub Tools](https://www.gdtf.eu/docs/gdtf-eu-tools/) — GDTF Bench Online and MVR Artist Online feature lists (3D Viewer, Differ, Patch viewer, Power Planner, etc.)
- [GDTF Hub — GDTF Share Fixture Library Added to GDTF Bench](https://www.gdtf.eu/blog/gdtf-share-fixture-library-added-to-the-gdtf-bench-online-tool/) — "60+ utilized GDTF properties" claim
- [Vectorworks — Become a GDTF & MVR Expert](https://www.vectorworks.net/en-US/newsroom/key-features-gdtf-mvr) — Spotlight's GDTF-Share integration, Update GDTF Files workflow
- [Vectorworks — Collaborating with MVR-xchange](https://app-help.vectorworks.net/2026/eng/VW2026_Guide/LightingDesign1/Collaborating_with_MVR-xchange.htm) — MVR-xchange group/station model, local vs. internet modes
- [GDTF Hub — Exploring MVR-xchange Protocol with Wireshark](https://www.gdtf.eu/blog/exploring-mvr-xchange-protocol-with-wireshark/) — protocol transport details (TCP/mDNS, WebSocket/DNS)
- [GitHub — mvrdevelopment/tools](https://github.com/mvrdevelopment/tools) — confirmed contents: Wireshark dissector, XSD/Schematron schemas, GDTF-Share API docs (NOT a parsing library or protocol client)
- [GitHub — open-stage/python-gdtf (pygdtf)](https://github.com/open-stage/python-gdtf) — actual reusable GDTF parsing library
- [GitHub — open-stage/python-mvr (pymvr)](https://github.com/open-stage/python-mvr) — actual reusable MVR parsing library; confirms MVR-xchange is not implemented here
- [GitHub — open-stage/blender-dmx](https://github.com/open-stage/blender-dmx) — BlenderDMX README confirms it contains the working open-source MVR-xchange client implementation, built on pygdtf/pymvr
- [MA Lighting Help — My Virtual Rig (MVR) in grandMA3](https://help.malighting.com/grandMA3/2.3/HTML/patch_mvr.html) — UUID-based fixture matching, selective import (address/position/both) — informs diff-matching design
- [Capture 2025 Reference Manual — File Menu](https://www.capture.se/Manual/en-UK/2025/FileMenu.html) — MVR import with fixture-library matching prompt

---
*Feature research for: GDTF/MVR fixture comparison desktop application*
*Researched: 2026-09-25*
