# Phase 1: Foundation Rebuild - Context

**Gathered:** 2026-09-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the crash-prone, hand-rolled Tkinter prototype (`BEtheLD`) with a spec-correct, decoupled foundation: users pick a target GDTF and one or more comparison GDTFs, and get a correct, crash-free comparison table in a modernized interface. Parsing moves to `pygdtf` (fixing attribute-collision and error-handling bugs), and the GUI layer is fully separated from a new, independently testable comparator/service layer. Full attribute browsing/search (Phase 2), diff highlighting (Phase 2), compare profiles/export (Phase 3), and packaging (Phase 4) are explicitly out of this phase's scope — Phase 1 only needs to keep the current two display categories (Beam, Physical Properties) working correctly on the new stack.

</domain>

<decisions>
## Implementation Decisions

### GUI Framework
- **D-01:** Rebuild on PySide6 (Qt for Python) instead of Tkinter/CustomTkinter — chosen for its mature `QTableView`/model-view widgets needed for Phase 2's sortable/filterable/diff-highlighted comparison grid, LGPL licensing (free to ship), and mature PyInstaller hooks for Phase 4 packaging. — **Reversibility:** one-way — swapping GUI frameworks again after Phase 2/3 build UI on top of PySide6's model/view system would mean redoing that UI work, not just a config change.
- **D-02:** Target Python 3.11+ as the floor (not the previously stated 3.7+) — required by the full research-recommended stack (PySide6 6.11.x needs ≥3.10, `websockets` 17.x needs ≥3.11 for Phase 5, `zeroconf` needs ≥3.10). Avoids re-deciding the Python floor in Phase 4/5. — **Reversibility:** costly — lowering it later would mean re-verifying every dependency's compatibility floor again.
- **D-03:** Full rewrite from scratch rather than incrementally porting `BEtheLD` — the framework swap (Tkinter → PySide6) and parser swap (hand-rolled → pygdtf) mean most existing code doesn't carry over directly; a clean rewrite avoids dragging Tkinter-specific patterns into the new stack.
- **D-04:** Proper package layout (e.g. separate `core`/service package + `gui` package + `tests/`) instead of a single script — directly supports UI-02 (GUI decoupled from parsing/comparison logic) and gives Phase 2/3 clean places to add code.

### Visual Style Direction
- **D-05:** Use `qt-material` for theming — a flat Material-Design-style reskin applied in ~2 lines, satisfying the "modernized, visually refreshed" requirement (UI-01) without restructuring the UI around a heavier widget-replacement library.
- **D-06:** Theme follows the OS's light/dark setting rather than a fixed default. Requires wiring qt-material's theme switching to the OS preference at startup (and ideally on change).
- **D-07:** No specific visual reference supplied — Claude has discretion to pick a clean, professional accent color/theme variant within qt-material's options that fits a lighting/AV tool.
- **D-08:** Polish bar for Phase 1 is a "functional modern baseline" — apply qt-material theming and clean layout, but don't over-invest in custom styling/icons yet. Phase 1's real goal is the decoupled architecture + spec-correct parsing; deeper visual polish can follow in later phases.

### pygdtf Data Model Depth
- **D-09:** The service/parsing layer wraps pygdtf's actual GDTF object model directly (fixture types, DMX modes, geometries, wheels, etc.) rather than flattening everything into a plain dict. Sets up Phase 2's full 60+ attribute browsing without a data-layer rework. — **Reversibility:** costly — Phase 2/3 will be built against this model shape; flattening it later would require touching every consumer.
- **D-10:** Phase 1 keeps displaying only the current two categories (Beam, Physical Properties) in the UI, even though the underlying model now exposes the full attribute set. Full browsing/search is explicitly Phase 2's job (ATTR-01/ATTR-02) — showing everything now would blur the phase boundary.
- **D-11:** Attribute name collisions (the current flat-dict bug) are fixed by namespacing each attribute by its full element path/context (e.g. which geometry or DMX channel it belongs to), mirroring pygdtf's own structured model. Directly satisfies Roadmap Phase 1 success criterion #2.
- **D-12:** No separate GDTF schema/structure pre-validation layer in Phase 1 — rely on pygdtf's own parsing errors (it implements the full GDTF object model and will raise on malformed input) and catch those exceptions for a friendly error message (RELI-01). RELI-02's `defusedxml`/size-limit guarding still applies independently as a security measure, not as structural pre-validation.

