# Project Research Summary

**Project:** GDTF Comparer
**Domain:** Cross-platform Python desktop GUI app for lighting/AV professionals — GDTF/MVR fixture comparison tool with standalone macOS+Windows packaging and MVR-xchange network integration
**Researched:** 2026-09-25
**Confidence:** MEDIUM-HIGH

## Executive Summary

GDTF Comparer is a niche-but-well-precedented category: a focused, offline-first desktop "diff tool" for lighting-fixture description files, sitting between browser-based utility suites (GDTF Bench Online's "Differ") and full design platforms (Vectorworks, grandMA3). Experts in this space build it as a layered desktop app — a framework-agnostic domain core (parsing + diffing + export) wrapped by a GUI, with any network I/O isolated behind an event-based boundary so it never touches widgets directly. That pattern is not unique to this domain; it's how any desktop app with background I/O avoids freezing its UI, and it maps directly onto this project's two riskiest asks (a modernized UI and live MVR-xchange networking).

The recommended approach: adopt PySide6 (Qt for Python) as the GUI framework — its native table/tree model and thread-safe Signal/Slot system solve both the "modernized UI with a real diff grid" requirement and the "background network I/O must not freeze the app" requirement in one choice. Replace the current hand-rolled, flattening XML walk with the spec-correct `pygdtf`/`pymvr` libraries (MIT-licensed, zero runtime deps, used in production by BlenderDMX), and route both local and network-sourced files through the same `FixtureRepository` parsing seam so there's exactly one code path to secure and test. Sequence the work core-first: extract the domain layer, add CSV export, build the new GUI, stand up packaging early (not last), and build MVR-xchange networking last, since it's the highest-risk, highest-complexity component and the project's own constraint ("networking must not break file-based comparison for non-networked users") is easiest to guarantee by building it as a genuinely optional, additive subsystem on top of an already-stable core.

The key risks cluster into three groups, and all three are avoidable with known techniques rather than open research problems. First, distribution risk: PyInstaller builds that work on the dev machine but fail on a clean install, plus macOS Gatekeeper and Windows SmartScreen blocking first launch for non-technical users — mitigated by clean-VM smoke tests, `--onedir` builds, and budgeting real time for code-signing/notarization. Second, correctness risk: the current parser's flat-dict attribute collisions (e.g., `Name` on a Geometry colliding with `Name` on a DMXChannel) must not be silently reintroduced when swapping in a richer parsing library — the fix is to model comparisons around GDTF's actual section/path structure, not a generic dict. Third, security/robustness risk, which compounds once MVR-xchange is added: GDTF/MVR files are untrusted ZIP+XML input (from disk *and*, once networked, from any peer on the LAN with zero authentication in the protocol spec) — this requires `defusedxml`, size/zip-bomb guards, and treating every network payload as adversarial by default, applied to local files first (parsing-robustness phase) and re-verified before networking ships.

## Key Findings

### Recommended Stack

The stack centers on Python 3.11/3.12 (the floor/ceiling intersection of all pinned dependencies), PySide6 6.11.2 for the GUI, and the `pygdtf`/`pymvr` libraries (from the `open-stage` GitHub org, not `mvrdevelopment/tools` — that repo is schemas/docs only, not a parsing library, a correction verified directly against its contents) for spec-correct parsing. MVR-xchange networking is supported by `zeroconf` (mDNS/LAN discovery) and `websockets` (internet/coordinator mode), with the wire protocol itself implemented from the public spec rather than copied from BlenderDMX's reference client (which is GPL-3.0 — a license-compatibility trap flagged explicitly in both STACK and ARCHITECTURE research). PyInstaller 6.22.3 handles packaging for both OSes, run as separate per-OS build jobs (no cross-compilation is possible).

**Core technologies:**
- PySide6 6.11.2: GUI framework — mature `QTableView`/`QAbstractItemModel` for a diff-highlighted comparison grid, plus thread-safe Signal/Slot marshaling needed for background network I/O; LGPL (free to ship), unlike PyQt6's GPL/commercial split.
- pygdtf 1.4.5 / pymvr 1.0.7: GDTF/MVR parsing — the real, actively-maintained, spec-correct (GDTF 1.2 / MVR 1.6) parsing libraries used in production by BlenderDMX; MIT-licensed, zero runtime dependencies (trivial PyInstaller bundling).
- zeroconf 0.151.3 + websockets 17.1: MVR-xchange transport — mDNS peer discovery for LAN mode and WebSocket client for internet/coordinator mode, matching the protocol's documented dual-transport design.
- PyInstaller 6.22.3: standalone macOS `.app` + Windows `.exe` builds, with built-in PySide6 hooks; `--onedir` preferred over `--onefile` for reliability and lower AV false-positive rates.
- qt-material 2.17 (or PySide6-Fluent-Widgets for a Windows-11 look): fastest path to a modernized visual theme without hand-written QSS.

### Expected Features

The GDTF/MVR tooling ecosystem already treats comparison/diffing as a first-class, named capability (GDTF Bench Online's "Differ"), validating this project's core value rather than requiring the team to invent the category. The differentiation opportunity is being the free, native, standalone (no browser, no license) tool with a *structured* attribute-level N-way diff, rather than raw XML diffing.

**Must have (table stakes):**
- Native standalone app, no runtime install (macOS + Windows)
- Full attribute/property coverage (60+ properties) with search/filter, not just the current two hardcoded categories
- Visual highlighting of differences in the comparison table
- Correct, spec-aware GDTF/MVR parsing (fixes the current silent name-collision bug)
- Graceful handling of malformed/corrupt files (fixes the current crash bug)
- CSV export of comparison results
- Modernized, professional visual UI

**Should have (differentiators):**
- MVR-xchange local-network receive-only client (pull a live fixture/scene from a peer's session into the same compare workflow)
- Saved/named attribute-selection ("compare profile") sets
- Multi-way (N-fixture) diff highlighting, cleaner than competitors' pairwise-only diffing
- Diff-only CSV export (rows that actually differ)

**Defer (v2+):**
- MVR-xchange internet/coordinator-server mode (bundle LAN mode only for this milestone)
- Becoming a full bidirectional MVR-xchange peer (hosting/broadcasting, not just receiving)
- Any 3D visualization or GDTF authoring/editing — explicitly out of this tool's lane; point users to existing dedicated tools instead

### Architecture Approach

A strictly layered desktop app: a framework-agnostic `domain/` core (FixtureRepository wrapping pygdtf/pymvr, ComparisonEngine, dataclass models) with zero GUI or socket imports; a thin ViewModel/Controller boundary; a `gui/` presentation layer (PySide6 widgets); an `export/` layer depending only on `domain/`; and a `network/` layer (MVR-xchange client) that runs entirely off the GUI thread and communicates with it only through typed events (Qt signals or a thread-safe queue) — never direct widget mutation from a background thread. `app.py` is the single composition root that wires all layers together, keeping the dependency graph a strict DAG instead of the current codebase's GUI-calls-parser-directly spaghetti.

**Major components:**
1. FixtureRepository — the single choke point wrapping pygdtf/pymvr; both local file loads and network-received MVR bytes flow through this one seam, so there is exactly one parsing/validation path to harden and test.
2. ComparisonEngine — pure, framework-agnostic diffing logic (target + N comparisons + selected attributes → structured `ComparisonResult`), fully unit-testable without a GUI.
3. NetworkClient (MVR-xchange) — background-thread(s)/event-loop wrapping zeroconf + TCP/WebSocket I/O, isolated behind an `events.py` contract; feature-flagged off by default so the core app is never blocked by network bugs.
4. GUI layer (PySide6) — renders the diff table, attribute selector, and network panel; imports only ViewModel classes, never domain/network code directly.

### Critical Pitfalls

1. **Frozen/packaged app fails on a clean machine** — PyInstaller only bundles what static analysis detects; test the actual built artifact on a genuinely clean VM per OS, not just `python app.py` on the dev machine.
2. **macOS Gatekeeper / Windows SmartScreen block first launch** — unsigned builds show "damaged app" or malware warnings to non-technical users; budget real time for code-signing/notarization (or ship `--onedir` + clear click-through instructions) before wider distribution.
3. **Flat attribute-dict comparison model reintroduces collisions on top of a richer parser** — swapping in pygdtf/pymvr does not fix the current bug unless the comparison layer is redesigned around the library's structured object model (sections/paths), not flattened back into a generic dict.
4. **Untrusted XML/ZIP input (XXE, billion-laughs, zip bombs)** — GDTF/MVR files come from disk *and*, once networked, from unauthenticated peers; swap to `defusedxml` and enforce size/ratio limits before extraction, applied to all entry points, before MVR-xchange networking multiplies the attack surface.
5. **MVR-xchange networking on the GUI thread, or scope creep into a full bidirectional peer** — network I/O must run on a background thread/event loop with events surfaced via a thread-safe queue or Qt signals; and the integration should be scoped narrowly (receive-only, LAN mode, specific message types) rather than implementing the full protocol surface.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Domain Core & Parsing Rebuild
**Rationale:** Every other phase (new GUI, export, networking) needs a stable, GUI-independent domain model to target; this also directly fixes the codebase's documented core anti-pattern (GUI calling the parser inline) and its worst bug (silent attribute-name collisions).
**Delivers:** `domain/` package (models, `FixtureRepository` wrapping pygdtf/pymvr, `ComparisonEngine`), hardened XML/ZIP parsing (`defusedxml`, size/ratio guards), fixed crash bugs (missing `messagebox` import, no error handling), unit tests proving same-named attributes from different GDTF sections stay distinct.
**Addresses:** Correct GDTF parsing, full attribute coverage, crash-bug fixes (all P1 in FEATURES.md).
**Avoids:** Pitfall 4 (flat-dict collisions), Pitfall 5 (XXE/billion-laughs), Pitfall 6 (zip-bomb DoS) — applied to local files first so the same hardening is already proven before networking exists.

### Phase 2: Export Layer
**Rationale:** Small, low-risk phase that validates the domain model from Phase 1 is actually complete/useful before investing in a new GUI on top of it.
**Delivers:** `export/csv_export.py` — `ComparisonResult` -> CSV, no widget/UI knowledge.
**Uses:** stdlib `csv` (no new dependency).
**Implements:** ExportService component from ARCHITECTURE.md.

### Phase 3: Modernized GUI (PySide6)
**Rationale:** The biggest visible-value chunk; should ship as a complete, working, offline-capable app before networking is added, directly satisfying PROJECT.md's constraint that file-based comparison must keep working for non-networked users.
**Delivers:** PySide6 main window, searchable/filterable attribute selector (`QSortFilterProxyModel`), diff-highlighted comparison table (`QTableView`), modern theming (qt-material or PySide6-Fluent-Widgets), ViewModel boundary wired to Phase 1's domain layer and Phase 2's export service.
**Addresses:** Searchable attribute selection, visual diff highlighting, modernized UI (all P1 in FEATURES.md).
**Avoids:** Pitfall — GUI directly calling parser/mutating widgets from background code (Anti-Pattern 1 in ARCHITECTURE.md).

### Phase 4: Standalone Packaging (macOS + Windows)
**Rationale:** Should start as soon as the GUI framework choice is locked in (even a "hello world" packaged build) so framework-specific packaging issues surface early rather than as a last-minute blocker; can run partly in parallel with/right after Phase 3, not strictly last.
**Delivers:** PyInstaller `--onedir` builds for both OSes (built on-OS, e.g., via CI matrix), macOS code-signing + notarization path, Windows SmartScreen/AV mitigation (local bootloader compile, VirusTotal pre-release scan), clean-VM smoke tests as a required gate.
**Addresses:** Standalone packaged builds for macOS and Windows (P1 in FEATURES.md) — the core distribution requirement.
**Avoids:** Pitfall 1 (frozen app fails on clean machine), Pitfall 2 (Gatekeeper "damaged app"), Pitfall 3 (SmartScreen/AV false positive).

### Phase 5: MVR-xchange Networking (Receive-Only, LAN Mode)
**Rationale:** Highest-complexity, highest-risk component (concurrent I/O, mDNS quirks across OSes, binary protocol, thread-safety bridging); deliberately sequenced last so it's built against an already-stable, already-useful core rather than co-evolving both at once, and so the "must not break file-based comparison" constraint is trivially satisfied by making it an optional, additive subsystem.
**Delivers:** `network/` package (mDNS discovery via `zeroconf`, TCP client implementing `MVR_JOIN`/`MVR_REQUEST`/`MVR_COMMIT` framing, background thread + event contract), network-received files routed through the same Phase 1 `FixtureRepository` seam, explicit user opt-in (no auto-starting listener), same untrusted-input hardening as Phase 1 applied to network payloads.
**Addresses:** MVR-xchange receive-only client (P2 in FEATURES.md).
**Avoids:** Pitfall 7 (GUI-thread network freeze), Pitfall 8 (trusting network peers by default), Pitfall 9 (MVR-xchange scope creep — explicitly scope to JOIN/REQUEST/receiving COMMIT, not full session-hosting).

### Phase Ordering Rationale

- Dependency-driven: GUI, export, and networking all need Phase 1's stable domain model first — parsing correctness is the hard prerequisite the whole milestone hinges on (STACK.md, ARCHITECTURE.md, PITFALLS.md all independently converge on this).
- Risk-driven: packaging is pulled forward (Phase 4, parallel with/after Phase 3) rather than left last, because framework-specific bundling issues are cheaper to discover early; networking is pushed to the end because it's the single highest-risk, least-documented component (MEDIUM-LOW confidence on protocol specifics per PITFALLS.md) and the project's explicit constraint requires it to be provably non-breaking, which is easiest to guarantee against an already-solid core.
- Security-driven: XML/ZIP hardening is done once in Phase 1 against local files (lower-stakes trust boundary) and explicitly re-verified in Phase 5 against network-received payloads (higher-stakes, adversarial-by-default trust boundary) rather than deferred until networking ships.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 5 (MVR-xchange Networking):** protocol wire-format specifics (message framing, mDNS service-type string, exact port numbers) are only MEDIUM/LOW confidence — verified against a single vendor spec page and a GPL-licensed reference implementation, not a documented SDK. Recommend `/gsd-plan-phase --research-phase 5` to re-verify against `mvrdevelopment/spec`'s actual spec text and cross-check with the Wireshark-dissector-based reverse-engineering blog post before implementation.
- **Phase 4 (Packaging):** macOS notarization and Windows SmartScreen/AV false-positive mitigation are well-documented in general but have project-specific unknowns (Apple Developer account setup, actual AV vendor response times) — light research recommended, primarily to confirm current entitlement requirements at implementation time (Qt/PyInstaller-specific packaging guidance evolves).

Phases with standard patterns (skip research-phase):
- **Phase 1 (Domain Core & Parsing):** pygdtf/pymvr are HIGH-confidence, directly-verified PyPI packages with clear integration patterns; XML/ZIP hardening (defusedxml, size limits) is standard, well-documented practice.
- **Phase 2 (Export):** stdlib `csv`, no external unknowns.
- **Phase 3 (GUI):** PySide6's model/view patterns and Signal/Slot threading are mature, extensively documented Qt patterns.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM-HIGH | Package/version facts verified directly against PyPI's registry API and official GitHub source (HIGH); MVR-xchange protocol wire details rely on a single vendor blog/spec page (MEDIUM/LOW) |
| Features | MEDIUM | Web search only, no paid research providers configured; several claims cross-verified across 2+ independent sources (GDTF Hub docs, Vectorworks docs, competitor tool pages) |
| Architecture | MEDIUM | Component boundaries and build-order reasoning are HIGH confidence (standard layered-desktop-app practice); MVR-xchange protocol/library specifics cross-verified across the official GDTF Hub spec page and the `open-stage` org's source directly, but this is a small/niche ecosystem not indexed by package-registry tooling |
| Pitfalls | MEDIUM | Web-sourced community/vendor knowledge for packaging/XML-security findings, broadly corroborated across multiple independent sources; MVR-xchange protocol-specific pitfalls (security model, message types) rely primarily on a single vendor page with no independent reference implementation to cross-check (MEDIUM-LOW) |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- MVR-xchange wire protocol specifics (exact message framing, mDNS service-type string, port numbers, chunked-transfer field names) need re-verification directly against `mvrdevelopment/spec`'s `mvr-spec.md`/xchange spec text during Phase 5 planning — current findings are corroborated across two sources (GDTF Hub spec page + BlenderDMX reference implementation) but neither is a fully documented, versioned protocol SDK.
- GPL-3.0 licensing boundary: BlenderDMX's `mvrx_protocol.py` and related modules are a useful architecture *reference* (thread-per-client pattern, event bridging) but must not be copied verbatim into this project without accepting GPL-3.0 obligations for the whole app — confirm this constraint explicitly with the user before Phase 5 implementation if any code inspection/porting is planned.
- `pygdtf` PyPI package identity was flagged by an automated legitimacy heuristic as needing manual verification (small/low-download package can trip typosquat-style checks) — confirm the exact PyPI package and pinned version resolve to the `open-stage` org's published releases before first install in Phase 1.
- Apple Developer account / code-signing budget ($99/yr) and time cost for notarization debugging cycles are not yet a confirmed decision — needs a go/no-go call before or during Phase 4 planning, since PROJECT.md's constraint ("people other than the creator can run it") effectively requires this for a good macOS first-run experience.

## Sources

### Primary (HIGH confidence)
- PyPI JSON API (`https://pypi.org/pypi/<package>/json`) — direct registry queries for all pinned packages (pygdtf, pymvr, PySide6, websockets, zeroconf, qt-material, PyInstaller, pytest-qt, etc.), fetched 2026-09-25
- `https://github.com/mvrdevelopment/tools` — fetched directly, confirms repo is schemas + Wireshark dissector + GDTF-Share API docs only, not a parsing library
- `https://raw.githubusercontent.com/open-stage/python-gdtf/master/pyproject.toml` and `https://raw.githubusercontent.com/open-stage/python-mvr/main/pyproject.toml` — confirms zero runtime dependencies, Python `>=3.8`
- `https://github.com/open-stage/blender-dmx` and `mvrx_protocol.py` — MVR-xchange reference implementation (architecture reference only; GPL-3.0)

### Secondary (MEDIUM confidence)
- [GDTF Hub — MVR-xchange Communication Format Definition](https://www.gdtf.eu/mvr/mvr-spec/xchange/) and [Exploring MVR-xchange Protocol with Wireshark](https://www.gdtf.eu/blog/exploring-mvr-xchange-protocol-with-wireshark/) — protocol transport/message-field details
- [Vectorworks — Collaborating with MVR-xchange](https://app-help.vectorworks.net/2026/eng/VW2026_Guide/LightingDesign1/Collaborating_with_MVR-xchange.htm) — mDNS-then-WebSocket architecture confirmation
- [GDTF Hub Tools](https://www.gdtf.eu/docs/gdtf-eu-tools/) and [GDTF Share Fixture Library / GDTF Bench blog post](https://www.gdtf.eu/blog/gdtf-share-fixture-library-added-to-the-gdtf-bench-online-tool/) — competitor feature landscape, "60+ properties" claim
- [pythonguis.com — Antivirus false positives with PyInstaller](https://www.pythonguis.com/faq/problems-with-antivirus-software-and-pyinstaller/) and related PyInstaller GitHub issues (#7937, #5112, #6754) — packaging pitfalls
- [defusedxml on PyPI](https://pypi.org/project/defusedxml/) and [Sourcery — Python XXE vulnerability](https://www.sourcery.ai/vulnerabilities/python-lang-security-use-defused-xml-parse) — XML hardening guidance

### Tertiary (LOW confidence)
- Web search synthesis (pythonguis.com, general 2026 Python packaging/GUI comparison articles) — used only for qualitative framework positioning, not version numbers
- MVR-xchange security-model characterization ("no authentication/encryption in the spec") — inferred from a single vendor spec page with no independent reference implementation to cross-check against; treat as needing re-verification, not settled fact

---
*Research completed: 2026-09-25*
*Ready for roadmap: yes*
