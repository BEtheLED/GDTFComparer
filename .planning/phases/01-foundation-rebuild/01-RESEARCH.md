# Phase 1: Foundation Rebuild - Research

**Researched:** 2026-09-25
**Domain:** Python desktop app rebuild — PySide6 GUI, pygdtf-based GDTF parsing, decoupled service layer, hardened XML/ZIP input
**Confidence:** MEDIUM-HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Rebuild on PySide6 (Qt for Python) instead of Tkinter/CustomTkinter — chosen for its mature `QTableView`/model-view widgets needed for Phase 2's sortable/filterable/diff-highlighted comparison grid, LGPL licensing (free to ship), and mature PyInstaller hooks for Phase 4 packaging. — **Reversibility:** one-way.
- **D-02:** Target Python 3.11+ as the floor (not the previously stated 3.7+) — required by the full research-recommended stack (PySide6 6.11.x needs ≥3.10, `websockets` 17.x needs ≥3.11 for Phase 5, `zeroconf` needs ≥3.10). — **Reversibility:** costly.
- **D-03:** Full rewrite from scratch rather than incrementally porting `BEtheLD` — the framework swap (Tkinter → PySide6) and parser swap (hand-rolled → pygdtf) mean most existing code doesn't carry over directly.
- **D-04:** Proper package layout (e.g. separate `core`/service package + `gui` package + `tests/`) instead of a single script — directly supports UI-02 and gives Phase 2/3 clean places to add code.
- **D-05:** Use `qt-material` for theming — a flat Material-Design-style reskin applied in ~2 lines, satisfying UI-01 without restructuring the UI around a heavier widget-replacement library.
- **D-06:** Theme follows the OS's light/dark setting rather than a fixed default. Requires wiring qt-material's theme switching to the OS preference at startup (and ideally on change).
- **D-07:** No specific visual reference supplied — Claude has discretion to pick a clean, professional accent color/theme variant within qt-material's options that fits a lighting/AV tool.
- **D-08:** Polish bar for Phase 1 is a "functional modern baseline" — apply qt-material theming and clean layout, but don't over-invest in custom styling/icons yet.
- **D-09:** The service/parsing layer wraps pygdtf's actual GDTF object model directly (fixture types, DMX modes, geometries, wheels, etc.) rather than flattening everything into a plain dict. — **Reversibility:** costly.
- **D-10:** Phase 1 keeps displaying only the current two categories (Beam, Physical Properties) in the UI, even though the underlying model now exposes the full attribute set.
- **D-11:** Attribute name collisions are fixed by namespacing each attribute by its full element path/context (e.g. which geometry or DMX channel it belongs to), mirroring pygdtf's own structured model.
- **D-12:** No separate GDTF schema/structure pre-validation layer in Phase 1 — rely on pygdtf's own parsing errors and catch those exceptions for a friendly error message (RELI-01). RELI-02's `defusedxml`/size-limit guarding still applies independently as a security measure, not as structural pre-validation.
- **D-13:** The comparator/service layer's public API returns a `ComparisonResult` object (small dataclass/model) rather than raw dicts. — **Reversibility:** costly.
- **D-14:** GDTF parsing runs off the UI thread starting in Phase 1 (a QThread/worker for parse+compare), not deferred to a later phase.
- **D-15:** The service layer exposes a batch API — `compare(target, [files])` → one `ComparisonResult` covering all comparison files at once.
- **D-16:** The service/parsing/comparison layer lives in its own dedicated package (e.g. `core/`) from the start, importable and unit-testable independently of Qt.

### Claude's Discretion

- Exact accent color / qt-material theme variant (per D-07).
- Exact naming/keying scheme for attribute namespacing, as long as it follows pygdtf's structured model (per D-11 — user selected "Namespace by element path" as the approach but left exact scheme to Claude).

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within Phase 1 scope. No scope-creep items were raised during this discussion.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PARSE-01 | App parses GDTF files using `pygdtf` instead of hand-rolled flat extraction, preserving element path/namespace so same-named attributes don't collide | See "pygdtf Object Model" and "Attribute Namespacing Pattern" below — verified directly from pygdtf source that `BeamAngle`/`FieldAngle`/etc. live per-`GeometryBeam` node (collision-prone) and `Width`/`Height`/`Length` live per-`Model` (also collision-prone), confirming D-11's path-namespacing approach is necessary, not optional |
| UI-01 | Modernized, visually refreshed interface | See "Standard Stack" (qt-material) and "OS Theme Detection" — use PySide6's native `QStyleHints.colorScheme()`, no extra dependency needed |
| UI-02 | GUI layer decoupled from parsing/comparison logic via a service layer | See "Architecture Patterns" — `core/` package + QThread worker pattern |
| RELI-01 | Friendly error message (not a crash) for invalid GDTF/zip/malformed XML | See "Critical Pitfall: pygdtf Silently Swallows Malformed XML" — this is the single most important finding of this research; naive reliance on pygdtf's own exceptions (per D-12) will NOT catch malformed-XML cases, only bad-zip cases |
| RELI-02 | Guard against oversized/malicious zip/XML input using `defusedxml` and size limits | See "Don't Hand-Roll" and "Security Domain" — pygdtf itself uses raw `xml.etree.ElementTree` internally with no hardening, so the app must pre-validate before calling pygdtf |
</phase_requirements>

## Summary

Phase 1 replaces `BEtheLD`'s single-file Tkinter script with a layered Python application: a framework-agnostic `core/` package (pygdtf-backed parsing + comparison), a PySide6 `gui/` package that only talks to `core/` through a typed `ComparisonResult` API, and a QThread worker boundary so parsing never blocks the UI. The research here is grounded directly in pygdtf's actual source (fetched and read this session, not just training knowledge) because the project's two riskiest correctness requirements — RELI-01 (friendly errors) and PARSE-01 (no attribute collisions) — depend on exactly how pygdtf behaves internally, not just on its public README.

