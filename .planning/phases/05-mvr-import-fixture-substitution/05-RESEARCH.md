# Phase 5: MVR Import & Fixture Substitution - Research

**Researched:** 2026-10-24
**Domain:** MVR (My Virtual Rig) file parsing via `pymvr`, GDTF-fixture-type deduplication, per-attribute requirement modeling (direction + tolerance), sidecar-file persistence, and candidate scoring/ranking — all inside the existing Qt-free `core/` / PySide6 `gui/` split.
**Confidence:** MEDIUM — the `pymvr` API surface and zip-embedding model were verified by reading and executing the actual installed package source this session (HIGH confidence on those points); the scoring/ranking math and smart-default-direction table are necessarily this researcher's design proposal since the project has never built a tolerance-based matcher before (flagged `[ASSUMED]` throughout, per `05-CONTEXT.md`'s own instruction to "ask questions if needed" on the direction+threshold model).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Scope redefinition
- **D-01:** Phase 5 drops the original live-LAN-discovery/MVR-xchange-networking framing (former NET-01/NET-02/NET-03) in favor of a file-based import + fixture-substitution workflow. — **Reversibility:** reversible — live discovery was never built; the old requirements move to REQUIREMENTS.md v2 and can be revisited as their own phase later without touching anything this phase builds.

#### MVR import
- **D-02:** Importing an MVR file produces one entry per **unique GDTF fixture type** referenced in the show, not one entry per physical fixture instance (so 24 identical moving heads collapse to a single entry). This list becomes the fixture set for this workflow, replacing manual one-by-one GDTF file browsing.
- **D-03:** The user works through fixtures **one at a time** (pick a fixture type → mark its requirements → optionally search for a replacement), not a batch-everything-up-front mode.

#### Per-fixture importance ("requirements")
- **D-04:** Each fixture type gets its own **independent** checklist of important attributes — not one shared/global Compare Profile (ATTR-03) applied uniformly to every fixture. A moving head and a strobe can flag entirely different attributes as important.
- **D-05:** For each attribute marked important, the app suggests a **smart default direction** (higher-is-better, lower-is-better, or closest-to-target-is-best) based on the attribute itself (e.g., weight → lower is better; lumen output → higher is better; beam angle → closest to target). The LD can override the suggested direction per attribute.
- **D-06:** Tolerance (how close counts as "close enough") is set **per attribute by the LD**, not one global tolerance percentage applied to everything. Different attributes can have very different tolerance bands.

#### Two-role workflow & sharing
- **D-07:** This is explicitly a **two-role workflow**: the LD imports the MVR and sets requirements per fixture; a separate party (e.g., a rental shop, possibly on a different computer entirely) uses GDTF Comparer with the LD's requirements to check what in *their own* inventory could work. The tool must support both roles running independently, not assume one person/one session does everything.
- **D-08:** The LD's per-fixture requirements (important attributes + direction + tolerance) are saved to a **separate, standalone shareable file** — explicitly **not embedded inside the MVR file itself**. — **Reversibility:** one-way in practice — once a file format for this exists and gets shared externally, changing its shape later is a breaking change for anyone who has saved one. Rationale confirmed by the user from direct prior experience at Vectorworks: custom data bolted onto a spec-governed scene-description format risks being silently dropped or mangled when the file passes through other lighting software (Vectorworks, Capture, MA3, etc.) that only knows the official schema. A sidecar file has no such risk and round-trips cleanly.
- **D-09:** The shop only needs **the one fixture's requirements file** to do their check — never the LD's full MVR (the whole show file, every fixture, every position in the plot). Keep the shared artifact scoped to a single fixture's requirements, not the whole plot.

#### Matching & candidate results
- **D-10:** Match results use a **three-state per-attribute indicator**, not a single pass/fail or a single numeric score:
  - Green — candidate meets or is better than the requirement (per that attribute's direction; note some attributes are "lower is better," so "better" is relative to the direction, not always a larger number).
  - Yellow — candidate is close; might work.
  - Red — candidate is well outside the requirement's range; won't work.
  Ask the user for clarification on edge-case attribute types during planning/research if the direction+threshold model doesn't cleanly fit (per the user's own "ask questions if needed" note).
- **D-11:** Candidates are **ranked, best match first** — derived from the per-attribute traffic lights (e.g., most greens / fewest reds ranks higher). The per-attribute lights are the detail view; the ranking is the summary/sort order. These two answers are not in conflict — rank by aggregate light quality, show the individual lights per attribute underneath.

#### Candidate library
- **D-12:** Candidate replacement fixtures come from a **local folder of GDTF files the user (shop) already maintains** — their own collected inventory from various manufacturers. The app's job is only to point at that folder and scan the `.gdtf` files in it.
- **D-13:** The app does **not** build any online GDTF database browsing/downloading feature (e.g., querying GDTF-Share) to acquire candidate files — out of scope for this phase. Users are expected to collect their own candidate GDTF files by whatever means they already use, outside the app.

### Claude's Discretion
- Exact on-disk format of the "fixture requirements" file (likely JSON, mirroring the existing `core/profile_repository.py` atomic-write pattern — same-folder temp file + `os.replace`, schema version field, zero Qt in `core/`). Research/planning should verify this pattern transfers cleanly.
- Exact UI flow/screen layout for "mark importance per fixture," "export requirements," "import requirements + pick candidate folder," and the ranked-results view. Follow existing patterns (Attributes side panel, Profiles dropdown/toolbar from Phase 3) where they fit.
- Smart-default direction rules per attribute type (D-05) — Claude should propose sensible defaults per GDTF attribute during planning/research, informed by lighting-domain knowledge (e.g., GDTF `AttributeDefinitions`), and the LD can always override.
- Tie-breaking logic within the ranked list when two candidates have the same green/yellow/red counts.

