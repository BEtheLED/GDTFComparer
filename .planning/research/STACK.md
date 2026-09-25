# Stack Research

**Domain:** Cross-platform Python desktop GUI app for lighting/AV professionals (GDTF/MVR fixture comparison tool) with standalone macOS+Windows packaging and MVR-xchange network integration
**Researched:** 2026-09-25
**Confidence:** MEDIUM-HIGH (package/version facts verified directly against PyPI's registry API and official GitHub source; MVR-xchange protocol wire details are MEDIUM/LOW confidence — see Gaps)

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11 (floor), 3.12 OK | Runtime | Satisfies the floor of every other pinned dependency below simultaneously: `websockets` 17.x requires `>=3.11`, `zeroconf` 0.15x requires `>=3.10`, `PySide6` 6.11.x requires `>=3.10,<3.15`. Staying at 3.11/3.12 (not 3.13+) maximizes current compatibility with PyInstaller hook coverage and third-party Qt theming packages, several of which lag newest CPython by a few months. HIGH confidence (verified via PyPI `requires_python` metadata for every dependency, 2026-09-25). |
| PySide6 (Qt for Python) | 6.11.2 | GUI framework, replaces raw Tkinter | The only realistic 2026 Python GUI option with a mature, native-quality **table/tree widget model** (`QTableView`/`QTreeView` + `QAbstractItemModel`) needed for a diff-highlighted comparison grid, plus a built-in `QSortFilterProxyModel` that gives you searchable/filterable attribute selection almost for free. It's the official Qt binding (LGPL, no runtime license fee, unlike PyQt6's GPL/commercial split), actively maintained by The Qt Company, and has first-class support in PyInstaller (built-in hooks) for macOS+Windows bundling. HIGH confidence (version verified via PyPI JSON API). |
| pygdtf | 1.4.5 | GDTF (description.xml) parsing | This is the real, actively-maintained continuation of GDTF parsing logic that the `mvrdevelopment` ecosystem produced — see "Important correction" below. It implements the full GDTF 1.2 (DIN SPEC 15800:2022-02) object model, used as the parser inside BlenderDMX and other MVR/GDTF tools. Pure standard-library (`zipfile` + `xml.etree.ElementTree` internally), **zero runtime dependencies**, so it packages trivially with PyInstaller. HIGH confidence (version + zero-deps verified via PyPI JSON API and the project's own `pyproject.toml`, 2026-09-25). |
| pymvr | 1.0.7 | MVR (.mvr scene) parsing/writing | Sibling library to pygdtf, same maintainers (Open Stage org), covers MVR 1.6 (DIN SPEC 15801:2023-12) reading and writing (`GeneralSceneDescriptionWriter`). Needed because MVR-xchange exchanges MVR-wrapped scene/fixture data, not bare GDTF files. Also zero runtime dependencies. HIGH confidence (verified via PyPI JSON API + GitHub `pyproject.toml`). |

**Important correction to the milestone brief:** `github.com/mvrdevelopment/tools` (the repo named in PROJECT.md) is **not** a parsing library. Verified directly by fetching the repo: it contains only `gdtf.xsd`/`mvr.xsd`/`gdtf.sch` XML schema files, a `GDTF_Share_API/` folder of REST API docs for the online GDTF-Share database, and a `mvrxchange_dissector/` Wireshark plugin (Lua) for inspecting MVR-xchange TCP traffic. There is no Python (or any) parsing code to "borrow" from that repo. The actual spec-correct Python parsing libraries the GDTF/MVR ecosystem uses (`pygdtf`, `pymvr`) live in the **`open-stage`** GitHub org — a friendly fork/continuation maintained with the original author's permission, now the de facto standard, used by BlenderDMX, PollToMVR, and others. **Recommendation: depend on `pygdtf`/`pymvr` from PyPI, and optionally vendor `gdtf.xsd`/`mvr.xsd` from `mvrdevelopment/tools` for schema validation if stricter spec-compliance checking is ever wanted.** (MEDIUM-HIGH confidence — corroborated by GitHub repo contents, PyPI package descriptions, and multiple independent articles.)

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `websockets` | 17.1 | MVR-xchange network mode (internet/`wss://`) | MVR-xchange's non-LAN mode connects to a coordinating server over WebSocket (per Vectorworks/GDTF Hub docs on "Collaborating with MVR-xchange"). Use for the "connect to a remote/cloud station" path. Requires Python >=3.11. |
| `zeroconf` | 0.151.3 | mDNS peer discovery for MVR-xchange LAN mode | MVR-xchange's local-network mode advertises/discovers stations via mDNS (Multicast DNS) before opening a TCP session — this is the standard pure-Python mDNS implementation, already used in comparable lighting-software integrations. Requires Python >=3.10. |
| stdlib `socket`/`asyncio` | n/a (stdlib) | MVR-xchange TCP transport | The reference implementation (BlenderDMX's `mvrx_tcp_client.py`/`mvrx_tcp_server.py`) talks raw JSON-over-TCP for the LAN "TCP Mode" that the Wireshark dissector documents (message fields: `Type`, `StationUUID`, `FileUUID`, `Commits`, `Provider`, etc.). No third-party package needed beyond the stdlib socket/asyncio layers. |
| `qt-material` | 2.17 | One-line modern theming for PySide6 | Fastest path to a "modernized UI" without hand-writing QSS: applies a Material-Design-style flat theme (dark/light variants, accent colors) to stock Qt widgets in ~2 lines. Last released April 2025 — actively enough maintained, small dependency surface (PySide6/PyQt only). Good default choice for this milestone's "visual refresh" requirement. |
| `PySide6-Fluent-Widgets` | 1.11.3 | Alternative theming (Windows-11 Fluent look) | Use instead of `qt-material` if you want a native-Windows-11-style aesthetic with pre-built modern widget replacements (cards, nav panels, pivots) rather than just a color/QSS reskin of stock widgets. More actively updated (Aug 2026) and more opinionated/heavier than `qt-material` — better if you're willing to restructure the UI around its widget set, not just reskin the existing one. |
| `qtawesome` | 1.4.2 | Icon fonts (FontAwesome/Material icons) for PySide6 | Cheap way to add modern iconography (search icon, export icon, diff markers) without shipping image assets. |
| stdlib `csv` | n/a (stdlib) | CSV export of comparison results | No third-party dependency needed — Python's built-in `csv` module is sufficient for the "export comparison results" requirement. |
| `PyInstaller` | 6.22.3 | Standalone macOS + Windows builds | See Core rationale below (packaging section). |
| `pytest` | (existing) | Unit tests | Already in use; keep. |
| `pytest-qt` | 4.5.0 | GUI testing for PySide6 widgets | Adds a `qtbot` fixture for driving/asserting on Qt widgets in tests — useful once comparison-table and search/filter UI exist and need regression coverage. Requires Python >=3.9. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| PyInstaller | Build frozen, no-Python-required executables for macOS (`.app`) and Windows (`.exe`) | Run as two separate build jobs (one per OS — PyInstaller does not cross-compile) or via CI matrix (GitHub Actions `macos-latest` + `windows-latest` runners). Has built-in hooks for PySide6, so `pyinstaller --windowed --name "GDTF Comparer" main.py` handles most of the Qt plugin bundling automatically; you'll still need `--add-data` for any theme/icon assets. |
| Apple code signing + notarization (`codesign`, `notarytool`) | Required for the macOS build to launch without a Gatekeeper "unidentified developer" block | Not a Python package — a macOS/Apple Developer Program requirement ($99/yr for a Developer ID). Budget time for this in the packaging phase; an unsigned/unnotarized `.app` will still run (right-click → Open bypasses Gatekeeper once) but will scare away non-technical users, which conflicts with the "person other than the creator can just run it" success metric. |
| GitHub Actions (or equivalent CI) | Automate the macOS + Windows build matrix | Recommended over manual local builds on both OSes — avoids needing to personally own both a Mac and a Windows machine to ship both artifacts, and makes repeat releases (after each milestone) cheap. |

## Installation

```bash
# Core GUI + parsing
pip install PySide6==6.11.2 pygdtf==1.4.5 pymvr==1.0.7

# MVR-xchange network support
pip install websockets==17.1 zeroconf==0.151.3

# UI polish
pip install qt-material==2.17 qtawesome==1.4.2

# Dev dependencies
pip install -D pyinstaller==6.22.3 pytest pytest-qt==4.5.0
```

Also add a `pyproject.toml` (the codebase currently has none — flagged in `.planning/codebase/STACK.md`) to pin these instead of relying on ad hoc `pip install`.

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|--------------|-------------|--------------------------|
| PySide6 | CustomTkinter 6.0.0 | If you want to keep the existing Tkinter code and widget structure and just reskin it with minimal rewrite risk. It's the easiest/lowest-effort "modern look" path since it's a drop-in wrapper around stdlib Tkinter (same `pip install`-free-runtime story on most platforms). Trade-off: its table/grid widget support is far weaker than Qt's `QTableView`, so building a real sortable/filterable/diff-highlighted comparison grid will be more manual work, and packaging with PyInstaller is less battle-tested than PySide6's. Reasonable choice only if minimizing rewrite scope matters more than table UX. |
| PySide6 | Flet 1.0.1 | If you want the most visually modern (Flutter-rendered) UI with minimal Qt-style boilerplate, and don't mind a heavier/newer toolchain. Flet just hit 1.0 in September 2026 — very recent stabilization, smaller desktop-packaging track record, and its "compile to native" story (`flet build`) pulls in the Flutter SDK, which is a much bigger and more failure-prone build dependency than PyInstaller+Qt for a small team shipping to both macOS and Windows. Revisit in a future milestone once 1.x has more packaging mileage. |
| PyInstaller | Nuitka 4.2.2 | If startup time or binary reverse-engineering resistance becomes a real concern (Nuitka compiles to C then a native binary, ~2-4x faster runtime for compute-heavy code, harder to decompile). This app is I/O-bound (file parsing, network), not compute-bound, so Nuitka's performance edge doesn't matter much here; PyInstaller's faster build iteration and broader/more mature hook coverage for PySide6 + `zeroconf` + `websockets` matters more during active development. |
| PyInstaller | Briefcase 0.4.5 (BeeWare) | If you want fully native installers (`.app`/`.dmg`, MSI) with app-store-style packaging conventions out of the box. Briefcase's packaging story is most mature for its own **Toga** widget toolkit — using it with PySide6 is a secondary, less-traveled path. Reasonable to revisit for a later "proper installer" polish pass, but adds tooling complexity for this milestone's first standalone-build cut. |
| `pygdtf`/`pymvr` (open-stage) | Hand-rolled MVRxchange fork | There is nothing to fork — `mvrdevelopment/tools` contains no parsing code (see correction above). Do not attempt to vendor code from that repo expecting a parser; use the schemas only if you want XML schema validation. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|--------------|
| PyQt6 | GPL-licensed by default (commercial license required to ship closed-source or avoid GPL obligations); functionally near-identical to PySide6 for this app's needs | PySide6 (LGPL, free to ship, official Qt binding) |
| Raw Tkinter (undecorated) as the long-term UI layer | Ships with Python so it's "free," but has no answer for the "modernized UI" requirement without heavy custom styling, and its table widget (`ttk.Treeview`) is far weaker than Qt's model/view system for a diff-highlighted comparison grid with search/filter | PySide6, or CustomTkinter if a lighter migration is preferred |
| `pyqtdarktheme` | Last released December 2022, explicitly capped at `python<3.12` in its own metadata — effectively unmaintained and will block you from newer Python | `qt-material` or `PySide6-Fluent-Widgets` |
| Writing your own MVR-xchange TCP/WS client from scratch, from the DIN SPEC alone | DIN SPEC 15801:2023-12 is a paywalled standard, and the wire protocol has undocumented edge cases (the GDTF Hub team wrote an entire blog post reverse-engineering it with Wireshark) | Study/port the reference implementation split across `open-stage/blender-dmx`'s `mvrx_protocol.py` / `mvrx_tcp_client.py` / `mvrx_tcp_server.py` / `mvrx_ws_client.py` / `mvrx_message.py` (GPLv3 — license-compatible with this free community tool, but confirm you're comfortable with GPLv3 obligations if you port substantial code) |
| Cross-compiling a single PyInstaller build for both OSes | PyInstaller (and Nuitka, and Briefcase) all build for the host OS they run on — there is no reliable cross-compile path from macOS to Windows or vice versa | Build on both OSes separately, ideally via CI matrix (GitHub Actions `macos-latest` + `windows-latest`) |
| Dear PyGui | Built for immediate-mode, real-time/plotting/game-dashboard UIs; awkward fit for a form-and-table-heavy "select files, compare, export" business app | PySide6 |

## Stack Patterns by Variant

**If minimizing rewrite risk is the priority over UI polish:**
- Use CustomTkinter over the existing Tkinter code
- Because it reuses widget layout patterns from `BEtheLD` almost directly, at the cost of a weaker table/grid experience for the diff view

**If the MVR-xchange network requirement turns out to be a stretch goal for this milestone:**
- Ship file-based comparison (pygdtf/pymvr parsing + PySide6 UI + PyInstaller packaging) first, and treat the network sync (`zeroconf`+`websockets`+ported protocol modules) as its own later phase
- Because the network protocol has the least documentation/highest research risk of everything in this milestone (MEDIUM/LOW confidence — see Gaps), while the parsing+UI+packaging work is well-trodden with HIGH-confidence library choices

**If GDTF-Share (online fixture library browsing/download) is wanted later:**
- Use the REST API documented in `mvrdevelopment/tools/GDTF_Share_API/`
- Because that's a separate, simpler HTTP API (not the MVR-xchange peer protocol) for pulling fixture files from the public GDTF-Share database — out of scope for this milestone's requirements but a natural future differentiator

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|------------------|-------|
| PySide6 6.11.2 | Python `>=3.10,<3.15` | Sets the practical Python ceiling for this stack; don't jump to 3.15 when it lands until PySide6 catches up |
| `websockets` 17.1 | Python `>=3.11` | Sets the practical Python floor — combined with PySide6's ceiling, target Python 3.11 or 3.12 |
| `zeroconf` 0.151.3 | Python `>=3.10` | Compatible with the 3.11/3.12 target |
| `pygdtf` 1.4.5 / `pymvr` 1.0.7 | Python `>=3.8`, zero runtime deps | Will not constrain the floor/ceiling chosen above; also means PyInstaller bundling is simple (no compiled extensions to worry about) |
| `qt-material` 2.17 | PySide6 or PyQt, Python `>=3.7` | No conflicts expected |
| `pytest-qt` 4.5.0 | Python `>=3.9`, needs a Qt binding installed (PySide6 satisfies this) | Fine alongside existing `pytest` |
| PyInstaller 6.22.3 | Python `<3.16,>=3.8` | Comfortably covers the recommended 3.11/3.12 target |

## Sources

- PyPI JSON API (`https://pypi.org/pypi/<package>/json`) — direct registry queries for `pygdtf`, `pymvr`, `PySide6`, `customtkinter`, `flet`, `pyinstaller`, `nuitka`, `briefcase`, `toga`, `websockets`, `zeroconf`, `qt-material`, `PySide6-Fluent-Widgets`, `pyqtdarktheme`, `qtawesome`, `lxml`, `pytest-qt` — HIGH confidence (first-party registry metadata, fetched 2026-09-25).
- `https://github.com/mvrdevelopment/tools` (fetched directly) — confirms repo contents are XSD schemas + Wireshark dissector + GDTF-Share API docs, no parsing library. HIGH confidence (primary source, directly read).
- `https://raw.githubusercontent.com/open-stage/python-gdtf/master/pyproject.toml` and `https://raw.githubusercontent.com/open-stage/python-mvr/main/pyproject.toml` (fetched directly) — confirms zero runtime dependencies, Python `>=3.8`. HIGH confidence (primary source).
- `https://raw.githubusercontent.com/open-stage/blender-dmx/main/mvrx_protocol.py` (fetched directly) — MVR-xchange message types (`MVR_JOIN_RET`, `MVR_REQUEST`, `MVR_COMMIT`, etc.), TCP+WebSocket dual-transport design, `StationUUID`/`FileUUID` model. MEDIUM confidence (real reference implementation, but this is a Blender-addon-embedded module, not a documented standalone library, and the module's port numbers / mDNS service-type string were not confirmed — see Gaps).
- `https://www.gdtf.eu/blog/exploring-mvr-xchange-protocol-with-wireshark/` — confirms TCP-mode JSON message fields (`OK`, `Provider`, `verMinor`/`verMajor`, `Commits`, `Files`, `StationUUID`, `FileUUID`, `FromStationUUID`) and that the wire protocol needed active reverse-engineering by the GDTF Hub team themselves. MEDIUM confidence (secondary source, but from the GDTF standard's own community blog).
- `https://app-help.vectorworks.net/2026/eng/VW2026_Guide/LightingDesign1/Collaborating_with_MVR-xchange.htm` and related MA Lighting/Vectorworks help pages (via web search synthesis) — confirms mDNS-then-WebSocket architecture for the internet mode, and that MVR-xchange is specified in DIN SPEC 15801:2023-12, jointly developed by MA Lighting and the wider industry, supported by grandMA3/Vectorworks/BlenderDMX/Production Assist/Zactrack. MEDIUM confidence (web search synthesis across multiple vendor doc pages, not independently fetched/verified line-by-line).
- Web search synthesis (`pythonguis.com`, `pistack.xyz` "Python GUI Frameworks in 2026" article, general 2026 Python packaging comparison articles) for GUI-framework and packaging-tool positioning/trends. MEDIUM confidence (cross-checked across multiple independent articles, consistent conclusions; used for qualitative framework positioning, not for any version numbers — those came from PyPI directly).

---
*Stack research for: GDTF/MVR fixture comparison desktop app (Python, PySide6, MVR-xchange integration)*
*Researched: 2026-09-25*