**Two findings materially change what "straightforward" looks like for this phase:**

1. **pygdtf does not raise on malformed XML.** Its internal `_find_root()` catches *any* exception from `ElementTree.fromstring()` (including `xml.etree.ElementTree.ParseError`) and silently substitutes a stub fixture (`Name="Original File Had Broken XML"`) instead of propagating the error. D-12 assumed "rely on pygdtf's own parsing errors... and catch those exceptions" — this only works for bad-zip cases (`zipfile.BadZipFile` is NOT caught by pygdtf and propagates normally); malformed-XML-inside-a-valid-zip needs its own detection path. The cleanest fix, which also satisfies RELI-02 in the same step, is to pre-parse `description.xml` with `defusedxml.ElementTree` *before* handing the file to pygdtf, and treat any parse failure there as the "invalid GDTF" error path.
2. **Both source categories the UI must keep (Beam, Physical Properties) are genuinely collision-prone in real GDTF files**, not just hypothetically: `BeamAngle`/`FieldAngle`/`PowerConsumption`/`LuminousFlux`/`ColorTemperature`/`BeamType` are attributes of `GeometryBeam` nodes, and a real fixture can have more than one `GeometryBeam` (multi-emitter fixtures); `Width`/`Height`/`Length` are attributes of `Model` nodes, and a real fixture typically has several `Model`s (one per 3D part — base, yoke, head, etc.). `Weight` is the outlier: it's a single fixture-level value (`fixture.properties.weight`), not per-geometry. The namespacing scheme (D-11) needs to handle "one value per fixture" and "N values per fixture, one per named element" as two distinct shapes.