### Deferred Ideas (OUT OF SCOPE)
- **Live LAN discovery of other MVR-xchange stations** (formerly NET-01) — moved to REQUIREMENTS.md v2. May become its own future phase.
- **Live MVR pull from a discovered station over the network** (formerly NET-02) — moved to REQUIREMENTS.md v2, same reasoning.
- **Built-in browsing/downloading of an online GDTF database** (e.g. GDTF-Share integration to acquire candidate fixtures) — explicitly out of scope per D-13; the user manages their own candidate-file folder.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|---------------------|
| PARSE-02 | App parses MVR files using the `pymvr` library | Verified `pymvr==1.0.7` API/zip-embedding model this session (Architecture Patterns 1-3); documented its hardening gaps and the pre-validation wrapper needed before it is safe to call (Common Pitfalls 1-3, Code Examples) |
| SUB-01 | Import an MVR file and see one entry per unique GDTF fixture type (not per instance) | Recursive fixture-walk (Pattern 2, verified by live execution) + dedup-by-`gdtf_spec` (Pattern 3) + embedded-GDTF extraction reusing the existing `core/repository.py`/`core/hardening.py` pipeline |
| SUB-02 | Mark attributes "important" per fixture type, each with a direction (smart default, overridable) and its own tolerance | Smart Default Direction Table proposal (Assumptions A1/A2, tagged for confirmation) + Don't Hand-Roll guidance reusing `core/models.py`/`core/comparator.py` shapes; Pitfalls 5-6 flag the non-numeric-attribute and undeclared-value edge cases |
| SUB-03 | Export one fixture's requirements to a separate shareable file; a different user/session can load it back in | Architecture Patterns (new `core/requirements_repository.py`) mirroring `core/profile_repository.py`'s proven atomic-write/schema-version pattern exactly; Security Domain flags this file as crossing a trust boundary (D-07's two roles) |
| SUB-04 | Score a folder of candidate GDTF files against an imported fixture's requirements with a three-state per-attribute result, ranked best-first | Scoring Algorithm proposal (Open Question 1, Assumption A4) + Don't Hand-Roll (reuse `FixtureRepository.load()` for the folder scan) + Architecture (reuse the `BackgroundBrushDelegate` pattern for the 3-state colors to actually render) |
</phase_requirements>

## Summary

Phase 5 adds a new file-format entry point (`pymvr`-parsed `.mvr` show files) and a new business capability (direction+tolerance fixture substitution) on top of an already mature, strictly layered codebase. The existing `core/` package is Qt-free, imports neither `tempfile` nor `shutil`, never calls `zipfile.ZipFile.extractall`, and pre-validates every GDTF archive (size limits, compression-ratio zip-bomb guard, `defusedxml` XXE guard) *before* handing bytes to `pygdtf` — enforced by an AST-based architecture test (`tests/test_architecture.py`) that will automatically cover any new module placed under `core/` or `gui/`. The new MVR-handling code must follow the identical discipline, because `pymvr` itself provides **none** of it: this session's direct inspection of the installed `pymvr==1.0.7` wheel confirms it parses `GeneralSceneDescription.xml` with bare `xml.etree.ElementTree.fromstring` (no `defusedxml`), has no size/zip-bomb guard, and raises bare `AttributeError`/`KeyError` (not a friendly typed error) on a missing or malformed archive — the exact class of gap `core/hardening.py` already closed for GDTF, Pitfall-for-Pitfall.

The second major finding is structural, not security-related: `pymvr.Fixture` objects only carry a *reference* to a GDTF file (`fixture.gdtf_spec`, a filename string) — they do **not** carry the parsed GDTF attribute data. To build the "one entry per unique GDTF fixture type" list (SUB-01) with real attribute values to mark as "important" (SUB-02), the app must independently open the same `.mvr` zip archive (never relying on `pymvr`'s own private `_package` handle) and extract each embedded `<name>.gdtf` member by exact name match against `fixture.gdtf_spec`, then run those bytes through the **existing** `core.hardening` + `pygdtf` + `core.extract` pipeline that already powers standalone `.gdtf` loading — reused, not duplicated. This session verified (by running real code against the installed package) that `pymvr.GeneralSceneDescription` accepts an in-memory `io.BytesIO` in place of a path, that `Fixture` nodes nest recursively inside `Layer.child_list` *and* inside `GroupObject.child_list`, and that `gdtf_spec` text is auto-normalized to end in `.gdtf`, matching the zip member name exactly.

The third finding is a genuinely open design question the research cannot resolve on its own: `05-CONTEXT.md` D-06 specifies **one** tolerance value per attribute, but D-10's three-state (green/yellow/red) indicator structurally needs **two** boundaries. This research proposes a concrete default (documented below, tagged `[ASSUMED]`) but flags it explicitly for `/gsd-plan-phase` or a human checkpoint to confirm before implementation, per D-10's own instruction ("ask questions if needed... if the direction+threshold model doesn't cleanly fit").

**Primary recommendation:** Add `pymvr==1.0.7` as a new pinned dependency behind a `checkpoint:human-verify` gate (package-legitimacy seam returned `SUS`, not `OK` — see Package Legitimacy Audit); build one new Qt-free `core` module per responsibility (MVR hardening/extraction, requirements persistence, candidate scoring) mirroring `core/hardening.py` + `core/profile_repository.py`'s proven patterns exactly; and resolve the single-tolerance/three-state ambiguity with the user before writing the scoring algorithm's final boundary math.

## Architectural Responsibility Map

This project is a two-tier desktop app (PySide6 GUI ↔ Qt-free `core/`), not a client/server web app — the standard tier vocabulary (Browser/SSR/API/CDN/DB) doesn't map cleanly, so this table uses the project's own enforced tiers instead (`tests/test_architecture.py` mechanically enforces the GUI↔Core boundary already).

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| MVR archive validation (size/zip-bomb/XXE) | Core (new `core/mvr_hardening.py` or extended `core/hardening.py`) | — | Mirrors existing GDTF hardening; `pymvr` provides none of this itself (verified this session) |
| MVR scene-tree parsing (`pymvr`) | Core (new `core/mvr_repository.py`) | — | Qt-free library call, same shape as `core/repository.py`'s `pygdtf` call |
| Unique-fixture-type dedup + embedded-GDTF extraction | Core | — | Pure data transform; reuses `core/hardening.py` + `core/extract.py` for the embedded `.gdtf` bytes |
| Per-fixture "mark important + direction + tolerance" UI | GUI (new widget) | Core (data model: `Requirement` dataclass) | State the user edits lives in GUI, same split as `gui/attribute_picker.py` vs `core/models.py` |
| Smart-default direction lookup | Core (new `core/direction_defaults.py` or inline table) | — | Pure function of attribute name → default `Direction`; no UI dependency |
| Requirements sidecar file (export/import, D-08) | Core (new `core/requirements_repository.py`) | Filesystem (user-chosen path, not app-data dir) | Same atomic-write discipline as `core/profile_repository.py`, but path is caller-supplied (Save/Open dialog), not a fixed app-data file |
| Candidate-folder GDTF scan (SUB-04) | Core | Filesystem | Reuses `core/repository.py`'s existing `FixtureRepository.load()` per file found |
| Candidate scoring (direction+tolerance → 3-state) | Core (new `core/substitution.py`) | — | Pure function, variant of `core/comparator.py`'s compare-logic shape, not Qt-aware |
| Ranking (green/yellow/red aggregate sort) | Core (same module) | — | Pure function over scoring output |
| Three-state traffic-light rendering | GUI (new delegate) | — | Must reuse the `BackgroundBrushDelegate` pattern (Phase 2 finding: qt-material's stylesheet silently suppresses `BackgroundRole` painting without a dedicated delegate) |
| MVR-open / folder-pick / requirements Save-As dialogs | GUI (`QFileDialog`) | — | Same as existing `select_target_file`/`select_compare_files` in `gui/main_window.py` |
| Long-running parse/scan off the GUI thread | GUI (`QThread` worker) | Core (pure function the worker calls) | Same `ComparisonWorker` pattern as `gui/worker.py` (D-14); MVR parsing and folder scanning are both blocking I/O that must not freeze the event loop |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|---------------|
| `pymvr` | 1.0.7 (latest on PyPI as of this session) [VERIFIED: pip index + PyPI JSON API, checked this session] | Parses `GeneralSceneDescription.xml` inside an `.mvr` zip into a typed object tree (`Scene`/`Layers`/`Layer`/`Fixture`/`GroupObject`/...) | Named explicitly in `REQUIREMENTS.md` PARSE-02/SUB-01 and `05-CONTEXT.md` — not a discretionary choice. Maintained by `open-stage` (same GitHub org as `pygdtf`, already approved and in production use since Phase 1) [VERIFIED: PyPI JSON API `project_urls.Repository` = `https://github.com/open-stage/python-mvr.git`, checked this session] |
| `pygdtf` | 1.4.5 (already pinned, Phase 1) | Parses each embedded `.gdtf` member extracted from the MVR zip — identical call already used for standalone GDTF files | Already the project's GDTF parser; no new library needed for this half of the work |
| `defusedxml` | 0.7.1 (already pinned, Phase 1) | Must additionally guard the MVR's own `GeneralSceneDescription.xml` parse, since `pymvr` does not | Already in the dependency tree; this phase just needs a second call site |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|---------------|
| `zipfile` (stdlib) | — | Independent re-open of the `.mvr` archive to extract embedded `.gdtf` members by exact name — never reuse `pymvr`'s private `_package` attribute | Every MVR import; the embedded-GDTF-extraction step |
| `json` (stdlib) | — | Requirements sidecar file serialization, same as `core/profile_repository.py`'s `profiles.json` | Requirements export/import (SUB-03) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `pymvr`'s own `GeneralSceneDescription(path=str)` opening the file from disk | `GeneralSceneDescription(path=io.BytesIO(validated_bytes))` | The in-memory form lets this app's own pre-validation (size/zip-bomb/XXE checks) run on the *exact* bytes `pymvr` will parse, with a single disk read — verified working this session (see Code Examples) |
| Hand-rolling a brand-new candidate-scoring engine | Extending `core/comparator.py`'s existing value-equality/row-matching shape | A parallel implementation would duplicate `AttributeKey`/`FixtureModel`/`values_equal` concepts for no benefit; the new scoring function should accept the same `FixtureModel.attributes` mapping `core/comparator.py` already consumes |

**Installation:**
```bash
pip install pymvr==1.0.7
```
Add to `pyproject.toml` `[project.dependencies]` alongside the existing pinned entries (`PySide6==6.11.2`, `pygdtf==1.4.5`, `defusedxml==0.7.1`, `qt-material==2.17`), following the project's existing exact-pin convention. **Gate this install behind a `checkpoint:human-verify` task** — see Package Legitimacy Audit below.

**Version verification:** `pip index versions pymvr` and `pip index versions pygdtf` were both run this session; `pymvr` is at 1.0.7 (11 releases back to 0.1.0), `pygdtf` unchanged at the already-pinned 1.4.5.

## Package Legitimacy Audit

Run via `gsd_run query package-legitimacy check --ecosystem pypi pymvr pygdtf` this session.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|--------------|---------|--------------|
| `pymvr` | PyPI | published 2026-04-03 per seam [weekly-download metric unavailable to seam] | unknown to seam | seam reported `no-repository`, but PyPI's own JSON API (`project_urls.Repository`) shows `https://github.com/open-stage/python-mvr.git` — checked directly this session | **SUS** (seam) | **Flagged — planner must add `checkpoint:human-verify` before `pip install pymvr` is first run** |
| `pygdtf` | PyPI | published 2026-03-31 per seam | unknown to seam | same `no-repository` false-negative; PyPI JSON shows `https://github.com/open-stage/python-gdtf.git` | **SUS** (seam) | **Already installed & in production since Phase 1 — no new action; not a new install this phase** |

**Packages removed due to `[SLOP]` verdict:** none.

**Packages flagged as suspicious `[SUS]`:** `pymvr` (new this phase — gate behind `checkpoint:human-verify`). `pygdtf` also shows `SUS` from the same seam, but it is an *existing, already-approved* dependency from Phase 1 (see `pyproject.toml`); no new checkpoint is needed for it specifically, it's flagged here only because the audit command was run for both.

**Audit note on the `no-repository` signal:** the legitimacy seam's heuristic appears to check only a package's `home_page` metadata field, which is `None` for both `pymvr` and `pygdtf` (both intentionally omit it and publish their repo only under PyPI's separate `project_urls` map). Fetching `https://pypi.org/pypi/pymvr/json` directly this session confirms `project_urls: {"Changelog": "...", "Repository": "https://github.com/open-stage/python-mvr.git"}` — the repository does exist, same maintaining org (`open-stage`) as the already-trusted `pygdtf`. This materially weakens the `SUS` verdict's practical risk, but per the Package Legitimacy Gate protocol, the verdict itself still governs disposition — a human must confirm before the new `pymvr` install, not this researcher.

## Architecture Patterns

### System Architecture Diagram

```
                    ┌─────────────────────────┐
                    │   GUI (PySide6)          │
                    │  QFileDialog: pick .mvr  │
                    └────────────┬─────────────┘
                                 │ path
                                 ▼
                    ┌─────────────────────────┐
                    │ QThread worker (D-14)    │  ← off GUI thread, mirrors
                    │ calls core.mvr_repository│    gui/worker.py exactly
                    └────────────┬─────────────┘
                                 │
         ┌───────────────────────┼─────────────────────────────┐
         ▼                       ▼                             ▼
┌──────────────────┐   ┌───────────────────┐        ┌─────────────────────┐
│ MVR hardening      │  │ pymvr parses       │        │ Independent zipfile │
│ (size/zip-bomb/XXE │─▶│ GeneralScene-      │        │ re-open: extract    │
│ pre-validation, new│  │ Description.xml    │        │ each embedded        │
│ code — pymvr has   │  │ into Layers/       │        │ <name>.gdtf member   │
│ none of this)       │  │ Fixture tree       │        │ by fixture.gdtf_spec │
└──────────────────┘   └─────────┬──────────┘        └──────────┬───────────┘
                                   │ recursive walk                │ bytes
                                   │ (Layer→ChildList→              │
                                   │  fixtures + GroupObject        ▼
                                   │  recursion)           ┌──────────────────────┐
                                   ▼                        │ core.hardening +      │
                          ┌─────────────────┐                │ pygdtf + core.extract │
                          │ Dedup by          │◀──────────────│ (EXISTING pipeline,   │
                          │ fixture.gdtf_spec │   attributes   │ reused unchanged)     │
                          │ → unique fixture  │                └──────────────────────┘
                          │ TYPES (D-02)      │
                          └────────┬──────────┘
                                   │ one FixtureModel-shaped entry per type
                                   ▼
                    ┌─────────────────────────────┐
                    │ GUI: fixture-type list        │
                    │ → per-type requirements editor│  "mark important,
                    │ (new widget, mirrors            direction, tolerance"
                    │  gui/attribute_picker.py shape) │  (SUB-02)
                    └────────────┬────────────────┘
                                 │ user-built Requirement list for ONE type
                                 ▼
                    ┌─────────────────────────────┐
                    │ core.requirements_repository  │  atomic write,
                    │ save_requirements(path, reqs) │  schema-versioned,
                    │  (SUB-03 — sidecar file,        same pattern as
                    │   D-08/D-09, user-chosen path) │  core/profile_repository.py
                    └─────────────────────────────┘
                                 │ .json file, shared out-of-band
                                 ▼
          ═══════════════ different machine / different session ═══════════════
                                 │
                    ┌─────────────────────────────┐
                    │ core.requirements_repository  │
                    │  load_requirements(path)       │  (SUB-03 round trip)
                    └────────────┬────────────────┘
                                 │
                    ┌─────────────────────────────┐
                    │ GUI: pick candidate folder     │
                    └────────────┬────────────────┘
                                 ▼
                    ┌─────────────────────────────┐
                    │ core.repository.FixtureRepository│ (EXISTING, reused)
                    │ .load() each *.gdtf in folder   │  skip/report per-file
                    └────────────┬────────────────┘      failures (RELI-01 style)
                                 ▼
                    ┌─────────────────────────────┐
                    │ core.substitution.score()      │  (new) direction+tolerance
                    │  → 3-state per attribute        │  → green/yellow/red (D-10)
                    │  → rank() aggregate sort         │  (D-11)
                    └────────────┬────────────────┘
                                 ▼
                    ┌─────────────────────────────┐
                    │ GUI: ranked results table       │  BackgroundBrushDelegate
                    │  (new delegate, reuses Phase 2   │  REQUIRED for the 3 colors
                    │   qt-material-stylesheet fix)    │  to actually paint
                    └─────────────────────────────┘
```

### Recommended Project Structure

```
src/gdtf_comparer/
├── core/
│   ├── hardening.py              # EXISTING — consider generalizing
│   │                              #   extract_description_bytes/parse_description_safely
│   │                              #   to accept any member name + size limit, so MVR reuses
│   │                              #   the same zip-bomb-guarded member-read helper
│   ├── mvr_hardening.py          # NEW — MVR-specific size constants + validation entry point
│   ├── mvr_repository.py         # NEW — pymvr call, recursive fixture walk, dedup by gdtf_spec,
│   │                              #   embedded-.gdtf extraction, feeds core.repository's pipeline
│   ├── requirements_repository.py# NEW — Requirement dataclass + atomic save/load sidecar JSON
│   ├── substitution.py           # NEW — direction+tolerance scoring + ranking (pure functions)
│   ├── repository.py             # EXISTING — FixtureRepository.load(), reused as-is for
│   │                              #   both embedded and candidate-folder GDTF files
│   ├── comparator.py             # EXISTING — unrelated to scoring, not modified
│   ├── errors.py                 # EXTEND — new MVRError/MVRValidationError/MVRParseError,
│   │                              #   RequirementsStorageError family, mirroring GDTFError/ProfileError
│   └── models.py                 # EXTEND (maybe) — Direction enum, Requirement dataclass
│                                   #   (or keep in substitution.py / requirements_repository.py)
├── gui/
│   ├── mvr_import_panel.py       # NEW — fixture-type list after MVR import
│   ├── requirements_editor.py    # NEW — per-fixture "mark important + direction + tolerance"
│   ├── candidate_results_view.py # NEW — ranked results table + 3-state delegate
│   ├── worker.py                 # EXTEND — new QThread worker classes for MVR parse + folder scan
│   ├── attribute_picker.py       # EXISTING — reference shape for requirements_editor's tree
│   └── table_model.py            # EXISTING — reference shape (BackgroundBrushDelegate) for
│                                   #   candidate_results_view's 3-state cell painting
tests/
├── core/
│   ├── test_mvr_hardening.py     # NEW
│   ├── test_mvr_repository.py    # NEW
│   ├── test_requirements_repository.py # NEW
│   └── test_substitution.py      # NEW
├── gui/
│   ├── test_mvr_import.py        # NEW
│   ├── test_requirements_editor.py # NEW
│   └── test_candidate_results.py # NEW
└── conftest.py                   # EXTEND — add an `make_mvr` fixture mirroring `make_gdtf`
```

### Pattern 1: Pre-validate bytes once, then hand the SAME bytes to the library (D-14/T-01-15 pattern, reused)

**What:** `core/hardening.py`'s `prevalidate_gdtf_document()` reads a file once into memory, validates it (`defusedxml`, size limits, zip-bomb ratio), and returns both the raw bytes *and* the already-parsed, already-safe XML tree — `pygdtf` then parses `io.BytesIO(validated_bytes)`, the exact same bytes, never a second disk read.

**When to use:** Apply the identical shape to MVR: read the `.mvr` file once, validate `GeneralSceneDescription.xml`'s bytes with `defusedxml` BEFORE calling `pymvr`, then hand `pymvr.GeneralSceneDescription` an `io.BytesIO` of the validated *archive* bytes (not just the XML member) so `pymvr`'s own internal (unguarded) `ElementTree.fromstring` call only ever runs on bytes this app has already confirmed are free of DTDs/entities.

**Example (verified working this session):**
```python
# Source: this session's interactive test against the installed pymvr==1.0.7 wheel
import io, zipfile
import pymvr

buf = io.BytesIO(validated_archive_bytes)  # bytes already read+validated by our own code
mvr = pymvr.GeneralSceneDescription(path=buf)   # accepts a file-like object, not just a path string
for layer in mvr.scene.layers:
    ...
# mvr._package is the zipfile.ZipFile pymvr opened internally — DO NOT rely on it for
# extracting embedded .gdtf members; re-open independently (Pattern 2) so the embedded-GDTF
# read goes through this app's own size-limited, non-extractall zip member read, not pymvr's.
```

### Pattern 2: Recursive fixture walk through `Layer` and nested `GroupObject` (verified this session)

**What:** `pymvr.Fixture` nodes are not only direct children of `Layer.child_list.fixtures` — they can also be nested inside `GroupObject.child_list.fixtures`, and `GroupObject`s can nest within each other. A flat `for layer in mvr.scene.layers: for fixture in layer.child_list.fixtures` walk **will silently miss grouped fixtures**.

**When to use:** Always, when enumerating every `Fixture` in an MVR for SUB-01's "one entry per unique GDTF fixture type" requirement.

**Example (confirmed by direct execution this session — see verbatim output below):**
```python
# Source: this session's interactive test (test script in scratchpad), confirmed output:
#   direct fixtures: ['F1']
#   group_objects: ['G1']
#   group child_list fixtures: ['F2', 'F3']
#   gdtf_spec values: ['Acme@Spot.gdtf', 'Beta@Wash.gdtf']
def iter_fixtures(child_list) -> "Iterator[pymvr.Fixture]":
    """Yield every Fixture node reachable from a ChildList, recursing into
    GroupObject (which can itself nest further GroupObjects), and into every
    other node type that carries its own child_list (Truss/Support/
    VideoScreen/Projector all subclass BaseChildNodeExtended and have one)."""
    if child_list is None:
        return
    yield from child_list.fixtures
    for group in child_list.group_objects:
        yield from iter_fixtures(group.child_list)
    for node_list in (
        child_list.trusses,
        child_list.supports,
        child_list.video_screens,
        child_list.projectors,
    ):
        for node in node_list:
            yield from iter_fixtures(getattr(node, "child_list", None))

def all_fixtures(mvr: "pymvr.GeneralSceneDescription"):
    for layer in mvr.scene.layers:
        yield from iter_fixtures(layer.child_list)
```

### Pattern 3: Dedup by `gdtf_spec`, then extract the matching embedded `.gdtf` member independently

**What:** `fixture.gdtf_spec` is a filename string (pymvr auto-appends `.gdtf` if the author's text omitted it — verified this session: `"Acme@Spot"` becomes `self.gdtf_spec == "Acme@Spot.gdtf"`), matching a top-level member name inside the same `.mvr` zip. Group every `Fixture` by this string to get SUB-01's unique-type list; for each unique value, extract that exact member's bytes with a **fresh, independent** `zipfile.ZipFile` (reusing the already-validated full-archive bytes this app read once) — never `mvr._package`, a private attribute of the `pymvr` object this app doesn't control the lifecycle of.

**Example:**
```python
# Source: this session's direct inspection of pymvr/__init__.py BaseChildNode._read_xml
# (lines 479-488) plus this session's live test confirming the zip member name matches
# fixture.gdtf_spec exactly.
from collections import defaultdict

by_gdtf_spec: "dict[str, list[pymvr.Fixture]]" = defaultdict(list)
for fixture in all_fixtures(mvr):
    if fixture.gdtf_spec:  # skip fixtures with no GDTF reference at all
        by_gdtf_spec[fixture.gdtf_spec].append(fixture)

with zipfile.ZipFile(io.BytesIO(validated_archive_bytes)) as zf:
    names = set(zf.namelist())
    for gdtf_spec, instances in by_gdtf_spec.items():
        if gdtf_spec not in names:
            # Reference to a GDTF the MVR claims but doesn't actually bundle —
            # report per-type, never crash the whole import (RELI-01 style).
            continue
        with zf.open(gdtf_spec) as member:
            gdtf_bytes = member.read(MVR_MAX_EMBEDDED_GDTF_BYTES + 1)  # capped read
        # Feed gdtf_bytes through the SAME hardening + pygdtf + extract_attributes
        # pipeline core/repository.py already uses for standalone .gdtf files.
```

### Anti-Patterns to Avoid

- **Trusting `pymvr`'s own XML/zip parsing as "safe enough":** it has none of this app's hardening (no `defusedxml`, no size caps, no zip-bomb ratio check — confirmed by reading `pymvr/__init__.py` this session). Every `.mvr` file must go through this app's own pre-validation before `pymvr` ever touches it, exactly as `pygdtf` is never handed unvalidated bytes today.
- **Calling `mvr._package` from outside `core.mvr_repository`:** it's a private, underscore-prefixed attribute with no documented lifecycle guarantee (the object isn't even always set — see Common Pitfalls below). Re-open the archive independently from the same validated bytes instead.
- **Deduplicating fixture types by `(gdtf_spec, gdtf_mode)` instead of `gdtf_spec` alone:** `gdtf_mode` is the DMX personality/mode name, not the fixture type — D-02's "unique GDTF fixture type" means the GDTF *file* reference, matching "24 identical moving heads collapse to one entry" regardless of which DMX mode each instance happens to be patched to.
- **Writing a second zip-bomb/XXE guard from scratch for MVR:** generalize `core/hardening.py`'s existing member-extraction helpers (parameterize the member name and size constant) rather than hand-rolling a parallel implementation — same reasoning as the project's own "Don't Hand-Roll" discipline below.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|--------------|-----|
| MVR scene-tree XML parsing | A hand-rolled `ElementTree` walk of `GeneralSceneDescription.xml`'s `Layer`/`Fixture`/`GroupObject` schema | `pymvr`'s typed object tree (`Scene`, `Layers`, `Layer`, `ChildList`, `Fixture`, `GroupObject`, ...) | It's the requirement (PARSE-02/SUB-01 name `pymvr` explicitly) and it already handles the MVR-spec quirks (e.g. the `cp437`/IBM-PC filename re-encoding in `GDTFSpec` text — see Common Pitfalls) that a from-scratch parser would silently get wrong |
| Zip-bomb / XXE guarding for the MVR archive | A second, parallel hardening module that duplicates `core/hardening.py`'s logic | Generalize the existing `extract_description_bytes`/`parse_description_safely` functions to take a member name + size-limit parameter, and call them for `GeneralSceneDescription.xml` the same way `description.xml` is called today | Two independently-maintained zip-bomb guards is exactly the kind of drift the project's single-pipeline discipline (D-14, T-01-15) exists to prevent |
| Candidate GDTF scoring against a target spec | A brand-new value-comparison engine from scratch | A new `core/substitution.py` module, but one that consumes the *same* `AttributeKey → AttributeValue` mapping `core/comparator.py` and `core/models.py` already define | The scoring function is conceptually "compare one candidate's value to a target value with a direction and a tolerance band" — a variant of `values_equal()`'s job, not an unrelated problem |
| Atomic sidecar-file writes | Plain `open(path, "w")` + `json.dump` | The exact same-folder-temp-file + `os.fsync` + `os.replace` pattern `core/profile_repository.py._write_all()` already implements | Partial-write corruption on crash/power-loss is a solved problem in this codebase already; don't reintroduce the risk for the new requirements file |
| Folder-of-GDTF-files scanning | A new directory walker + ad-hoc per-file try/except | `os.listdir()` (or `glob`) over the chosen folder, feeding each `*.gdtf` path through the **existing** `core.repository.FixtureRepository.load()` (already raises typed `GDTFError` subclasses on a bad file) | SUB-04 says "the app's job is only to point at that folder and scan the `.gdtf` files in it" (D-12) — loading logic is 100% already built |

**Key insight:** every new piece of SUB-01..04 either (a) wraps an external library call in the project's existing hardening/typed-error discipline, or (b) is a small pure-function variant of a data shape (`AttributeKey`/`FixtureModel`) the project already has. There is no part of this phase that genuinely needs a new architectural pattern — it needs the *existing* patterns applied twice more.

## Common Pitfalls

### Pitfall 1: `pymvr.GeneralSceneDescription(path=None)` crashes with a bare `AttributeError`, not a friendly error

**What goes wrong:** `GeneralSceneDescription.__init__` only ever sets `self._package` inside an `if path is not None:` branch, then immediately checks `if self._package is not None:` unconditionally — so calling it with no path raises `AttributeError: 'GeneralSceneDescription' object has no attribute '_package'`.
**Why it happens:** Confirmed by direct execution this session (`pymvr.GeneralSceneDescription(path=None)` → `AttributeError 'GeneralSceneDescription' object has no attribute '_package'`). It's a real bug/gap in the library, not a misunderstanding.
**How to avoid:** Never call the constructor without a path/file-like object; wrap every call in this app's own `try/except` that catches `Exception` broadly (same posture as `core/repository.py`'s `FixtureRepository.load()` catch-all) and re-raises a typed `MVRParseError`/`MVRValidationError` with a friendly message — this app must never surface a raw `AttributeError` to the user.
**Warning signs:** Any code path that could pass `None` through (e.g. an empty "recent files" list defaulting to `None` rather than being guarded before the call).

### Pitfall 2: A non-MVR or corrupted `.mvr` file raises a bare `KeyError`, not a typed error

**What goes wrong:** If the zip doesn't contain a member named exactly `GeneralSceneDescription.xml`, `pymvr._find_root()` lets `zipfile.ZipFile.open()`'s `KeyError` propagate unchanged: `KeyError: "There is no item named 'GeneralSceneDescription.xml' in the archive"`.
**Why it happens:** Confirmed by direct execution this session. `pymvr` has no `try/except` around this lookup at all.
**How to avoid:** Mirror `core/hardening.py`'s `extract_description_bytes()` pattern — check archive membership explicitly (or catch `KeyError`/`zipfile.BadZipFile` around the `pymvr` call) and raise a friendly typed error (`MVRValidationError`, e.g. "it is not a valid MVR file (GeneralSceneDescription.xml is missing)") instead of letting the raw exception surface in a GUI dialog.
**Warning signs:** A user selecting a renamed `.zip` or a `.gdtf` file by mistake in the "Import MVR" file picker.

### Pitfall 3: `pymvr`'s XML parsing has no XXE/zip-bomb protection — it's a defense-in-depth gap identical to the one Phase 1 already closed for GDTF

**What goes wrong:** `_find_root()` (line 46 of `pymvr/__init__.py`, read directly this session) calls plain `xml.etree.ElementTree.fromstring(description_str)` with no `forbid_dtd`/`forbid_entities`/`forbid_external` guard, and nothing in the library checks the archive's total uncompressed size or compression ratio before extracting.
**Why it happens:** `pymvr` is a parsing convenience library, not a hardened file-ingestion layer — same posture `pygdtf` has, which is exactly why `core/hardening.py` exists in front of it today.
**How to avoid:** Pre-validate the `.mvr` archive with the same `defusedxml`-based approach `core/hardening.py` already uses for `description.xml`: read the archive bytes once, check size/ratio limits, extract and `defusedxml`-parse `GeneralSceneDescription.xml` *before* calling `pymvr` at all; only call `pymvr.GeneralSceneDescription` on bytes already proven safe (if `pymvr` is never reached when the pre-check fails, its unguarded internal re-parse is provably redundant, not a gap).
**Warning signs:** None visible at the UI layer until a malicious or corrupted `.mvr` triggers a hang/crash/XXE read — this must be caught by a dedicated test (billion-laughs / oversized-archive fixtures), not discovered by a user.

### Pitfall 4: The "IBM PC encoding" `cp437` round-trip on `GDTFSpec` text

**What goes wrong:** `BaseChildNode._read_xml` (lines 482-485, read this session) does `self.gdtf_spec = self.gdtf_spec.encode("utf-8").decode("cp437")` on every `<GDTFSpec>` element's text, with an inline comment "IBM PC encoding." A manufacturer/fixture name containing non-ASCII characters (e.g. accented Latin letters common in European manufacturer names) could, in principle, round-trip incorrectly if Python's `zipfile` module's own default member-name decoding (also historically `cp437` unless the UTF-8 flag bit is set) doesn't agree byte-for-byte with this transform.
**Why it happens:** MVR's spec inherited a legacy DOS-codepage assumption for zip member names from the broader zip-format ecosystem; `pymvr` replicates it for the `<GDTFSpec>` text specifically so it matches the zip member name Python's own `zipfile.namelist()` will report.
**How to avoid:** Always perform the embedded-GDTF lookup via exact string match against `zf.namelist()` (as Pattern 3 above does) rather than re-deriving or re-encoding the filename independently — let both sides of the comparison go through the same (already-tested, already-shipped) library code. Add a test fixture with a non-ASCII manufacturer name to `tests/core/test_mvr_repository.py` to catch any future regression here.
**Warning signs:** A fixture type showing up in the dedup list with `gdtf_spec not in zf.namelist()` (member not found) specifically when the manufacturer/model name has non-ASCII characters.

### Pitfall 5: Marking a non-numeric attribute "important" doesn't fit the direction+tolerance model at all

**What goes wrong:** Several attributes `core/extract.py` already surfaces are enums or free text, not numbers: `BeamType` (Wash/Spot/Beam/...), and every DMX-attribute-definition property (`Pretty`, `Feature`, `ActivationGroup`, `MainAttribute`, `PhysicalUnit`, `Color`). "Higher/lower/closer-to-target" and a numeric tolerance have no meaning for `BeamType == "Wash"` vs `"Spot"`.
**Why it happens:** `05-CONTEXT.md` D-05/D-06 were written with physical-spec attributes in mind (weight, lumens, beam angle — all of `core/extract.py`'s `BEAM_ATTRIBUTES`/`MODEL_ATTRIBUTES`/Weight are numeric), but the requirements-editor UI will inevitably expose the *entire* existing attribute catalog (same one `gui/attribute_picker.py` already shows), including the non-numeric categories.
**How to avoid:** This research proposes (see Open Questions below) an "exact-match" fallback mode for non-numeric attributes — green if the candidate's value equals the target exactly, red otherwise, no yellow state — but this is a genuine open design question, not a settled decision, and D-10 explicitly asked for it to be raised. Confirm with the user before implementation.
**Warning signs:** A direction dropdown rendered for an attribute where "higher is better" is nonsensical (e.g. `PhysicalUnit`).

### Pitfall 6: An attribute marked "important" whose target fixture never declared a value

**What goes wrong:** `core/extract.py`'s presence-check semantics mean many (category, attribute) pairs legitimately resolve to `None` ("N/A") for a given fixture — the manufacturer's GDTF simply didn't declare that attribute. If the requirements editor lets the LD mark such an attribute "important," there is no target value to score candidates against.
**Why it happens:** The requirements editor's attribute catalog is the same `core.comparator.attribute_catalog()` output already used for the Attributes panel — it lists every attribute *name* seen across the loaded fixture, not just the ones with a non-`None` value for *this specific* fixture type.
**How to avoid:** Filter the requirements-editor's eligible attribute list to only (category, attribute) pairs where this specific imported fixture type's extracted value is non-`None`, mirroring the existing `missing_attributes()` helper's "is this pair actually available" check in `core/profile_repository.py`.
**Warning signs:** A saved requirements file containing a `target_value: null` entry with a direction and tolerance that can never be evaluated.

## Code Examples

### Hardening a `.mvr` archive before `pymvr` ever sees it (proposed shape, extending `core/hardening.py`)

```python
# Proposed shape — generalizes the EXISTING extract_description_bytes()/
# parse_description_safely() in core/hardening.py (read this session) to take
# a member name + size-limit parameter, rather than hand-rolling a second
# zip-bomb-guarded reader for MVR. Constants (MAX_MVR_FILE_BYTES etc.) are
# new and [ASSUMED] — no production MVR file size data exists yet to tune
# them against, exactly the same posture as hardening.py's own existing
# [ASSUMED] GDTF constants ("per RESEARCH A1 -- unbenchmarked reasonable
# defaults; tune here only if real-world fixtures trip them").

GSD_XML_MEMBER = "GeneralSceneDescription.xml"
MAX_MVR_FILE_BYTES = 500 * 1024 * 1024          # [ASSUMED]
MAX_GSD_XML_BYTES = 64 * 1024 * 1024             # [ASSUMED] — same as MAX_DESCRIPTION_XML_BYTES
MAX_EMBEDDED_GDTF_BYTES = MAX_GDTF_FILE_BYTES    # reuse GDTF's own existing limit per member

def prevalidate_mvr_document(path: str) -> "ValidatedMVR":
    """Same three-step shape as prevalidate_gdtf_document(): read once,
    extract+size-check the named member, defusedxml-parse it. Returns both
    the full validated archive bytes (for pymvr AND for later embedded-.gdtf
    extraction) and the parsed <GeneralSceneDescription> root element."""
    data = read_bytes_with_limit(path, MAX_MVR_FILE_BYTES)          # generalize read_gdtf_bytes
    xml_bytes = extract_member_bytes(data, GSD_XML_MEMBER, MAX_GSD_XML_BYTES, path)
    root = parse_xml_safely(xml_bytes, path)                        # generalize parse_description_safely
    return ValidatedMVR(archive_bytes=data, description_root=root)
```

### Feeding an embedded `.gdtf` member through the existing GDTF pipeline (proposed shape)

```python
# Proposed shape — core/repository.py's FixtureRepository.load(path) takes a
# file path; this phase needs a bytes-accepting sibling entry point so the
# SAME hardening + pygdtf + extract_attributes pipeline can run on bytes
# already extracted from the MVR zip (no second disk round-trip, no
# temporary file — core/ is still forbidden from importing tempfile/shutil).

def load_gdtf_bytes(data: bytes, label: str) -> "FixtureModel":
    """Sibling to FixtureRepository.load(path): runs the identical
    prevalidate -> pygdtf.FixtureType(io.BytesIO(...)) -> extract_attributes
    pipeline on already-in-memory bytes (e.g. extracted from an MVR zip
    member) instead of reading a path from disk. `label` is used only for
    error messages (e.g. the gdtf_spec filename), the same role `path` plays
    in the existing GDTFError.file_name property."""
    validated = prevalidate_gdtf_bytes(data, label)   # generalize prevalidate_gdtf_document
    with pygdtf.FixtureType(io.BytesIO(validated.archive_bytes)) as fixture_type:
        attributes = extract_attributes(fixture_type, validated.description_root)
        return FixtureModel(
            source_path=label,
            name=fixture_type.name or label,
            manufacturer=fixture_type.manufacturer or "",
            attributes=attributes,
            fixture_type=fixture_type,
        )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|-------------------|---------------|--------|
| GDTF/MVR comparison tools built around "compare two files and show diffs" (this project's Phases 1-3) | "Fixture substitution" as a named workflow (mark requirements, share a sidecar spec, score candidates) | This phase (2026-10-24 scope redefinition) | New business concept for this codebase; no prior pattern to reuse beyond the generic diff/compare machinery already built |
| `.mvr` files handled only by full MVR-xchange networking stacks (BlenderDMX etc.) | File-based, offline `.mvr` import via `pymvr` with no networking at all | `05-CONTEXT.md` D-01 (2026-10-24) — networking explicitly deferred to v2 | Simpler, smaller attack surface; no mDNS/socket code in this phase at all (the existing `tests/test_architecture.py`'s `test_no_network_modules_in_package` guard will automatically catch an accidental regression) |

**Deprecated/outdated:** Nothing in this phase deprecates prior project work — Phases 1-3's parsing/comparison/profile machinery is extended, not replaced.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Smart-default direction for `PowerConsumption` is "lower is better" | Smart Default Direction Table (Open Questions) | LD disagrees that lower power draw is always preferable (e.g. some contexts want to match power draw, not minimize it) — low risk since it's overridable per D-05, but the *default* could annoy users if wrong often |
| A2 | Smart-default direction for `ColorTemperature`, `FieldAngle`, and per-model `Width`/`Height`/`Length` is "closer to target" | Smart Default Direction Table | Same as A1 — overridable, but a wrong-feeling default on common attributes could erode trust in the "smart default" feature |
| A3 | Non-numeric attributes (`BeamType`, DMX-attribute-definition properties) fall back to an "exact-match, two-state (no yellow)" scoring mode rather than being excluded from the requirements editor entirely | Pitfall 5 / Open Questions | If the user actually wants these excluded (or wants a different treatment, e.g. a fuzzy string match), the UI/data-model shape built on this assumption would need rework |
| A4 | The single tolerance value (D-06) splits into a green/yellow boundary at `tolerance * 0.5` for "closer-to-target" attributes, and the target value itself is the natural green/yellow boundary (no split needed) for "higher/lower is better" attributes | Scoring Algorithm (Open Questions) | This is pure interpolation of an ambiguous requirement — a wrong guess here changes which candidates show green vs yellow, a user-visible correctness issue, not just a styling one |
| A5 | "Unique GDTF fixture type" (D-02) is deduplicated by `fixture.gdtf_spec` string alone, ignoring `gdtf_mode` (DMX personality) | Anti-Patterns / Pattern 3 | If the user actually wants one entry per (GDTF file, DMX mode) combination, the dedup key and the resulting fixture-type count shown to the user would both be wrong |
| A6 | `pymvr==1.0.7`'s hardening gaps (Pitfalls 1-3) are exhaustive — i.e., no *other* unguarded entry point exists in the library beyond `_find_root`'s `ElementTree.fromstring` call | Common Pitfalls | `pymvr` is 1958 lines; this session read the top ~900 lines and the class list in full, but did not line-by-line audit every `to_xml`/writer method (irrelevant to this phase's read-only import use case) — a residual, low-probability gap in an unaudited code path is possible |
| A7 | Default size constants for MVR hardening (`MAX_MVR_FILE_BYTES` etc.) follow the same "unbenchmarked reasonable default" posture as the existing GDTF constants, scaled up roughly 5x to account for an MVR bundling many embedded GDTFs | Code Examples | No real-world MVR show file was available to benchmark against this session; a real large show (100+ unique fixture types, each with full GDTF profiles including 3D models) could plausibly exceed a 500MB default |

**If this table is empty:** N/A — assumptions exist and are listed above; several require explicit user/planner confirmation before implementation (see Open Questions).

## Open Questions

1. **How does a single per-attribute tolerance (D-06) produce three states (green/yellow/red, D-10)?**
   - What we know: D-06 locks "one tolerance value per attribute, not global." D-10 locks a three-state indicator per attribute. D-10 itself anticipates this tension: "Ask the user for clarification on edge-case attribute types during planning/research if the direction+threshold model doesn't cleanly fit."
   - What's unclear: Whether the LD is expected to picture tolerance as "the yellow boundary, red is everything worse" (one real boundary, which is what this research assumed — A4 above) or something else (e.g. a percentage band split symmetrically, or a UI that actually asks for two numbers despite D-06's "its own tolerance" wording).
   - Recommendation: Confirm assumption A4's exact boundary math with the user during `/gsd-discuss-phase` or a plan-time `checkpoint:human-verify`, showing a concrete worked example (e.g. "Weight target 15kg, tolerance 2kg — candidate at 14kg is green, 16.5kg is yellow, 20kg is red") before the scoring module is implemented.

2. **Do non-numeric attributes (BeamType, DMX-definition metadata) even belong in the requirements editor?**
   - What we know: The requirements editor will naturally expose the same attribute catalog the Attributes panel already shows (Beam, Physical Properties, and every `DMX: <feature group>` category) — some of these are plainly non-numeric.
   - What's unclear: Whether the LD actually wants to mark, say, `BeamType` as "important" at all (exact-match fallback, assumption A3), or whether the requirements editor should simply scope itself to Beam + Physical Properties numeric attributes only (mirroring `DEFAULT_SELECTED_CATEGORIES`) and exclude DMX-definition metadata entirely.
   - Recommendation: Default to including all attributes with the exact-match fallback for non-numeric ones (keeps the editor consistent with the existing picker's full catalog), but flag this for explicit confirmation — excluding DMX categories entirely would simplify both the UI and the scoring algorithm meaningfully if the user doesn't need them.

3. **What happens when a fixture's referenced GDTF (`gdtf_spec`) is not actually bundled in the `.mvr` zip?**
   - What we know: This is a real, reachable case (a show file can reference a GDTF the exporting software failed to embed, or the file was hand-edited). Pattern 3 above proposes skipping that fixture type and reporting it, never crashing the whole import.
   - What's unclear: Whether the user wants a way to *manually* supply the missing `.gdtf` file for that one fixture type (browse-to-file fallback) rather than simply losing that fixture type from the workflow entirely.
   - Recommendation: Ship the skip-and-report behavior for the MVP (matches D-13's "no online GDTF database" scope-limiting spirit — don't build a recovery UI for a rare case this phase), but mention the gap explicitly in the UI (e.g. "3 fixture types could not be imported — their GDTF file was not found in this MVR") so it's not a silent data loss.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 + pytest-qt 4.5.0 (both already pinned in `pyproject.toml[project.optional-dependencies.dev]`) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` — `testpaths = ["tests"]`, `pythonpath = ["src"]`, `addopts = "--import-mode=importlib -ra"`, `qt_api = "pyside6"` |
| Quick run command | `pytest tests/core/test_mvr_repository.py tests/core/test_mvr_hardening.py tests/core/test_requirements_repository.py tests/core/test_substitution.py` |
| Full suite command | `pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|---------------------|---------------|
| PARSE-02 | `.mvr` file parses via `pymvr`, embedded GDTF extracted and attribute-correct | unit | `pytest tests/core/test_mvr_repository.py -x` | ❌ Wave 0 |
| SUB-01 | Import yields one entry per unique `gdtf_spec`, not per fixture instance; nested `GroupObject` fixtures included | unit | `pytest tests/core/test_mvr_repository.py::test_dedup_by_gdtf_spec -x` | ❌ Wave 0 |
| SUB-01 | Malformed/oversized/XXE-bearing `.mvr` rejected with a friendly typed error, never a bare `AttributeError`/`KeyError` | unit | `pytest tests/core/test_mvr_hardening.py -x` | ❌ Wave 0 |
| SUB-02 | Marking an attribute important captures direction (with correct smart default) and tolerance, independently per fixture type | unit (core data model) + gui | `pytest tests/core/test_substitution.py::test_requirement_model -x` and `pytest tests/gui/test_requirements_editor.py -x` | ❌ Wave 0 |
| SUB-03 | Export writes a sidecar file scoped to one fixture (not the whole MVR); a fresh `requirements_repository.load_requirements()` call in a separate process/session round-trips it exactly | unit | `pytest tests/core/test_requirements_repository.py -x` | ❌ Wave 0 |
| SUB-04 | Candidate folder scan scores each `.gdtf` found against loaded requirements with correct 3-state per attribute, ranked best-first | unit | `pytest tests/core/test_substitution.py::test_score_and_rank -x` | ❌ Wave 0 |
| SUB-04 | Three-state colors actually paint in the GUI (not silently suppressed by qt-material's stylesheet, per the Phase 2 `BackgroundBrushDelegate` finding) | gui (pytest-qt) | `pytest tests/gui/test_candidate_results.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** the relevant new test file(s) from the Quick run command above.
- **Per wave merge:** `pytest` (full suite) — must stay green; this also re-runs `tests/test_architecture.py` against every new `core`/`gui` module automatically, with zero changes needed to that test file.
- **Phase gate:** Full suite green before `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] `tests/core/test_mvr_hardening.py` — covers PARSE-02's size/zip-bomb/XXE guard
- [ ] `tests/core/test_mvr_repository.py` — covers SUB-01 (dedup, nested-GroupObject walk, embedded-GDTF extraction, missing-reference handling)
- [ ] `tests/core/test_requirements_repository.py` — covers SUB-03 (atomic sidecar write/read, schema versioning, single-fixture scope)
- [ ] `tests/core/test_substitution.py` — covers SUB-02 (direction/tolerance data model) and SUB-04 (scoring + ranking math)
- [ ] `tests/gui/test_mvr_import.py`, `tests/gui/test_requirements_editor.py`, `tests/gui/test_candidate_results.py` — GUI-level coverage (pytest-qt), including the 3-state-color-actually-paints check
- [ ] `tests/conftest.py` — add a `make_mvr` fixture (bundling a synthetic `GeneralSceneDescription.xml` + embedded `.gdtf` members into a zip) mirroring the existing `make_gdtf`/`build_description_xml` helpers; this is required before any of the above tests can be written
- [ ] Framework install: none — pytest/pytest-qt are already pinned; only the new runtime dependency `pymvr==1.0.7` needs adding (behind the Package Legitimacy checkpoint above)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|-----------------|---------|---------------------|
| V2 Authentication | No | Desktop, local-file app; no auth surface in this phase |
| V3 Session Management | No | No sessions |
| V4 Access Control | No | Single-user local app; no multi-tenant data |
| V5 Input Validation | **Yes** | Every externally-sourced file (`.mvr`, embedded `.gdtf` members, candidate-folder `.gdtf` files, the requirements sidecar `.json`) must be size-capped and schema/shape-validated before being trusted, mirroring `core/hardening.py`'s existing GDTF pattern exactly |
| V6 Cryptography | No | No cryptographic operations introduced this phase |
| V12 File & Resource Handling *(ASVS 4.x numbering)* | **Yes** | No `zipfile.ZipFile.extractall()` anywhere in `core/` (enforced by the existing `tests/test_architecture.py::test_core_never_unpacks_archives_or_uses_temp_dirs` AST guard, which automatically covers new `core/` modules); exact zip-member-name lookups only, capped reads, zip-bomb compression-ratio check reused/extended from `core/hardening.py` |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|------------------------|
| XXE / external-entity injection via `GeneralSceneDescription.xml` (confirmed this session: `pymvr` has no `defusedxml` guard at all) | Tampering / Information Disclosure | Pre-parse with `defusedxml.ElementTree.fromstring(..., forbid_dtd=True, forbid_entities=True, forbid_external=True)` **before** handing bytes to `pymvr`, exactly as `core/hardening.py` already does for `description.xml` |
| Zip-bomb (decompression amplification) via an `.mvr` archive or an embedded `.gdtf` member | Denial of Service | Reuse/extend `core/hardening.py`'s existing total-uncompressed-size and compression-ratio checks (`MAX_TOTAL_UNCOMPRESSED_BYTES`, `MAX_COMPRESSION_RATIO`) for the MVR archive as a whole, and apply the existing per-member `MAX_GDTF_FILE_BYTES` cap to each embedded `.gdtf` member individually |
| Path traversal via a crafted `gdtf_spec` filename (e.g. `../../etc/passwd`) | Tampering | Never use `zipfile.ZipFile.extract()`/`extractall()` (already architecturally forbidden); only ever `zf.open(exact_member_name)` against `zf.namelist()`'s own enumerated names — a traversal string that isn't an exact existing member name simply fails the "not in names" check in Pattern 3 and is skipped, never touches the filesystem outside the zip's own in-memory read |
| Oversized/malicious requirements sidecar `.json` fed back in by the "shop" role (D-07's second, less-trusted role) | Tampering / Denial of Service | Apply the same `MAX_PROFILES_FILE_BYTES`-style size cap and strict schema-version/shape validation `core/profile_repository.py` already uses for `profiles.json`, since this file crosses a trust boundary (authored on one machine, loaded on a different one, by a different person, per D-07) |

## Sources

### Primary (HIGH confidence)
- `pymvr==1.0.7` installed wheel, read and executed directly this session (`pip download pymvr==1.0.7 --no-deps`, extracted, `Read` tool over `pymvr/__init__.py` lines 1-1021, class list for all 1958 lines, plus live execution of test scripts against the real package) — source of every `[VERIFIED: pymvr 1.0.7 source/tested this session]` claim above
- `https://pypi.org/pypi/pymvr/json` and `https://pypi.org/pypi/pygdtf/json` — fetched directly via `curl` this session, confirming `project_urls.Repository` for both packages
- This project's own source, read directly this session: `src/gdtf_comparer/core/hardening.py`, `core/repository.py`, `core/extract.py`, `core/models.py`, `core/comparator.py`, `core/profile_repository.py`, `core/errors.py`, `gui/attribute_picker.py`, `gui/worker.py`, `gui/table_model.py`, `gui/theme.py` (partial), `tests/test_architecture.py`, `tests/conftest.py` (partial), `tests/test_fixture_builder.py`, `pyproject.toml`

### Secondary (MEDIUM confidence)
- `https://raw.githubusercontent.com/open-stage/python-mvr/master/README.md` (WebFetch this session) — confirms the `pymvr.GeneralSceneDescription("mvr_file.mvr")` / `for layer in mvr_file.scene.layers` usage pattern this research also derived independently from the source, and states MVR 1.6 (DIN SPEC 15801:2023-12) coverage
- `05-CONTEXT.md`, `REQUIREMENTS.md`, `STATE.md`, `ROADMAP.md` — this project's own planning artifacts, read directly this session

### Tertiary (LOW confidence)
- Smart-default attribute-direction table beyond the three explicit user-given examples (Weight/LuminousFlux/BeamAngle) — this researcher's domain-knowledge proposal, not verified against any external lighting-industry standard this session; see Assumptions Log A1/A2

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — `pymvr`/`pygdtf` versions and the project's existing dependency pins were read/queried directly this session
- Architecture (MVR parsing + embedded-GDTF extraction): HIGH — every structural claim about `pymvr`'s object tree, zip-embedding model, and failure modes was confirmed by reading the source and/or executing real code against the installed package this session
- Architecture (requirements/scoring data model): MEDIUM — follows existing project patterns closely, but is new ground for this codebase
- Pitfalls (MVR hardening gaps): HIGH — all three library-gap pitfalls were directly observed (source read + live execution), not inferred
- Pitfalls/Open Questions (direction/tolerance scoring semantics): LOW — genuinely unresolved by the user's own locked decisions; flagged for confirmation, not guessed at silently

**Research date:** 2026-10-24
**Valid until:** 30 days (stable domain — `pymvr`/`pygdtf` release infrequently; re-check versions if planning is delayed past late November 2026)
