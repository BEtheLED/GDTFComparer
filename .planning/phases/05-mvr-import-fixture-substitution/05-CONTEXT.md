# Phase 5: MVR Import & Fixture Substitution - Context

**Gathered:** 2026-10-24
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase replaces Phase 5's original "live LAN discovery" framing (see `<decisions>` D-01). The new boundary: a lighting designer (LD) imports a static MVR show file, works through its unique fixture types one at a time marking which attributes matter (with direction and tolerance), exports those requirements as a standalone shareable file, and a second person — potentially a rental shop on a different machine, matching against their own inventory folder — loads that file and sees ranked, traffic-lit substitute candidates. No networking of any kind is involved. `pymvr` is used for MVR parsing (PARSE-02).

</domain>

<decisions>
## Implementation Decisions

### Scope redefinition
- **D-01:** Phase 5 drops the original live-LAN-discovery/MVR-xchange-networking framing (former NET-01/NET-02/NET-03) in favor of a file-based import + fixture-substitution workflow. — **Reversibility:** reversible — live discovery was never built; the old requirements move to REQUIREMENTS.md v2 and can be revisited as their own phase later without touching anything this phase builds.

### MVR import
- **D-02:** Importing an MVR file produces one entry per **unique GDTF fixture type** referenced in the show, not one entry per physical fixture instance (so 24 identical moving heads collapse to a single entry). This list becomes the fixture set for this workflow, replacing manual one-by-one GDTF file browsing.
- **D-03:** The user works through fixtures **one at a time** (pick a fixture type → mark its requirements → optionally search for a replacement), not a batch-everything-up-front mode.

### Per-fixture importance ("requirements")
- **D-04:** Each fixture type gets its own **independent** checklist of important attributes — not one shared/global Compare Profile (ATTR-03) applied uniformly to every fixture. A moving head and a strobe can flag entirely different attributes as important.
- **D-05:** For each attribute marked important, the app suggests a **smart default direction** (higher-is-better, lower-is-better, or closest-to-target-is-best) based on the attribute itself (e.g., weight → lower is better; lumen output → higher is better; beam angle → closest to target). The LD can override the suggested direction per attribute.
- **D-06:** Tolerance (how close counts as "close enough") is set **per attribute by the LD**, not one global tolerance percentage applied to everything. Different attributes can have very different tolerance bands.

### Two-role workflow & sharing
- **D-07:** This is explicitly a **two-role workflow**: the LD imports the MVR and sets requirements per fixture; a separate party (e.g., a rental shop, possibly on a different computer entirely) uses GDTF Comparer with the LD's requirements to check what in *their own* inventory could work. The tool must support both roles running independently, not assume one person/one session does everything.
- **D-08:** The LD's per-fixture requirements (important attributes + direction + tolerance) are saved to a **separate, standalone shareable file** — explicitly **not embedded inside the MVR file itself**. — **Reversibility:** one-way in practice — once a file format for this exists and gets shared externally, changing its shape later is a breaking change for anyone who has saved one. Rationale confirmed by the user from direct prior experience at Vectorworks: custom data bolted onto a spec-governed scene-description format risks being silently dropped or mangled when the file passes through other lighting software (Vectorworks, Capture, MA3, etc.) that only knows the official schema. A sidecar file has no such risk and round-trips cleanly.
- **D-09:** The shop only needs **the one fixture's requirements file** to do their check — never the LD's full MVR (the whole show file, every fixture, every position in the plot). Keep the shared artifact scoped to a single fixture's requirements, not the whole plot.

### Matching & candidate results
- **D-10:** Match results use a **three-state per-attribute indicator**, not a single pass/fail or a single numeric score:
  - 🟢 **Green** — candidate meets or is better than the requirement (per that attribute's direction; note some attributes are "lower is better," so "better" is relative to the direction, not always a larger number).
  - 🟡 **Yellow** — candidate is close; might work.
  - 🔴 **Red** — candidate is well outside the requirement's range; won't work.
  Ask the user for clarification on edge-case attribute types during planning/research if the direction+threshold model doesn't cleanly fit (per the user's own "ask questions if needed" note).
- **D-11:** Candidates are **ranked, best match first** — derived from the per-attribute traffic lights (e.g., most greens / fewest reds ranks higher). The per-attribute lights are the detail view; the ranking is the summary/sort order. These two answers are not in conflict — rank by aggregate light quality, show the individual lights per attribute underneath.

### Candidate library
- **D-12:** Candidate replacement fixtures come from a **local folder of GDTF files the user (shop) already maintains** — their own collected inventory from various manufacturers. The app's job is only to point at that folder and scan the `.gdtf` files in it.
- **D-13:** The app does **not** build any online GDTF database browsing/downloading feature (e.g., querying GDTF-Share) to acquire candidate files — out of scope for this phase. Users are expected to collect their own candidate GDTF files by whatever means they already use, outside the app.