### Service Layer & Threading
- **D-13:** The comparator/service layer's public API returns a `ComparisonResult` object (small dataclass/model: target data, per-file comparisons, diff info) rather than raw dicts — gives Phase 2 (diff highlighting) and Phase 3 (CSV export) a clean, typed contract to build on. — **Reversibility:** costly — Phase 2/3 will consume this shape directly.
- **D-14:** GDTF parsing runs off the UI thread starting in Phase 1 (a QThread/worker for parse+compare), not deferred to a later phase — CONCERNS.md already flags UI-freeze as a known architectural issue in the old app; fixing it now avoids a rework once more UI depends on a synchronous flow.
- **D-15:** The service layer exposes a batch API — `compare(target, [files])` → one `ComparisonResult` covering all comparison files at once — matching the existing UI flow (pick target + multiple files, run once) and keeping aggregation logic out of the GUI layer.
- **D-16:** The service/parsing/comparison layer lives in its own dedicated package (e.g. `core/`) from the start, importable and unit-testable independently of Qt — consistent with D-04's package-layout decision.

### Claude's Discretion
- Exact accent color / qt-material theme variant (per D-07).
- Exact naming/keying scheme for attribute namespacing, as long as it follows pygdtf's structured model (per D-11, user selected "Namespace by element path" as the approach but left exact scheme to Claude in an earlier equivalent option).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project & Requirements
- `.planning/PROJECT.md` — core value, constraints, key decisions (milestone-level)
- `.planning/REQUIREMENTS.md` — v1 requirements; Phase 1 covers PARSE-01, UI-01, UI-02, RELI-01, RELI-02
- `.planning/ROADMAP.md` — Phase 1 goal and success criteria

### Existing Codebase
- `.planning/codebase/ARCHITECTURE.md` — current `BEtheLD` structure, data flow, anti-patterns being fixed (tightly-coupled GUI, missing `messagebox` import)
- `.planning/codebase/CONCERNS.md` — known bugs, security gaps (no file size limits, unvalidated paths), UI-freeze/threading issue being addressed by D-14
- `.planning/codebase/STACK.md` — current stack baseline being replaced

### Stack & Library Research
- `.planning/research/STACK.md` — full rationale for PySide6/pygdtf/pymvr/qt-material/PyInstaller choices, version compatibility matrix, alternatives considered (CustomTkinter, Flet), and the "what NOT to use" list (PyQt6, raw Tkinter, `pyqtdarktheme`)
- `.planning/research/SUMMARY.md` — overall research synthesis, including the correction that `mvrdevelopment/tools` has no parsing code (pygdtf/pymvr from `open-stage` is the real library)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/test_parse_gdtf.py`: existing pytest coverage for parse error paths (BadZipFile, ParseError) — pattern to follow for testing the new `core` package, even though the implementation underneath changes to pygdtf.
- `attribute_categories` dict (`BEtheLD` lines 21-24): the "Beam" / "Physical Properties" category split that Phase 1 keeps as the display scope (D-10) — re-derive equivalent categories from the new pygdtf-backed model rather than porting the old dict verbatim.

### Established Patterns
- Current app is single-threaded and blocks the UI during parsing (`CONCERNS.md` "Single-threaded UI" scaling limit) — D-14 fixes this at the foundation instead of carrying it forward.
- Current temp-directory extraction (copy-then-extract, `tempfile.mkdtemp()` + `shutil.rmtree()` in `finally`) is flagged as an unnecessary double I/O step in CONCERNS.md — the new `core` package should read GDTF zips directly rather than copying first, since pygdtf/`zipfile` can open the archive in place.

### Integration Points
- The new `core`/service package (D-16) is what the PySide6 GUI layer calls into — GUI code must not import `pygdtf` or `zipfile` directly, only the service layer's `ComparisonResult`-returning API (D-13, D-15).
- Error handling: service layer should let pygdtf's exceptions propagate (D-12); the GUI layer's worker/thread boundary (D-14) is where those exceptions get caught and turned into a user-friendly message, replacing the currently-broken `messagebox` error path (`CONCERNS.md` "Missing Import: messagebox").

</code_context>

<specifics>
## Specific Ideas

No specific visual reference was supplied (D-07) — Claude has discretion on the exact qt-material theme variant/accent color, staying within a "clean, professional" aesthetic appropriate for a lighting/AV tool. Theme mode (dark/light) should follow the OS setting (D-06) rather than a fixed default.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within Phase 1 scope. No scope-creep items were raised during this discussion.

</deferred>

---

*Phase: 1-Foundation Rebuild*
*Context gathered: 2026-09-25*
