# Architecture Research

**Domain:** Desktop lighting-fixture comparison tool (Python) with modern GUI, offline file parsing, and live network protocol (MVR-xchange) sync
**Researched:** 2026-09-25
**Confidence:** MEDIUM (component boundaries and build-order reasoning are HIGH confidence — standard layered-desktop-app practice; MVR-xchange protocol/library specifics are cross-verified across the official GDTF Hub spec page and the `open-stage` GitHub organization's source directly, but individual web sources score LOW on the raw provider tier since this is a small/niche ecosystem not indexed by package-registry tooling. Treat protocol/library facts as "verified against two independent official sources," not "SDK-documented.")

## Standard Architecture

### System Overview

```
┌───────────────────────────────────────────────────────────────────────┐
│                        Presentation Layer (GUI)                       │
│  MainWindow / Views  ·  AttributeSelector  ·  DiffTable  ·  Network   │
│  Panel — framework-native widgets only, zero parsing/network imports  │
├──────────────────────────────┬─────────────────────────┬──────────────┤
│                               │                         │              │
│                        ViewModel / Controller layer (thin, testable)  │
│         translates domain objects <-> widget-friendly view state      │
├──────────────────────────────┴─────────────────────────┴──────────────┤
│                         Application/Domain Core                       │
│  ┌────────────────┐  ┌────────────────────┐  ┌──────────────────┐    │
│  │ FixtureRepo     │  │ ComparisonEngine    │  │ ExportService     │    │
│  │ (wraps pygdtf/  │  │ (attribute diffing, │  │ (CSV/JSON writers,│    │
│  │  pymvr parsing) │  │  category filtering)│  │  no UI knowledge) │    │
│  └────────┬────────┘  └─────────┬───────────┘  └─────────┬─────────┘   │
│           │                     │                        │             │
├───────────┴─────────────────────┴────────────────────────┴────────────┤
│                    Network Layer (MVR-xchange client)                 │
│  mDNS discovery (zeroconf)  ·  TCP client/server  ·  WebSocket client │
│  runs on background thread(s)/event loop; talks to GUI only via a     │
│  thread-safe queue or the GUI framework's cross-thread signal system  │
├─────────────────────────────────────────────────────────────────────┤
│                          Packaging / Runtime                          │
│  PyInstaller (onedir) builds  ·  macOS .app + codesign/notarize path  │
│  Windows .exe + installer  ·  bundled Python interpreter, no host dep │
└───────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|-------------------------|
| Presentation (Views) | Render widgets, capture user input, display diff table/highlighting, show network status | PySide6 (Qt for Python) widgets/QML, or CustomTkinter widgets if staying Tkinter-based |
| ViewModel/Controller | Adapt domain objects to view-friendly state; owns no parsing/network code; the *only* thing that imports both GUI classes and domain classes | Plain Python classes; Qt Signal/Slot bindings if PySide6 |
| FixtureRepository | Load a `.gdtf`/`.mvr` file into the app's internal model, wrapping `pygdtf`/`pymvr` (or the current hand-rolled parser during transition) behind one interface | Thin adapter class; this is the seam where "hand-rolled parsing" gets replaced by MVR-xchange-ecosystem libraries without touching UI or export code |
| ComparisonEngine | Given a target fixture + N comparison fixtures + selected attribute set, produce a structured diff result (which attributes differ, per file) | Pure function/class, framework-agnostic, unit-testable without a display |
| ExportService | Serialize a `ComparisonResult` to CSV (and later other formats) | Pure function, takes domain object, returns bytes/writes file — no widget references |
| NetworkClient (MVR-xchange) | mDNS discovery, TCP/WebSocket join/leave/commit/request handling, file transfer chunking | Background thread(s) (or a dedicated asyncio loop run in one thread) wrapping `zeroconf` + raw sockets/`websockets`; emits events the GUI layer consumes asynchronously |
| Packaging scripts | Produce a double-clickable, dependency-free app per OS | PyInstaller spec files (`.spec`) per platform, run in CI per OS (must build ON the target OS) |

## Recommended Project Structure

```
src/gdtf_comparer/
├── domain/                  # Framework-agnostic core; no GUI or socket imports
│   ├── models.py            # FixtureType, ComparisonResult, AttributeDiff dataclasses
│   ├── fixture_repository.py# Wraps pygdtf/pymvr; single choke point for parsing
│   └── comparison_engine.py # Diffing logic, attribute selection/filtering
├── export/
│   └── csv_export.py        # ComparisonResult -> CSV; add json_export.py etc later
├── network/
│   ├── discovery.py         # zeroconf mDNS register/browse
│   ├── mvrx_client.py       # TCP client: JOIN/LEAVE/COMMIT/REQUEST framing
│   ├── mvrx_ws_client.py    # WebSocket mode variant
│   ├── mvrx_server.py       # TCP listener for incoming peer requests
│   └── events.py            # Typed events the GUI subscribes to (StationSeen, FileOffered, TransferComplete, TransferFailed)
├── gui/
│   ├── main_window.py       # Top-level window composition
│   ├── attribute_selector.py
│   ├── diff_table.py        # Diff highlighting rendering
│   ├── network_panel.py     # Station list, join/request UI
│   └── view_models.py       # Domain <-> view adapters
├── app.py                   # Composition root: builds repo/engine/export/network, wires to GUI, starts event loop
└── __main__.py               # Entry point for `python -m gdtf_comparer` and for PyInstaller
tests/
├── domain/                  # Fast, no GUI, no network — bulk of test coverage
├── network/                 # Protocol framing tests with mocked sockets
└── gui/                     # Optional smoke tests only
packaging/
├── pyinstaller_macos.spec
├── pyinstaller_windows.spec
└── build.md                 # Per-OS build instructions (must build on-OS)
```

### Structure Rationale

- **`domain/` has zero GUI or socket imports:** this is the direct fix for the current codebase's core anti-pattern (`GDTFComparerApp.run_comparison()` calling `parse_gdtf()` and mutating the Treeview inline). Every other layer depends on `domain/`; `domain/` depends on nothing app-specific.
- **`network/` is isolated behind an `events.py` contract:** the GUI never touches sockets, `zeroconf`, or threading primitives directly. It only reacts to typed events. This makes the network layer independently testable (feed it mocked TCP/WS payloads) and means it can be developed, or even entirely stubbed out, without blocking GUI work.
- **`export/` depends only on `domain/`:** exporting doesn't know a GUI exists, so "export to CSV" works identically from the GUI, a future CLI, or a test.
- **`app.py` is the only file that imports from all layers** (composition root) — this keeps the dependency graph a strict DAG instead of the current spaghetti.

## Architectural Patterns

### Pattern 1: Repository/Adapter over the parsing library

**What:** `FixtureRepository.load(path) -> FixtureType` wraps whichever underlying parser is in use (today's hand-rolled `parse_gdtf`, tomorrow's `pygdtf`/`pymvr`) and returns the app's own domain model, not the library's raw objects.
**When to use:** Any time an external library's object shape might change or you want to swap libraries without touching call sites.
**Trade-offs:** One extra layer of indirection; pays for itself the moment you actually swap the parser (which this milestone explicitly plans to do), and insulates the rest of the app from `pygdtf`/`pymvr` API changes.

```python
# domain/fixture_repository.py
class FixtureRepository:
    def load(self, path: str) -> FixtureType:
        raw = pygdtf.FixtureType(path)          # or pymvr for .mvr
        return FixtureType.from_pygdtf(raw)       # map to our own dataclass
```

### Pattern 2: Background network worker + thread-safe event queue (or GUI-native signals)

**What:** The MVR-xchange client (mDNS discovery + TCP/WebSocket I/O) runs entirely off the GUI thread. It never touches widgets directly. It posts events (station discovered, file offered, transfer progress/complete/failed) onto either (a) a `queue.Queue` that the GUI polls on a timer, or (b) if using Qt, emits thread-safe `Signal`s that Qt marshals onto the GUI thread automatically.
**When to use:** Any GUI framework — this is required because GUI event loops (Tkinter `mainloop`, Qt event loop) are single-threaded and must never block on network I/O, and widgets must never be touched from a non-GUI thread.
**Trade-offs:** Qt's Signal/Slot mechanism is safer and less error-prone than a hand-rolled `queue.Queue` + `.after()` poll loop (Tkinter's idiom) because Qt guarantees the cross-thread marshaling; Tkinter requires you to build and discipline that yourself. This is a real point in favor of choosing Qt for this milestone specifically because live networking is in scope.

```python
# network/mvrx_client.py (thread target)
def run(self):
    for msg in self._receive_loop():
        self.on_event(parse_message(msg))   # on_event is a callback/signal, not a widget call

# gui/network_panel.py (Qt)
self.client.station_discovered.connect(self._add_station_row)  # auto thread-marshaled
```

### Pattern 3: Optional/pluggable subsystem via feature flag

**What:** The network layer starts disabled by default (or "offline mode") and the app is fully functional for local file comparison with it off. `app.py` wires the network subsystem only if enabled; the GUI's network panel degrades to "not connected" rather than failing.
**When to use:** Whenever a major subsystem is higher-risk/optional and a hard project constraint says the rest of the app "must not break" if it's unavailable — exactly PROJECT.md's constraint here ("MVRxchange integration must not break basic file-based comparison for users who aren't networked").
**Trade-offs:** Small amount of extra wiring (a flag/config check) in exchange for the core app never being blocked by network-layer bugs, firewall/mDNS issues, or protocol edge cases during development.

## Data Flow

### Local comparison flow (unchanged in spirit, now layered)

```
User picks files (GUI)
    ↓
ViewModel calls FixtureRepository.load() for target + each comparison file
    ↓
ComparisonEngine.compare(target, comparisons, selected_attributes) -> ComparisonResult
    ↓
ViewModel maps ComparisonResult -> DiffTable view rows (with highlight flags)
    ↓
GUI renders table; user can trigger ExportService.to_csv(result, path)
```

### Network (MVR-xchange) flow

```
App startup (if network enabled)
    ↓
NetworkClient starts on background thread: zeroconf register + browse
    ↓
Peers discovered -> StationSeen event -> NetworkPanel updates station list
    ↓
User requests a file from a peer -> MVR_REQUEST sent -> binary/JSON reply streamed
    ↓
On completion: TransferComplete event carries raw MVR bytes
    ↓
Same FixtureRepository.load() path used for local files parses the received MVR
    ↓
Result flows into the same ComparisonEngine / DiffTable pipeline as local files
```

The key design point: incoming network files re-enter the pipeline at the *same* `FixtureRepository` seam local files use. The comparison/export/GUI layers do not need to know whether a fixture file came from disk or from the network — this is what keeps the network layer additive rather than something that forces a rearchitecture of the core.

## Scaling Considerations

This is a single-user desktop tool, not a scaled service — "scale" here means "growing complexity of a single session," not concurrent users.

| Scale | Architecture Adjustments |
|-------|---------------------------|
| Small comparisons (2-5 fixtures, occasional network peer) | Current recommended architecture handles this with no special-casing. |
| Larger comparisons (10+ fixtures, large attribute sets, many active network peers) | Move `ComparisonEngine` execution and `FixtureRepository.load()` calls for network-received files off the GUI thread too (a small thread pool or the same background worker used for networking), so the UI never freezes parsing a large batch — this is already a known bug class in the current app ("Comparison runs synchronously... will freeze UI"). |
| Many simultaneous MVR-xchange peers / large MVR scene files | Chunked transfer (the protocol already defines `MVR_PACKAGE_COUNT`/chunking) plus a transfer-progress event so the GUI can show progress instead of appearing to hang; cap concurrent transfers if peer count grows. |

### Scaling Priorities

1. **First likely bottleneck:** synchronous parsing/diffing blocking the GUI thread for large files or many-file comparisons — mitigate by running `FixtureRepository.load()` + `ComparisonEngine.compare()` off the GUI thread from day one of the rebuild, not just for network-sourced files.
2. **Second likely bottleneck:** MVR-xchange peer/session churn (stations joining/leaving, mDNS record changes) causing UI list flicker — mitigate with debounced event batching in the ViewModel layer, not in the network layer itself.

## Anti-Patterns

### Anti-Pattern 1: GUI event handler calls parser/network code directly (current codebase's actual bug)

**What people do:** `run_comparison()` (or its future equivalent) calls `parse_gdtf()`/network functions inline and mutates the Treeview/widget tree directly, as the current `BEtheLD` script does.
**Why it's wrong:** Untestable without a GUI, blocks the event loop during I/O, and makes the parser or network client impossible to reuse or swap (exactly the problem this milestone needs to solve to adopt MVR-xchange libraries).
**Do this instead:** GUI handlers call into ViewModel methods only; ViewModel calls domain/network services; results flow back as data, not as direct widget mutations from a background thread.

### Anti-Pattern 2: Doing network I/O on the GUI thread

**What people do:** Calling `socket.recv()`/mDNS browse/WebSocket read directly inside a button-click handler "just to keep it simple."
**Why it's wrong:** Freezes the entire application for the duration of any network wait (peer discovery, file transfer) — worse than the existing synchronous-parsing bug, since network waits are unbounded (peer might never respond).
**Do this instead:** All MVR-xchange I/O runs on background thread(s)/an event loop dedicated to networking; GUI only receives events.

### Anti-Pattern 3: Touching GUI widgets from a background thread

**What people do:** A network callback thread directly calls `treeview.insert(...)` or `label.setText(...)`.
**Why it's wrong:** Both Tkinter and Qt widget trees are not thread-safe; this causes crashes or corrupted UI state that are hard to reproduce (timing-dependent).
**Do this instead:** Background threads only ever enqueue events / emit signals; the GUI thread is the only thing that mutates widgets, either via a polling `.after()` loop draining a `queue.Queue` (Tkinter) or via Qt's built-in thread-safe Signal/Slot marshaling (Qt) — this is one of the practical reasons to prefer Qt if the network client is a first-class feature.

### Anti-Pattern 4: Vendoring GPL-licensed reference code into a differently-licensed project without checking

**What people do:** Copy the MVR-xchange client implementation from `open-stage/blender-dmx` (GPL-3.0) directly into this project.
**Why it's wrong:** `blender-dmx`'s protocol implementation (`mvrx_protocol.py` and related modules) is GPL-3.0-licensed; copying it verbatim would obligate this project to GPL-3.0 licensing too. By contrast, `pygdtf` and `pymvr` (the parsing libraries, also from the `open-stage` org) are MIT-licensed and safe to depend on directly.
**Do this instead:** Use `pygdtf`/`pymvr` as direct dependencies (MIT). For the network protocol client, implement it independently from the public MVR-xchange protocol specification (message types, packet framing, mDNS service name are all documented openly) — the BlenderDMX source is a useful *design reference* for architecture (thread-per-client, callback/event pattern, chunked transfer) but should not be copy-pasted unless the project is comfortable adopting GPL-3.0 for the whole app.

## Integration Points

### External Services / Libraries

| Service/Library | Integration Pattern | Notes |
|------------------|----------------------|-------|
| `pygdtf` (PyPI: `pygdtf`) | Direct dependency, wrapped by `FixtureRepository` | MIT-licensed, maintained by `open-stage`, used in production by BlenderDMX. Replaces the current hand-rolled flat-attribute XML walk with spec-correct, namespaced GDTF parsing (`FixtureType`, `DmxChannel`, geometry/attribute classes). PyPI package name flagged by this project's automated legitimacy heuristic as needing manual verification (small/low-download package can trip typosquat-style checks) — confirm you're pulling `pygdtf` from the `open-stage` org's published releases, e.g. pin an exact version and check the project URL in the package metadata before first install. |
| `pymvr` (PyPI: `pymvr`) | Direct dependency, wrapped by `FixtureRepository` for `.mvr` scene files | MIT-licensed, same org/maintainers as `pygdtf`. Provides `GeneralSceneDescription`, `Scene`, `Layer`, `Fixture` object graph. |
| MVR-xchange protocol (TCP mode + WebSocket mode) | Custom client implemented from the public spec (`gdtf.eu` "Communication Format Definition"), informed by BlenderDMX's `mvrx_protocol.py`/`mvrx_server.py`/`mvrx_ws_client.py` as an architecture reference (thread-per-connection, callback events, chunked framing) but not copied verbatim (license) | Two transport modes: TCP+mDNS (zero-config LAN) and WebSocket+DNS (routable, needs a known server URL). Five message types: `MVR_JOIN`, `MVR_LEAVE`, `MVR_COMMIT`, `MVR_REQUEST`, `MVR_NEW_SESSION_HOST`. TCP packets use a fixed binary header (package header/version/number/count/type + payload length) in network byte order; WebSocket sends JSON text frames + binary frames. Implement TCP mode first (zero-config, matches "sync with other lighting/visualization software on the network" on a LAN) and treat WebSocket mode as a stretch/later addition. |
| `zeroconf` (PyPI, pure Python mDNS) | Used by the network layer for TCP-mode peer discovery | Cross-platform, no native mDNS daemon dependency (important for a no-install standalone build) — avoids requiring Bonjour/Avahi to be separately present on the user's machine. |
| PyInstaller | Build-time packaging tool, not a runtime dependency | Must run its build *on* the target OS (build the macOS app on macOS, the Windows exe on Windows) — plan CI or manual build steps accordingly. `--onedir` output is more reliable than `--onefile` for apps with data files/resources (attribute definition files, icons); `--onefile` is slower to start (self-extracts to a temp dir every launch) and has had more reported issues bundling GUI-framework data files (e.g. CustomTkinter's `.json`/font assets). macOS builds additionally need code-signing + notarization to avoid Gatekeeper warnings for a "just download and run" experience; Windows builds may trigger SmartScreen warnings without a code-signing certificate — acceptable to ship unsigned for a free community tool but worth flagging as a known rough edge, not a blocker. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|----------------|-------|
| GUI ↔ ViewModel | Direct method calls (GUI thread only) | ViewModel is the only thing GUI code imports besides widget/framework classes. |
| ViewModel ↔ Domain (FixtureRepository, ComparisonEngine) | Direct method calls, may be dispatched to a worker thread/pool for large files | Domain layer has no knowledge of the GUI framework in use — this is what makes "modernized UI" swappable without touching parsing/comparison logic. |
| ViewModel ↔ ExportService | Direct method call, triggered by user action (e.g. "Export CSV" button) | ExportService takes a `ComparisonResult`, has no GUI/network imports. |
| GUI/ViewModel ↔ NetworkClient | Event-based only (queue or GUI-native signals), never direct widget mutation from the network thread | This boundary is the one genuinely new architectural concern this milestone introduces relative to the current codebase — get this one right and the rest is a fairly standard layered refactor. |
| NetworkClient ↔ FixtureRepository | NetworkClient hands raw received MVR bytes to the same `FixtureRepository.load()` path local files use | Ensures network-sourced fixtures/scenes flow through identical parsing/validation as local files — no parallel/duplicate parsing logic for the network path. |

## Suggested Build Order (with dependency rationale)

1. **Domain core extraction first:** pull parsing (`FixtureRepository` wrapping `pygdtf`/`pymvr`, replacing the current hand-rolled walk) and `ComparisonEngine` out of the GUI file into `domain/`, fully unit-tested without any GUI. This directly fixes the codebase's documented core anti-pattern and is a hard prerequisite for everything else — both the new GUI and the network layer need a stable, GUI-independent domain model to target.
2. **Export layer next (small, low-risk):** implement `ExportService.to_csv()` against the now-stable `ComparisonResult` domain object. This is a good validation step that the domain model is actually complete/useful before investing in a new GUI on top of it.
3. **New GUI layer third:** build the modernized presentation layer (framework choice — see below) against the `domain/` + `export/` services via the ViewModel boundary. This is the biggest visible-value chunk and should ship as a complete, working, offline-capable app before networking is added — directly satisfies PROJECT.md's constraint that file-based comparison must keep working for non-networked users.
4. **Packaging pipeline in parallel with/right after step 3, not last:** stand up a minimal PyInstaller build for both OSes as soon as the GUI framework choice is locked in (even a "hello world" packaged build), so framework-specific packaging issues (e.g., CustomTkinter's data-file bundling quirks, Qt's larger bundle size, macOS notarization) surface early rather than as a last-minute blocker before release. Full packaging polish (signing, installer UX) can trail, but the "does this framework even package cleanly on both OSes" question needs answering before the GUI is fully built out, not after.
5. **MVR-xchange network layer last:** build the network client (`network/`) behind the `events.py` contract, feeding into the *same* `FixtureRepository`/`ComparisonEngine`/GUI pipeline already proven in steps 1-3. Reasons to sequence it last:
   - It is the highest-complexity, highest-risk component (concurrent I/O, mDNS quirks across OSes/networks, a binary protocol, thread-safety bridging to the GUI) — de-risk it by building it against an already-stable core rather than co-evolving both at once.
   - PROJECT.md explicitly requires that networking "must not break basic file-based comparison for users who aren't networked" — building it as an additive, optional subsystem *after* the core is solid is the natural way to guarantee that constraint, versus retrofitting an optionality flag onto networking that was built in lockstep with the core.
   - The network layer's payoff (received MVR bytes) only becomes useful once there's a working `FixtureRepository.load()` + `ComparisonEngine` + GUI to hand it to — building it earlier would mean stubbing out consumers that already exist by step 5.
   - It's the one piece most likely to need its own deeper phase-specific research spike (mDNS behavior on macOS vs Windows, firewall prompts, WebSocket-mode server availability) — better to hit that after the rest of the roadmap has already de-risked the simpler layers.

## GUI Framework Recommendation

Given this milestone explicitly wants (a) a real presentation/business-logic split, (b) standalone no-Python-required builds for macOS + Windows, and (c) a background network client that must safely push updates into the GUI:

- **Recommended: PySide6 (Qt for Python).** LGPLv3-licensed (free for this use case), genuinely modern native-feeling widgets out of the box (no extra theming library needed to look "not stock Tkinter"), and — most relevant to this milestone specifically — Qt's Signal/Slot system provides built-in, well-tested thread-safe marshaling from background worker threads to the GUI thread, which is exactly the mechanism the MVR-xchange network client needs. This avoids hand-rolling a `queue.Queue` + `.after()` poll loop and its associated race-condition risk.
- **Lower-risk fallback: keep Tkinter, add CustomTkinter (MIT) or ttkbootstrap for the visual refresh.** Smaller bundle size, less churn from the existing codebase, faster to reskin. Workable, but the cross-thread GUI update pattern must be built and disciplined manually (`queue.Queue` + `root.after()` polling) — doable, just more manual plumbing than Qt gets for free, and CustomTkinter's non-standard data-file bundling has known PyInstaller gotchas (must use `--onedir`, not `--onefile`, and manually `--add-data` its assets).
- Either choice is compatible with the layered architecture above — the framework choice only affects the `gui/` folder and the exact mechanism used at the GUI↔NetworkClient boundary; it does not change `domain/`, `export/`, or `network/`.

## Sources

- [MVR-xchange Communication Format Definition — GDTF Hub (official spec)](https://www.gdtf.eu/mvr/mvr-spec/xchange/)
- [How MVR-xchange Works — GDTF & MVR Help Pages](https://gdtf-share.com/help/developers/recipes/mvr_xchange_docs/index.html)
- [mvrdevelopment/tools — GitHub (schemas, Wireshark dissector, no Python reference client)](https://github.com/mvrdevelopment/tools)
- [open-stage/python-gdtf (pygdtf) — GitHub](https://github.com/open-stage/python-gdtf)
- [open-stage/python-mvr (pymvr) — GitHub](https://github.com/open-stage/python-mvr)
- [open-stage/blender-dmx — GitHub (MVR-xchange Python reference implementation, GPL-3.0)](https://github.com/open-stage/blender-dmx)
- [blender-dmx/mvrx_protocol.py — GitHub (architecture reference: thread-per-client TCP/WS/server pattern, callback/event bridging)](https://github.com/open-stage/blender-dmx/blob/main/mvrx_protocol.py)
- [Exploring MVR-xchange Protocol with Wireshark — GDTF Hub blog](https://www.gdtf.eu/blog/exploring-mvr-xchange-protocol-with-wireshark/)
- [Packaging Tkinter applications for Windows, with PyInstaller — Python GUIs](https://www.pythonguis.com/tutorials/packaging-tkinter-applications-windows-pyinstaller/)
- [CustomTkinter Packaging documentation](https://customtkinter.tomschimansky.com/documentation/packaging/)
- Project's own codebase map: `/Users/brandon/GDTFComparer/.planning/codebase/ARCHITECTURE.md` (source of the current anti-patterns this research addresses)

---
*Architecture research for: GDTF/MVR desktop comparison app — GUI/core/export/network layering*
*Researched: 2026-09-25*