**Primary recommendation:** Build a thin `core/repository.py` that pre-validates each GDTF zip with `defusedxml` + a zip-bomb ratio/size check, then calls `pygdtf.FixtureType(path)` for the real parse; build `core/models.py` around dataclasses that mirror pygdtf's tree structure (keyed by element path) rather than a flat dict; run both through a `QThread`-based worker invoked from the GUI; theme via `qt-material` with the theme name chosen at runtime from `QGuiApplication.styleHints().colorScheme()`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| GDTF zip/XML parsing (pygdtf wrapping) | Core/Domain (`core/`) | — | Must be GUI-independent and unit-testable per D-16; zero Qt imports |
| Input hardening (defusedxml, size limits) | Core/Domain (`core/`) | — | Same trust boundary as parsing — must run before pygdtf ever sees the bytes, and before the GUI is involved |
| Attribute comparison / diffing | Core/Domain (`core/`) | — | Pure function of two+ parsed fixture models → `ComparisonResult`; no UI concerns (D-13) |
| Background execution (thread management) | GUI (`gui/`, QThread boundary) | Core (worker callable) | The QThread/worker object lives in the GUI layer per Qt's threading model, but it calls into `core/` functions — `core/` itself stays synchronous and thread-agnostic (D-14) |
| File selection dialogs | GUI (`gui/`) | — | `QFileDialog` is a Qt widget concern |
| Comparison table rendering | GUI (`gui/`, `QAbstractTableModel`/`QTableView`) | — | Presentation of `ComparisonResult`, no parsing knowledge |
| Error presentation (friendly messages) | GUI (`gui/`) | Core (raises typed exceptions) | Core raises/returns structured error info; GUI decides how to show it (`QMessageBox`) — mirrors the existing anti-pattern fix already documented in ARCHITECTURE.md |
| Theming (qt-material + OS theme detection) | GUI (`gui/`, app composition root) | — | Purely a presentation-layer concern; `QStyleHints` is a Qt/GUI API |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PySide6 | 6.11.2 | GUI framework | `[VERIFIED: pip index versions PySide6]` — matches project-level `.planning/research/STACK.md` recommendation; official Qt-for-Python binding, LGPL |
| pygdtf | 1.4.5 | GDTF parsing | `[VERIFIED: pip index versions pygdtf]` — MIT-licensed (confirmed via reading `base_node.py` header this session), zero runtime deps, real object model with `.geometries`, `.dmx_modes`, `.wheels`, `.models`, `.properties` |
| defusedxml | 0.7.1 | Safe XML pre-parse for RELI-02 | `[VERIFIED: pip index versions defusedxml]` — this package was in project-level research's Sources list but NOT in its Supporting Libraries table; phase-level research fills that gap. Needed regardless of pygdtf because pygdtf's own internal parser (`xml.etree.ElementTree`) has no XXE/entity-expansion hardening `[VERIFIED: open-stage/python-gdtf __init__.py:32 — "from xml.etree import ElementTree"]` |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| qt-material | 2.17 | One-line Material theming | `[VERIFIED: pip index versions qt-material]` — apply at app composition root via `apply_stylesheet(app, theme=...)` |
| pytest | (existing, add via pyproject) | Unit tests for `core/` | Already used in repo; keep for `core/` package tests |
| pytest-qt | 4.5.0 | GUI widget/signal testing | `[VERIFIED: pip index versions pytest-qt]` — provides `qtbot` fixture; useful for QThread worker signal tests and basic widget smoke tests |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `defusedxml` pre-parse before pygdtf | Monkey-patching pygdtf's internal `ElementTree` import with `defusedxml.defuse_stdlib()` | defusedxml's own README explicitly warns against this: `[VERIFIED: tiran/defusedxml README.txt:308-312]` "`defuse_stdlib()` should be avoided. It can break third party package or cause surprising side effects." Pre-parsing our own copy of `description.xml` before calling pygdtf is safer and also gives us control over the "malformed XML" error path that pygdtf itself swallows |
| `QStyleHints.colorScheme()` for OS theme detection | `darkdetect` package | `darkdetect` is a legitimate, small (`[ASSUMED]` — discovered via WebSearch, not independently verified against an authoritative source) third-party package that works down to older Qt/Tk versions, but PySide6 6.11.2 already has this built in natively since Qt 6.5 (`[VERIFIED: doc.qt.io/qt-6/qstylehints.html` — `colorScheme` property "since 6.5", plus a `colorSchemeChanged` signal for D-06's "ideally on change" requirement). Prefer the built-in — one fewer dependency to package/verify |

**Installation:**
```bash
pip install PySide6==6.11.2 pygdtf==1.4.5 defusedxml==0.7.1 qt-material==2.17
pip install -D pytest pytest-qt==4.5.0
```

**Version verification:** Verified 2026-09-25 via `pip3 index versions <package>` directly against PyPI — all versions match `.planning/research/STACK.md`'s prior project-level verification (also 2026-09-25), confirming currency. `defusedxml` is pinned at 0.7.1, its latest version (last released 2021-03-08 — stable, feature-complete, no newer release exists).

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| PySide6 | PyPI | published 2026-08-18 (this version) | unknown (checker limitation) | https://pyside.org | SUS (`unknown-downloads` only) | Approved — official Qt Company package; STACK.md already deep-verified this at project level |
| pygdtf | PyPI | published 2026-03-31 | unknown (checker limitation) | none listed on PyPI metadata | SUS (`unknown-downloads`, `no-repository`) | Approved — real repo is `github.com/open-stage/python-gdtf`, confirmed by directly fetching and reading its source this session (MIT license header read at `base_node.py`); PyPI metadata simply omits the repo URL field |
| defusedxml | PyPI | published 2021-03-08 | unknown (checker limitation) | https://github.com/tiran/defusedxml | SUS (`unknown-downloads` only) | Approved — long-standing, widely-used security package; README fetched and read directly this session |
| qt-material | PyPI | published 2025-04-21 | unknown (checker limitation) | https://github.com/dunderlab/qt-material | SUS (`unknown-downloads` only) | Approved — already vetted at project level in STACK.md |
| pytest-qt | PyPI | published 2025-07-01 | unknown (checker limitation) | http://github.com/pytest-dev/pytest-qt | SUS (`unknown-downloads` only) | Approved — maintained under the `pytest-dev` GitHub org, the same org that owns `pytest` itself |

**Packages removed due to `[SLOP]` verdict:** none.
**Packages flagged as suspicious `[SUS]`:** All five packages above returned `SUS` from the legitimacy checker, but in every case the sole reason is `unknown-downloads` (the checker has no PyPI download-count signal available in this environment) — not a red flag on its own. `pygdtf` additionally flagged `no-repository` because PyPI's project metadata omits the repo URL field, but the real source (`github.com/open-stage/python-gdtf`) was independently confirmed by fetching and reading it directly this session. None of these are new/unknown packages: all were previously vetted at the project level in `.planning/research/STACK.md` (fetched via PyPI JSON API, GitHub `pyproject.toml`) except `defusedxml`, which is vetted here directly. **The planner should still add a single `checkpoint:human-verify` task before the initial `pip install` step**, per protocol, since the automated checker could not independently confirm download volume for any of these five packages in this environment — this is a one-time gate, not a sign of specific risk.

## Architecture Patterns

### System Architecture Diagram

```text
┌─────────────────────────────────────────────────────────────────────┐
│                         gui/ (PySide6)                                │
│  MainWindow — file pickers, "Run Comparison" button, results table   │
└───────────────┬─────────────────────────────────────┬─────────────────┘
                │ (1) user picks target + N compare      │ (6) ComparisonResult
                │     files, clicks "Run Comparison"      │     or error → render
                ▼                                         │
┌─────────────────────────────────┐                       │
│   ComparisonWorker (QObject)     │                       │
│   moveToThread(QThread)          │───────────────────────┘
│   .run() calls core.compare()    │
│   emits finished(result) /       │
│   emits failed(error_message)    │
└───────────────┬───────────────────┘
                │ (2) calls into core/ (plain Python call,
                │     no Qt imports on this side)
                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         core/ (framework-agnostic)                    │
│                                                                        │
│  (3) repository.load(path)                                            │
│      ├─ size check (file size limit)                                  │
│      ├─ zip-bomb ratio check (uncompressed/compressed size)           │
│      ├─ defusedxml.ElementTree pre-parse of description.xml           │
│      │     → raises GDTFParseError on malformed XML (RELI-01 fix)     │
│      └─ pygdtf.FixtureType(path) → real object model                  │
│            (geometries, dmx_modes, wheels, models, properties)        │
│                                                                        │
│  (4) FixtureModel.from_pygdtf(fixture_type)                           │
│      walks .geometries tree + .models list, builds namespaced         │
│      attribute keys (element path → value)                            │
│                                                                        │
│  (5) comparator.compare(target: FixtureModel,                         │
│                          comparisons: list[FixtureModel])              │
│      → ComparisonResult (target + per-file diffs, still keyed          │
│        by namespaced path, not flat attribute name)                   │
└─────────────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure
```
src/
├── core/                    # framework-agnostic domain layer (D-16)
│   ├── __init__.py
│   ├── errors.py            # GDTFParseError, GDTFValidationError, etc.
│   ├── hardening.py         # size limits, zip-bomb ratio check, defusedxml pre-parse
│   ├── repository.py        # FixtureRepository.load(path) -> FixtureModel
│   ├── models.py            # FixtureModel, ComparisonResult dataclasses
│   └── comparator.py        # compare(target, [comparisons]) -> ComparisonResult
├── gui/                     # PySide6 presentation layer
│   ├── __init__.py
│   ├── main_window.py       # MainWindow (file pickers, results table)
│   ├── worker.py            # ComparisonWorker(QObject) + QThread wiring
│   ├── table_model.py       # ComparisonTableModel(QAbstractTableModel)
│   └── theme.py             # qt-material apply + QStyleHints OS-theme wiring
├── app.py                   # composition root: builds QApplication, MainWindow, wires layers
tests/
├── core/
│   ├── test_repository.py   # replaces tests/test_parse_gdtf.py's role
│   ├── test_hardening.py    # malformed-XML / zip-bomb / oversized-file cases
│   └── test_comparator.py   # namespacing / collision-avoidance assertions
└── gui/
    └── test_main_window.py  # pytest-qt smoke tests
pyproject.toml                # NEW — pins all deps; repo currently has none (CONCERNS.md gap)
```

### Pattern 1: Pre-Validation Before pygdtf (closes the RELI-01/RELI-02 gap)
**What:** Before calling `pygdtf.FixtureType(path)`, open the zip yourself, check file size and compression ratio, extract `description.xml`, and parse it with `defusedxml.ElementTree.fromstring()`. Only call pygdtf if that pre-parse succeeds.
**When to use:** Every GDTF file load, local files only in Phase 1 (network-sourced files are Phase 5's concern, per D-12's framing of RELI-02 as independent of structural validation).
**Why required (not optional):** verified this session that pygdtf's own malformed-XML handling silently returns a stub fixture rather than raising — see Common Pitfalls below. Without this pre-validation step, RELI-01's "friendly error message" success criterion cannot be met for malformed-XML files; the app would instead silently show a fake, empty-looking fixture named "Original File Had Broken XML" with no user-visible error at all.
```python
# core/hardening.py
import zipfile
import defusedxml.ElementTree as DET

MAX_FILE_SIZE = 100 * 1024 * 1024      # 100 MB, per CONCERNS.md's own suggested limit
MAX_COMPRESSION_RATIO = 100             # reject if uncompressed/compressed > 100x

class GDTFValidationError(Exception):
    """Raised when a .gdtf file fails pre-validation before parsing."""

def validate_and_extract_description(path: str) -> str:
    with zipfile.ZipFile(path, "r") as zf:
        total_compressed = sum(i.compressed_size for i in zf.infolist())
        total_uncompressed = sum(i.file_size for i in zf.infolist())
        if total_compressed and total_uncompressed / total_compressed > MAX_COMPRESSION_RATIO:
            raise GDTFValidationError("File failed a compression-ratio safety check.")
        try:
            with zf.open("description.xml") as f:
                xml_bytes = f.read()
        except KeyError:
            raise GDTFValidationError("No description.xml found in this GDTF file.")
    try:
        DET.fromstring(xml_bytes)   # raises on XXE/entities/malformed XML
    except Exception as exc:
        raise GDTFValidationError(f"description.xml is not valid XML: {exc}") from exc
    return xml_bytes.decode("utf-8")
```
*(Sizes/limits are `[ASSUMED]` reasonable defaults inherited from CONCERNS.md's own suggestion — not independently benchmarked against real-world GDTF file sizes this session; flag for confirmation if very large real fixture libraries are expected.)*

### Pattern 2: QThread Worker for Non-Blocking Parse+Compare (D-14)
**What:** A `QObject` subclass holding the actual `compare()` call, moved to a `QThread` via `moveToThread()`, communicating results back via signals.
**When to use:** Every "Run Comparison" click.
**Example:**
```python
# Source: doc.qt.io/qtforpython-6/PySide6/QtCore/QThread.html pattern (WebSearch-corroborated,
# standard Qt worker-object pattern) [CITED: doc.qt.io/qtforpython-6]
from PySide6.QtCore import QObject, QThread, Signal

class ComparisonWorker(QObject):
    finished = Signal(object)   # ComparisonResult
    failed = Signal(str)        # friendly error message

    def __init__(self, target_path: str, compare_paths: list[str]):
        super().__init__()
        self.target_path = target_path
        self.compare_paths = compare_paths

    def run(self):
        from core.repository import FixtureRepository
        from core.comparator import compare
        from core.errors import GDTFValidationError
        try:
            repo = FixtureRepository()
            target = repo.load(self.target_path)
            comparisons = [repo.load(p) for p in self.compare_paths]
            result = compare(target, comparisons)
            self.finished.emit(result)
        except GDTFValidationError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # zipfile.BadZipFile etc. propagate here (D-12)
            self.failed.emit(f"Could not read this file: {exc}")

# In MainWindow:
def run_comparison(self):
    self.thread = QThread()
    self.worker = ComparisonWorker(self.target_file, self.compare_files)
    self.worker.moveToThread(self.thread)
    self.thread.started.connect(self.worker.run)
    self.worker.finished.connect(self.on_result)
    self.worker.failed.connect(self.on_error)
    self.worker.finished.connect(self.thread.quit)
    self.worker.failed.connect(self.thread.quit)
    self.thread.start()
```

### Pattern 3: Namespaced Attribute Keys (D-11)
**What:** Instead of `{attr_name: value}`, key attributes by their element path, mirroring pygdtf's own nested structure.
**When to use:** Building `FixtureModel` from a parsed `pygdtf.FixtureType`.
**Verified structural basis** `[VERIFIED: open-stage/python-gdtf geometries.py:516-557, __init__.py:1279-1318, properties.py:31-44]`:
- `GeometryBeam` nodes carry `.beam_angle`, `.field_angle`, `.power_consumption`, `.luminous_flux`, `.color_temperature`, `.beam_type` — **one set of values per `GeometryBeam` node**, and a fixture's `.geometries` tree can contain more than one.
- `Model` nodes carry `.length`, `.width`, `.height` — **one set of values per named `Model`**, and `.models` is a list.
- `Properties` (on `FixtureType.properties`) carries `.weight` — a **single fixture-level value**, no path needed.
```python
# core/models.py — illustrative shape, exact scheme is Claude's discretion per D-11's "Claude's Discretion" note
@dataclass
class FixtureModel:
    name: str
    # keyed by "GeometryPath/AttrName", e.g. "Head1/Beam1/BeamAngle"
    beam_attrs: dict[str, float]
    # keyed by "ModelName/AttrName", e.g. "HeadModel/Width"
    physical_attrs: dict[str, float]
    weight: float  # single value, no namespacing needed
```

### Anti-Patterns to Avoid
- **Flattening pygdtf's tree back into `{attr_name: value}`:** reintroduces the exact collision bug this phase exists to fix (multiple `GeometryBeam`/`Model` nodes would overwrite each other's `BeamAngle`/`Width` under a flat key) — this is D-09's explicit rationale for wrapping the real object model.
- **Trusting `zipfile.ZipInfo.file_size` alone for zip-bomb detection:** this header can be forged by a malicious zip; the ratio check above is a reasonable heuristic but is not airtight (`[ASSUMED]` — standard mitigation used broadly, not a formal guarantee; acceptable for a niche desktop tool's threat model per RELI-02's scope).
- **Calling `pygdtf.FixtureType()` directly from GUI code:** violates UI-02 and D-16; all pygdtf imports must live inside `core/`.
- **Using `defusedxml.defuse_stdlib()` monkey-patching to harden pygdtf's internals:** defusedxml's own README explicitly warns this is "untested" and can break third-party packages `[VERIFIED: tiran/defusedxml README.txt:305-312]`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|--------------|-----|
| GDTF zip/XML parsing | Custom `zipfile` + `ElementTree` walk (the current `BEtheLD` approach) | `pygdtf.FixtureType` | Spec-correct, actively maintained, already handles the full GDTF 1.2 object model (geometries, DMX modes, wheels, physical descriptions) |
| XXE/entity-expansion protection | Manual XML sanitization or regex pre-filtering | `defusedxml.ElementTree` | Purpose-built, actively maintained, correctly raises typed exceptions (`EntitiesForbidden`, `ExternalReferenceForbidden`) `[VERIFIED: tiran/defusedxml README.txt:318-329]` |
| OS dark/light mode detection | Platform-specific `ctypes`/registry/`defaults read` calls, or a third-party package | `QGuiApplication.styleHints().colorScheme()` + `colorSchemeChanged` signal | Built into the exact Qt version already being installed (PySide6 6.11.2, feature added in Qt 6.5) `[VERIFIED: doc.qt.io/qt-6/qstylehints.html]` — zero extra dependency |
| Cross-thread result delivery | Manual locks/queues between a `threading.Thread` and the Tkinter/Qt main loop | Qt's `Signal`/`Slot` queued-connection mechanism | Thread-safe by construction when a `QObject` worker is moved to a `QThread`; this is the documented, idiomatic Qt pattern `[CITED: doc.qt.io/qtforpython-6/PySide6/QtCore/QThread.html]` |
| Comparison table widget | Hand-rolled grid via nested Tkinter frames or a raw `QTableWidget` filled cell-by-cell | `QAbstractTableModel` + `QTableView` | Model/view separation scales to Phase 2's sort/filter/highlight needs without a rewrite; `QTableWidget` would need to be replaced later anyway |

**Key insight:** Every "don't hand-roll" item above maps to a Phase 1 requirement (PARSE-01→pygdtf, RELI-02→defusedxml, UI-01/D-06→QStyleHints, UI-02/D-14→Signal/Slot, UI-01→QAbstractTableModel). None of these are exotic choices — they're the standard tool for each specific job, verified directly against source/docs rather than assumed from general Qt/Python familiarity.

## Common Pitfalls

### Pitfall 1: pygdtf Silently Swallows Malformed XML (verified this session — HIGH-impact)
**What goes wrong:** A `.gdtf` file that is a valid zip but contains malformed `description.xml` does not raise any exception from `pygdtf.FixtureType(path)`. Instead, the fixture object is populated with a stub: `Name="Original File Had Broken XML"`, empty everything else.
**Why it happens:** `pygdtf`'s internal `_find_root()` function wraps `ElementTree.fromstring()` in `try: ... except Exception as e: return ElementTree.fromstring(<hardcoded fallback XML>)` — a broad catch-and-replace, not a catch-and-reraise `[VERIFIED: open-stage/python-gdtf __init__.py:88-112]`.
**How to avoid:** Pre-parse `description.xml` yourself with `defusedxml.ElementTree.fromstring()` before ever calling `pygdtf.FixtureType()` (see Pattern 1 above). Treat any exception from that pre-parse as the RELI-01 "invalid file" error path. Do not rely on wrapping `pygdtf.FixtureType()` in a try/except for this case — it won't catch anything for malformed XML.
**Warning signs during implementation:** If a test feeds a `.gdtf` with deliberately malformed XML through `pygdtf.FixtureType()` directly and expects an exception, the test will fail (no exception raised) — this is expected behavior of the library, not a bug in the new code, and is exactly why the pre-validation step exists.

### Pitfall 2: `description.xml` Lookup Is Exact-Name, Not Case-Insensitive/Recursive
**What goes wrong:** pygdtf looks up the zip entry by the literal name `"description.xml"` via `zf.open("description.xml")` `[VERIFIED: open-stage/python-gdtf __init__.py:92]`, unlike the current `BEtheLD` code which does a case-insensitive `os.walk()` across the whole extracted tree.
**Why it happens:** pygdtf assumes GDTF-spec-compliant zips, where `description.xml` is always at the archive root with that exact casing.
**How to avoid:** If a `.gdtf` file has `description.xml` in a different case or nested path (spec violation, but real-world files can be malformed), `zf.open("description.xml")` raises `KeyError`, which is NOT caught by pygdtf's internal try/except (that only wraps the XML-parse call, not the zip-open call) — it propagates normally and should be caught by the same layer catching `zipfile.BadZipFile`, both treated as "invalid GDTF file" for RELI-01.
**Warning signs:** A real-world `.gdtf` from an older export tool that used different casing would surface as an uncaught `KeyError` if the service layer's except clause only lists `zipfile.BadZipFile`/`GDTFValidationError` and not a broader catch.

### Pitfall 3: "Physical Properties" Category Spans Two Different Cardinalities
**What goes wrong:** Naively re-deriving the "Physical Properties" category (Weight, Width, Height, Length) from pygdtf's model can produce a broken comparison table if all four are treated as single scalar values.
**Why it happens:** `Weight` is fixture-level (`fixture.properties.weight`, one value) but `Width`/`Height`/`Length` are per-`Model` (`fixture.models[i].width/.height/.length`, potentially several values if the fixture has multiple 3D model parts) `[VERIFIED: open-stage/python-gdtf properties.py:31-44, __init__.py:1279-1318]`.
**How to avoid:** Design `FixtureModel`'s physical-properties shape to explicitly separate the single `weight` scalar from a `{model_name: {width, height, length}}` mapping (see Pattern 3 dataclass sketch). Decide (Claude's discretion, per D-11) how to display multiple models in the Phase 1 UI — e.g., one row per model, or aggregate/first-model-only with a note — but do not silently drop or overwrite extra models.
**Warning signs:** A GDTF file with more than one `<Model>` element producing a comparison table that only shows dimensions for one of them with no indication others exist.

### Pitfall 4: Threading + Qt Widget Access From the Worker Thread
**What goes wrong:** Touching any `QWidget` (e.g., `self.tree_view.setModel(...)`) directly from inside `ComparisonWorker.run()` (which executes on the background `QThread`) causes undefined behavior/crashes — Qt widgets are not thread-safe.
**Why it happens:** Easy mistake when porting synchronous logic into a worker — the temptation is to just call the UI-update code inline instead of emitting a signal.
**How to avoid:** The worker must only emit `Signal`s (`finished`, `failed`); all widget mutation happens in slots connected to those signals, which Qt automatically marshals back onto the GUI thread via queued connections `[CITED: doc.qt.io/qtforpython-6/PySide6/QtCore/QThread.html]`.
**Warning signs:** Segfaults or "QObject: Cannot create children for a parent that is in a different thread" warnings during manual testing.

## Code Examples

### OS Theme Detection + qt-material Wiring (D-06)
```python
# gui/theme.py
# Source: doc.qt.io/qt-6/qstylehints.html (colorScheme property, since Qt 6.5) [VERIFIED]
from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import Qt
from qt_material import apply_stylesheet

LIGHT_THEME = "light_teal.xml"   # exact accent color is Claude's discretion (D-07)
DARK_THEME = "dark_teal.xml"

def apply_os_theme(app):
    def _pick_and_apply(scheme):
        theme = DARK_THEME if scheme == Qt.ColorScheme.Dark else LIGHT_THEME
        apply_stylesheet(app, theme=theme)

    hints = app.styleHints()
    _pick_and_apply(hints.colorScheme())
    hints.colorSchemeChanged.connect(_pick_and_apply)  # D-06 "ideally on change"
```

### pygdtf Loading (verified constructor + attribute access)
```python
# Source: open-stage/python-gdtf __init__.py:115-131 [VERIFIED], README (WebSearch) [CITED]
import pygdtf

fixture = pygdtf.FixtureType(path="example.gdtf")   # raises zipfile.BadZipFile if not a zip
print(fixture.name)                                  # from FixtureType/@Name
print(fixture.dmx_modes[0].name)
print(fixture.dmx_modes[0].dmx_channels_count)
print(fixture.properties.weight)                     # single fixture-level value
for model in fixture.models:
    print(model.name, model.width, model.height, model.length)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| Hand-rolled `zipfile` + `ElementTree.iter()` flat-attribute walk (`BEtheLD`) | `pygdtf.FixtureType` structured object model | This phase | Fixes attribute collision bug (roadmap success criterion #2); adds ~zero runtime deps |
| Tkinter `ttk.Treeview` | PySide6 `QTableView` + `QAbstractTableModel` | This phase | Enables Phase 2's sort/filter/highlight without another framework swap |
| Synchronous parse on the UI thread | `QThread` worker + signals | This phase | Fixes UI-freeze scaling limit noted in CONCERNS.md |
| No dependency pinning (`.planning/codebase/CONCERNS.md` "Missing Dependency Management") | `pyproject.toml` with pinned versions | This phase | Reproducible installs; required groundwork for Phase 4 packaging |

**Deprecated/outdated:**
- Copy-then-extract via `tempfile.mkdtemp()` + `shutil.copyfile()` + `zipfile.extractall()`: unnecessary double I/O per CONCERNS.md; `zipfile.ZipFile` (and pygdtf itself) can read directly from the original file path with no extraction to disk at all for `description.xml` access.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|----------------|
| A1 | 100 MB file-size limit and 100x compression-ratio threshold are reasonable defaults for GDTF files | Pattern 1 / Code Examples | If real-world GDTF files (with embedded thumbnails/3D models) commonly exceed these, legitimate files could be rejected; these are inherited from CONCERNS.md's own suggestion, not independently benchmarked against a corpus of real GDTF files this session |
| A2 | `darkdetect` was considered and rejected in favor of `QStyleHints.colorScheme()` | Standard Stack / Alternatives Considered | Low risk — this is a "don't add it" recommendation, not a dependency being introduced; if `QStyleHints.colorScheme()` proves unreliable on a specific OS/Qt-theme-engine combination during implementation, `darkdetect` (PyPI, not independently verified this session) is the documented fallback |
| A3 | qt-material 2.17's specific `light_teal.xml`/`dark_teal.xml` theme names are current | Code Examples | If qt-material renamed/removed these exact theme files in 2.17, the `apply_stylesheet()` call would raise at startup — low risk, easily caught by manual smoke test, and any other bundled theme name is a one-line fix |
| A4 | GDTF real-world files always use exactly-cased `description.xml` at the zip root (per current pygdtf behavior) | Pitfall 2 | If a meaningful fraction of real fixture files in the wild don't comply, more users will hit the "invalid file" error path than expected; mitigation (catching the resulting `KeyError` as a friendly error) already covers this even if the assumption about prevalence is wrong |

**If this table is empty:** N/A — see above; all other claims in this research were verified directly against pygdtf/defusedxml/Qt source or documentation fetched and read this session.

## Open Questions

1. **Exact attribute-path key format for namespacing (D-11's "Claude's discretion")**
   - What we know: pygdtf exposes a real tree (`Geometry.geometries` recursive list) and flat lists (`models`, `wheels`) that can be walked to build unique keys.
   - What's unclear: Whether the planner should key by full geometry path (`"Head/Beam1/BeamAngle"`) or by a shorter unique-enough identifier (`"Beam1/BeamAngle"`) — GDTF's `get_geometry_tree()` helper (mentioned in pygdtf's README, not independently verified this session) may offer a ready-made path-building utility worth investigating during planning.
   - Recommendation: Planner should budget a small investigation task to check whether `pygdtf.utils.get_geometry_tree()` (referenced in the README `[CITED]`, not read directly this session) already produces path strings, before hand-rolling a path-builder in `core/models.py`.

2. **How many `Model` entries does a typical real GDTF file have, and how should Phase 1's UI show more than one?**
   - What we know: The pygdtf object model supports N models per fixture (Pitfall 3).
   - What's unclear: Real-world distribution — is one model common, or do most professional fixtures ship 3-5+?
   - Recommendation: Use a small real `.gdtf` sample (from a manufacturer, or GDTF-Share) during Phase 1 implementation/testing to see real-world shape before finalizing the display scheme; not blocking for planning, since the dataclass shape already accounts for N models.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python interpreter | Entire phase | ✓ | 3.14.6 (`/opt/miniconda3/bin/python3`) | — within D-02's floor (3.11+) and PySide6 6.11.2's ceiling (<3.15), but close to the ceiling — see note below |
| pip | Package installs | ✓ | present (used for `pip3 index versions` checks this session) | — |
| PySide6 | GUI | ✗ (not installed) | — | Install step required in Phase 1 plan; no fallback needed, this is the first install |
| pygdtf | Parsing | ✗ (not installed) | — | Install step required |
| defusedxml | Hardening | ✗ (not installed) | — | Install step required |
| qt-material | Theming | ✗ (not installed) | — | Install step required |
| pytest-qt | Testing | ✗ (not installed) | — | Install step required |
| `pyproject.toml` / dependency pinning file | Reproducible installs | ✗ (does not exist in repo) | — | Must be created this phase — CONCERNS.md already flags this gap |

**Missing dependencies with no fallback:** None — all five packages are new installs with no existing partial state to reconcile; this is a clean install situation, not a broken environment.

**Note on Python version:** The active interpreter (3.14.6, via conda's `base` env) is right at the edge of PySide6 6.11.2's documented ceiling (`>=3.10,<3.15` per `.planning/research/STACK.md`). This is currently compatible but leaves little headroom before the next CPython release would require a PySide6 upgrade to keep working. Recommend the Phase 1 plan create an isolated virtual environment (not relying on the conda `base` env) pinned via `pyproject.toml`, both for hygiene and to decouple this project's Python version from whatever the system/conda default happens to be.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (already used for `tests/test_parse_gdtf.py`) + pytest-qt 4.5.0 (new, for GUI/worker tests) |
| Config file | none — see Wave 0 Gaps (needs a `pyproject.toml` `[tool.pytest.ini_options]` section or `pytest.ini`) |
| Quick run command | `pytest tests/core -x` (core logic only, fast, no Qt event loop needed) |
| Full suite command | `pytest tests/` (includes `tests/gui`, requires a display/`QT_QPA_PLATFORM=offscreen` in CI) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PARSE-01 | Same-named attributes from different geometries/models don't collide | unit | `pytest tests/core/test_comparator.py::test_no_attribute_collision -x` | ❌ Wave 0 |
| PARSE-01 | pygdtf-backed load returns a structured `FixtureModel` | unit | `pytest tests/core/test_repository.py::test_load_valid_gdtf -x` | ❌ Wave 0 |
| RELI-01 | Malformed XML inside a valid zip is caught before reaching pygdtf's silent-fallback behavior | unit | `pytest tests/core/test_hardening.py::test_malformed_xml_raises -x` | ❌ Wave 0 |
| RELI-01 | Invalid/non-zip file raises a catchable error | unit | `pytest tests/core/test_repository.py::test_invalid_zip_raises -x` | ❌ Wave 0 |
| RELI-02 | Oversized file / bad compression ratio is rejected before parsing | unit | `pytest tests/core/test_hardening.py::test_oversized_file_rejected -x` | ❌ Wave 0 |
| RELI-02 | XXE/entity-expansion payload is rejected | unit | `pytest tests/core/test_hardening.py::test_xxe_rejected -x` | ❌ Wave 0 |
| UI-02 | `gui/` package contains no direct `import pygdtf` or `import zipfile` | static/lint check | `grep -rn "import pygdtf\|import zipfile" src/gui/` (expect empty) | ❌ Wave 0 (can be a simple test asserting no such imports, or a code-review gate) |
| UI-01 | App launches with qt-material theme applied, no stock-Tkinter look | manual-only | Manual smoke test (justification: purely visual, no automatable "looks modern" assertion) | n/a |

### Sampling Rate
- **Per task commit:** `pytest tests/core -x`
- **Per wave merge:** `pytest tests/`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `pyproject.toml` with `[tool.pytest.ini_options]` (`testpaths = ["tests"]`) — no config file exists yet
- [ ] `tests/core/__init__.py`, `tests/gui/__init__.py` — new test package structure replacing the current single `tests/test_parse_gdtf.py`
- [ ] `tests/core/conftest.py` — shared fixtures for building minimal valid/malformed/oversized `.gdtf` zips in `tmp_path`, following the existing `build_gdtf_zip()` helper pattern already in `tests/test_parse_gdtf.py`
- [ ] Framework install: `pip install -D pytest-qt==4.5.0` — needed before any `tests/gui/` tests can run
- [ ] Decide fate of `tests/test_parse_gdtf.py` — it tests the old `BEtheLD.parse_gdtf()` function being removed this phase; should be deleted/replaced by `tests/core/test_repository.py`, not left dangling against dead code

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-------------------|
| V2 Authentication | No | Standalone desktop app, no accounts/login |
| V3 Session Management | No | No sessions |
| V4 Access Control | No | Single-user local desktop app |
| V5 Input Validation | Yes | `defusedxml` pre-parse + size/ratio checks on every GDTF file before pygdtf sees it (Pattern 1) |
| V6 Cryptography | No | No secrets, no data at rest requiring encryption in this phase |
| V10 Malicious Code | Yes | Zip-bomb ratio check; treat every selected file as untrusted input, including ones the user themselves picked (defense in depth against corrupted/malicious downloads) |
| V12 Files and Resources | Yes | File size limits before processing; read zip contents directly rather than extracting to a predictable temp path (also closes the CONCERNS.md "temp dir cleanup on error" and "no file size limits" gaps) |

### Known Threat Patterns for this Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|----------------------|
| XXE (external entity injection) via a crafted `description.xml` | Information Disclosure / Denial of Service | `defusedxml.ElementTree.fromstring()` with default `forbid_entities=True`, `forbid_external=True` `[VERIFIED: tiran/defusedxml README.txt:322-329]` |
| "Billion laughs" entity-expansion DoS | Denial of Service | Same `defusedxml` pre-parse — `forbid_entities=True` rejects any `<!ENTITY>` declaration outright, which also blocks entity-expansion bombs |
| Zip bomb (small file, huge decompressed size) | Denial of Service | Compression-ratio + total-uncompressed-size check before any extraction (Pattern 1); note the `[ASSUMED]` caveat in Anti-Patterns — header-based ratio checks are a heuristic, not airtight, but proportionate for this app's threat model |
| Path traversal via crafted zip entry names (`../../etc/passwd`-style) | Tampering | Phase 1 never calls `zf.extractall()` — only `zf.open("description.xml")` by exact known name, which sidesteps the entire "malicious entry path" class of zip attacks used by `extractall()`-based traversal exploits `[VERIFIED: open-stage/python-gdtf __init__.py:92 — zf.open("description.xml", "r")]` |

## Sources

### Primary (HIGH confidence)
- `pip3 index versions <package>` — direct PyPI registry queries for PySide6, pygdtf, defusedxml, qt-material, pytest-qt, run this session (2026-09-25/26)
- `https://raw.githubusercontent.com/open-stage/python-gdtf/master/pygdtf/__init__.py` — fetched and read directly this session; source of the `FixtureType.__init__`/`_find_root` malformed-XML-swallowing finding
- `https://raw.githubusercontent.com/open-stage/python-gdtf/master/pygdtf/geometries.py` — fetched and read directly; source of `GeometryBeam` attribute fields
- `https://raw.githubusercontent.com/open-stage/python-gdtf/master/pygdtf/properties.py` — fetched and read directly; source of `Properties.weight` single-value finding
- `https://raw.githubusercontent.com/open-stage/python-gdtf/master/pygdtf/base_node.py` — fetched and read directly; MIT license header confirmation
- `https://raw.githubusercontent.com/tiran/defusedxml/main/README.txt` — fetched and read directly; `forbid_dtd`/`forbid_entities`/`forbid_external` default values and exception names
- `https://doc.qt.io/qt-6/qstylehints.html` — fetched and read directly (raw HTML grepped); `colorScheme` property (since 6.5) and `colorSchemeChanged` signal
- `gsd-tools query package-legitimacy check --ecosystem pypi` — automated registry-signal check for all 5 new packages this session

### Secondary (MEDIUM confidence)
- WebSearch: pygdtf README/usage patterns (`FixtureType(dsc_file=...)`, `dmx_modes[0].dmx_channels_count`, `get_geometry_tree()` helper) — corroborates but was not independently read line-by-line for the `get_geometry_tree()` helper specifically (flagged in Open Questions)
- WebSearch: PySide6 `QThread`/`moveToThread()` worker pattern — corroborated across `doc.qt.io`, Real Python, pythontutorial.net; standard, extensively-documented Qt pattern
- WebSearch: PySide6 `QAbstractTableModel` required methods (`rowCount`, `columnCount`, `data`, `headerData`) — corroborated across `doc.qt.io` and pythonguis.com
- WebSearch: qt-material `apply_stylesheet()` usage and theme file naming convention — corroborated across the `dunderlab/qt-material` GitHub repo and readthedocs page
- `.planning/research/STACK.md`, `.planning/research/SUMMARY.md` — project-level research already completed 2026-09-25, re-confirmed rather than re-derived where overlapping

### Tertiary (LOW confidence)
- WebSearch: `darkdetect` package existence/API — considered and explicitly rejected in favor of the verified native `QStyleHints` approach; not independently verified against an authoritative source since it's not the recommendation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — every version verified directly against PyPI this session; matches independently-verified project-level research
- Architecture: HIGH — core patterns (pre-validation, QThread worker, namespaced keys) grounded in source code read directly this session, not assumed
- Pitfalls: HIGH for Pitfalls 1-3 (directly verified from pygdtf source), MEDIUM for Pitfall 4 (standard Qt threading knowledge, WebSearch-corroborated)

**Research date:** 2026-09-25
**Valid until:** 2026-10-25 (30 days — stable ecosystem, but re-verify pygdtf/PySide6 versions if planning is delayed significantly, since both are actively released)