### Claude's Discretion
- Exact on-disk format of the "fixture requirements" file (likely JSON, mirroring the existing `core/profile_repository.py` atomic-write pattern — same-folder temp file + `os.replace`, schema version field, zero Qt in `core/`). Research/planning should verify this pattern transfers cleanly.
- Exact UI flow/screen layout for "mark importance per fixture," "export requirements," "import requirements + pick candidate folder," and the ranked-results view. Follow existing patterns (Attributes side panel, Profiles dropdown/toolbar from Phase 3) where they fit.
- Smart-default direction rules per attribute type (D-05) — Claude should propose sensible defaults per GDTF attribute during planning/research, informed by lighting-domain knowledge (e.g., GDTF `AttributeDefinitions`), and the LD can always override.
- Tie-breaking logic within the ranked list when two candidates have the same green/yellow/red counts.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & roadmap
- `.planning/REQUIREMENTS.md` §"Fixture Substitution (Phase 5, redefined 2026-10-24)" — SUB-01..04, the locked requirements for this phase
- `.planning/REQUIREMENTS.md` §"v2 Requirements" — former NET-01/02/03, deferred, for context on what NOT to build this phase
- `.planning/ROADMAP.md` §"Phase 5: MVR Import & Fixture Substitution" — goal, success criteria, scope-redefinition note

### Existing patterns this phase should reuse or mirror
- `src/gdtf_comparer/core/profile_repository.py` — atomic JSON-file read/write pattern (schema version, `os.replace`, zero Qt/tempfile/shutil in `core/`), explicitly written with "D-01's 'substitute fixture' workflow" in mind already — the natural precedent for the new fixture-requirements file format
- `src/gdtf_comparer/core/comparator.py` — existing attribute comparison engine; the new "score candidate against requirements" logic is a variant of this, not a parallel implementation
- `src/gdtf_comparer/gui/attribute_picker.py` — existing per-attribute checkbox/search UI (Attributes panel); the new "mark important attributes per fixture" UI should look and behave consistently with this

No other external specs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `core/profile_repository.py`: atomic single-JSON-file repository pattern (`APP_DATA_DIR_NAME`, `PROFILES_SCHEMA_VERSION`, `os.open(O_EXCL)`-based atomic write) — reuse this shape for the new fixture-requirements repository, including its own schema version so an older app build never silently misreads a newer file.
- `core/comparator.py`: the existing diff/comparison engine between a target and comparison GDTFs — candidate-scoring logic should extend or sit alongside this, not duplicate it.
- `gui/attribute_picker.py`: existing attribute search/checkbox panel (ATTR-01/02) — likely reusable UI chrome for "mark this attribute important."

### Established Patterns
- `core/` has zero Qt imports and a strict architecture guard (`tests/test_architecture.py`) forbidding `tempfile`/`shutil` — any new fixture-requirements persistence code must follow the same constraint.
- Profiles are one atomic file keyed by name (Phase 3 D-02/D-03/D-07) rather than many small files — consider whether fixture requirements should follow the same "one file, many keyed entries" shape or be genuinely one-file-per-fixture (needed for the sharing use case in D-08/D-09, since a shop needs to receive exactly one fixture's requirements, not the LD's whole local store).

### Integration Points
- MVR import (SUB-01) is a new parsing entry point alongside the existing GDTF `repository.py`/`extract.py` — needs its own module using `pymvr`, feeding fixture-type metadata into the existing compare/attribute-selection UI rather than replacing it.
- The candidate-folder scan (SUB-04) reuses existing GDTF parsing (`core/repository.py`, `core/extract.py`) against every `.gdtf` file found in a user-chosen folder.

</code_context>

<specifics>
## Specific Ideas

- The three-state match indicator was specified by the user in exact terms: "3 light system, green meets or is better (note some fields might be lower is better) yellow it's close so it might work. Red way outside the set range will not work." This phrasing should carry through to planning/research verbatim as the acceptance bar for the matching UI.
- The user has direct professional experience (worked at Vectorworks) that informed the decision to keep the requirements file separate from the MVR rather than embedding custom data in it — treat D-08 as well-grounded, not merely cautious.

</specifics>

<deferred>
## Deferred Ideas

- **Live LAN discovery of other MVR-xchange stations** (formerly NET-01) — moved to REQUIREMENTS.md v2. May become its own future phase.
- **Live MVR pull from a discovered station over the network** (formerly NET-02) — moved to REQUIREMENTS.md v2, same reasoning.
- **Built-in browsing/downloading of an online GDTF database** (e.g. GDTF-Share integration to acquire candidate fixtures) — explicitly out of scope per D-13; the user manages their own candidate-file folder.

### Reviewed Todos (not folded)
None — discussion stayed within phase scope.

</deferred>

---

*Phase: 5-MVR Import & Fixture Substitution*
*Context gathered: 2026-10-24*
