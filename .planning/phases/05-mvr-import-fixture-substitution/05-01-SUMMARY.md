---
phase: 05-mvr-import-fixture-substitution
plan: 01
subsystem: mvr-import-substitution
tags: [pymvr, mvr, requirements, fixture-substitution, pyside6, defusedxml]

requires:
  - phase: 01-foundation-rebuild
    provides: core.hardening's GDTF prevalidation pipeline, core.repository.FixtureRepository, GDTFError hierarchy
  - phase: 02-attribute-browsing-diff-highlighting
    provides: core.comparator.compare(), gui.table_model.BackgroundBrushDelegate
provides:
  - MVR import into unique fixture types via pymvr, hardened the same way GDTF files are (core.mvr_repository)
  - Per-attribute requirement marking with direction + tolerance (core.substitution)
  - Atomic, shareable requirements sidecar file format v1 (core.requirements_repository)
  - Green/yellow/red folder-scan ranking against a loaded requirements file
  - Find Substitutes... entry point and two-tab window on the main app
affects: [05-02-mvr-import-hardening, 05-03-requirements-editor-widening, 05-04-requirements-file-safety, 05-05-substitution-scoring-widening]

actuals:
  tokens: 95000
  tasks: 1
  commits: 1

tech-stack:
  added: [pymvr==1.0.7]
  patterns:
    - "File-kind-parameterized hardening (_FileKind/_read_file_bytes/_extract_member_bytes/_parse_xml_safely) shared between GDTF and MVR instead of a second hardening module"
    - "bytes-accepting sibling entry point (FixtureRepository.load_bytes / prevalidate_gdtf_bytes) for parsing an already-in-memory archive member without touching disk"

key-files:
  created:
    - src/gdtf_comparer/core/mvr_repository.py
    - src/gdtf_comparer/core/substitution.py
    - src/gdtf_comparer/core/requirements_repository.py
    - src/gdtf_comparer/gui/requirements_editor.py
    - src/gdtf_comparer/gui/candidate_results.py
    - src/gdtf_comparer/gui/substitution_window.py
    - tests/gui/test_substitution_round_trip.py
  modified:
    - pyproject.toml
    - src/gdtf_comparer/core/errors.py
    - src/gdtf_comparer/core/hardening.py
    - src/gdtf_comparer/core/repository.py
    - src/gdtf_comparer/gui/worker.py
    - src/gdtf_comparer/gui/main_window.py
    - tests/conftest.py
    - tests/test_architecture.py

key-decisions:
  - "Task 1 (package legitimacy checkpoint): user approved pymvr==1.0.7 after visually verifying its PyPI page (title, description, author 'vanous') and its github.com/open-stage/python-mvr repository against the already-trusted pygdtf's PyPI page, which the Credits section confirms is maintained by the same 'vanous' under the same Open-Stage organization."
  - "Task 2 (tolerance semantics, one-way door D-08/D-10): user chose option a -- the tolerance is the outer 'might still work' limit, in the attribute's own units. Higher/lower-is-better: green = equal to or better than target, yellow = worse but within tolerance, red beyond. Closest-to-target: green = within half the tolerance, yellow = within the full tolerance. Implemented as core.substitution.TOLERANCE_KIND = 'absolute', CLOSEST_GREEN_FACTOR = 0.5, CLOSEST_YELLOW_FACTOR = 1.0."
  - "hardening.py generalized rather than duplicated: _FileKind(label, validation_error, unsafe_error) parameterizes _read_file_bytes/_extract_member_bytes/_parse_xml_safely so GDTF and MVR share one zip-bomb/XXE-guarded pipeline; all 14 pre-existing tests/core/test_hardening.py assertions pass unchanged, confirming message text was reproduced word for word."
  - "import_summary_message's fixture count sums only the successfully imported fixture_types' instance_count (not skipped ones), since the sentence reads 'Found N types (M fixtures)' about the found types specifically."

requirements-completed: [PARSE-02, SUB-01, SUB-02, SUB-03, SUB-04]

coverage:
  - id: D1
    description: "pymvr==1.0.7 installed only after a human-approved legitimacy checkpoint, pinned as the 5th pyproject.toml dependency"
    requirement: PARSE-02
    verification:
      - kind: unit
        ref: "command invocation: python -c \"import importlib.metadata as m; assert m.version('pymvr') == '1.0.7'\""
        status: pass
    human_judgment: true
    rationale: "The legitimacy review itself (Task 1) was a human checkpoint approved in this session -- recorded here, not re-verifiable by an automated test."
  - id: D2
    description: "MVR import collapses two fixture instances referencing the same GDTF (one direct, one nested in a GroupObject) into one fixture-type entry with the right instance count, via the generalized hardening pipeline"
    requirement: SUB-01
    verification:
      - kind: e2e
        ref: "tests/gui/test_substitution_round_trip.py#test_ld_to_shop_round_trip"
        status: pass
    human_judgment: false
  - id: D3
    description: "An LD can mark one attribute with a direction and tolerance in the requirements editor, and the default direction/tolerance seed correctly"
    requirement: SUB-02
    verification:
      - kind: e2e
        ref: "tests/gui/test_substitution_round_trip.py#test_ld_to_shop_round_trip"
        status: pass
    human_judgment: false
  - id: D4
    description: "Requirements save atomically to a sidecar file with exactly the specified fields (no MVR mutation, no extraneous data) and reload correctly in a fresh, independent window"
    requirement: SUB-03
    verification:
      - kind: e2e
        ref: "tests/gui/test_substitution_round_trip.py#test_ld_to_shop_round_trip"
        status: pass
    human_judgment: false
  - id: D5
    description: "Scanning a folder of three candidate GDTFs against the loaded requirements ranks them green/yellow/red in the correct best-first order, painted via BackgroundBrushDelegate"
    requirement: SUB-04
    verification:
      - kind: e2e
        ref: "tests/gui/test_substitution_round_trip.py#test_ld_to_shop_round_trip"
        status: pass
    human_judgment: false
  - id: D6
    description: "Find Substitutes... button on the main window opens a single SubstitutionWindow (opens once, re-raises on a second click) without disturbing the existing compare workflow"
    verification:
      - kind: e2e
        ref: "tests/gui/test_substitution_round_trip.py#test_find_substitutes_button_opens_one_window"
        status: pass
    human_judgment: false
  - id: D7
    description: "'Check Inventory With These...' sends the Set Requirements tab's currently checked attributes to the Check Inventory tab and switches to it in the same session"
    verification:
      - kind: e2e
        ref: "tests/gui/test_substitution_round_trip.py#test_check_inventory_with_these_sends_current_requirements"
        status: pass
    human_judgment: false

duration: 45min
completed: 2026-10-24
status: complete
---

# Phase 5 Plan 1: MVR Import & Fixture Substitution Tracer Summary

**End-to-end MVR-to-substitution slice: pymvr import collapsing duplicate fixture instances, per-attribute requirement marking with a direction and tolerance, an atomic shareable sidecar file, and a folder scan ranked green/yellow/red through a new Find Substitutes window.**

## Performance

- **Duration:** ~45 min (estimated; not precisely timed in this session)
- **Completed:** 2026-10-24T17:54:31-04:00
- **Tasks:** 3 (1 human-verify checkpoint, 1 decision checkpoint, 1 tracer implementation task)
- **Files modified:** 15 (7 created, 8 modified)

## Accomplishments

- pymvr 1.0.7 installed and pinned after a human legitimacy review (Task 1 checkpoint: approved).
- The tolerance semantics for green/yellow/red scoring decided by the user (Task 2 checkpoint: option a) and implemented as `core.substitution`'s three named constants.
- `core/hardening.py` generalized (not duplicated) to share one zip-bomb/XXE-guarded pipeline between GDTF and MVR files, parameterized by a `_FileKind`. All 14 pre-existing `tests/core/test_hardening.py` assertions pass unchanged, proving every GDTF message is reproduced word for word.
- New `core.mvr_repository.import_mvr()` walks an MVR's full fixture tree (including fixtures nested inside `GroupObject`), deduplicates by GDTF file reference, and loads each embedded GDTF through the existing hardening + pygdtf pipeline via a new `FixtureRepository.load_bytes()` sibling entry point — nothing is ever unpacked to disk.
- New `core.substitution` scores a candidate's value against a marked requirement (direction + tolerance) into green/yellow/red, and ranks candidates deterministically.
- New `core.requirements_repository` saves/loads a one-fixture-type sidecar file atomically (same `os.open(O_EXCL)` + `fsync` + `os.replace` pattern as `core.profile_repository`), carrying only the fields D-09 allows.
- New GUI: `RequirementsEditor`, `CandidateResultsModel` (painted via the existing `BackgroundBrushDelegate`), and `SubstitutionWindow` with its two tabs ("1. Set Requirements" / "2. Check Inventory"), wired to two new QThread workers (`MVRImportWorker`, `CandidateScanWorker`) so neither the import nor the folder scan blocks the GUI thread.
- A new "Find Substitutes…" button on the main window opens (or re-raises) the single `SubstitutionWindow`, leaving the existing compare workflow untouched.

## Task Commits

This plan's Task 1 and Task 2 were human checkpoints with no code to commit (recorded as decisions below). Task 3 (the tracer) was committed as one atomic commit, per its single `type="tracer"` nature:

1. **Task 3: End-to-end MVR import → fixture substitution round trip** - `1130e7e` (feat)

**Plan metadata:** (this SUMMARY + STATE/ROADMAP/REQUIREMENTS updates, committed separately)

## Files Created/Modified

- `src/gdtf_comparer/core/mvr_repository.py` - MVR import, fixture-tree walk, dedup-by-GDTF-spec
- `src/gdtf_comparer/core/substitution.py` - Direction/MatchState scoring, ranking, folder scan
- `src/gdtf_comparer/core/requirements_repository.py` - Atomic sidecar file save/load
- `src/gdtf_comparer/gui/requirements_editor.py` - Checkable per-attribute requirement tree
- `src/gdtf_comparer/gui/candidate_results.py` - Ranked-candidates table model
- `src/gdtf_comparer/gui/substitution_window.py` - Two-tab Find Substitutes window
- `tests/gui/test_substitution_round_trip.py` - End-to-end round-trip tests
- `pyproject.toml` - Added `pymvr==1.0.7` as the 5th runtime dependency
- `src/gdtf_comparer/core/errors.py` - Added MVRError/MVRValidationError/MVRUnsafeFileError/MVRParseError and SubstitutionError/RequirementsFileError/CandidateFolderError
- `src/gdtf_comparer/core/hardening.py` - Generalized to `_FileKind`-parameterized helpers shared by GDTF and MVR; added MVR constants, `ValidatedMVR`, `prevalidate_gdtf_bytes`, `prevalidate_mvr_document`, `read_mvr_member_bytes`
- `src/gdtf_comparer/core/repository.py` - Added `FixtureRepository.load_bytes()` / `_model_from_validated()`
- `src/gdtf_comparer/gui/worker.py` - Added `MVRImportWorker` and `CandidateScanWorker`
- `src/gdtf_comparer/gui/main_window.py` - Added `substitutes_button`, `substitution_window`, `open_substitution_window()`
- `tests/conftest.py` - Added `build_gdtf_bytes`, `fixture_xml`, `build_scene_xml`, `make_mvr` fixture
- `tests/test_architecture.py` - Added the three new core modules to `APPROVED_CORE_SURFACE` and `"pymvr"` to `PARSING_LIBRARY_TOP_LEVELS`

## Decisions Made

**Task 1 — Package legitimacy review (blocking-human checkpoint): APPROVED.**
User visually verified:
- https://pypi.org/project/pymvr/1.0.7/ — title "pymvr 1.0.7", description "My Virtual Rig (MVR) library for Python", author "vanous".
- Its "Repository" project link → https://github.com/open-stage/python-mvr, owned by "open-stage".
- https://pypi.org/project/pygdtf/ (already-trusted) — Credits section confirms "vanous" forked it under the Open-Stage organization and still publishes it; "vanous" is listed as a maintainer. Same author, same organization.
- Spelling confirmed exactly "pymvr" (not a near-miss).

`pip show pymvr` output after install:
```
Name: pymvr
Version: 1.0.7
Summary: My Virtual Rig (MVR) library for Python
Author-email: vanous <noreply@nodomain.com>
License:
Location: /Users/brandon/GDTFComparer/.venv/lib/python3.12/site-packages
Requires:
Required-by:
```

**Task 2 — Tolerance semantics decision (one-way door, D-08/D-10): Option A.**
"Tolerance is the 'might still work' limit, typed in the attribute's own units." No change requested to the file-layout description. Implemented in `core/substitution.py`:
```python
TOLERANCE_KIND = "absolute"
CLOSEST_GREEN_FACTOR = 0.5
CLOSEST_YELLOW_FACTOR = 1.0
```
Rules: higher/lower-is-better — green = equal to or better than target, yellow = worse but within tolerance, red beyond. Closest-to-target — green = within half the tolerance, yellow = within the full tolerance, red beyond. A value landing exactly on a boundary always takes the better color (`_at_most`'s `math.isclose` tolerance).

## Deviations from Plan

None - plan executed exactly as written. The one ambiguity not pinned down by the plan text (whether `import_summary_message`'s fixture count sums imported-only or imported+skipped instance counts) was resolved by reading the surrounding sentence structure ("Found N types (M fixtures)" describing the found types) rather than treated as a deviation, since no test exercises the exact wording.

## Issues Encountered

None. All three `<verify>` commands (pymvr version check, the new test file alone, the full suite with `-W error::DeprecationWarning`) and every `<acceptance_criteria>` grep/git-diff check passed on the first attempt after implementation — no node-repair cycles were needed.

## User Setup Required

None - no external service configuration required. The one new dependency (`pymvr==1.0.7`) is a pure-Python package with no further runtime dependencies, already installed in the shared venv.

## Next Phase Readiness

This tracer proves the full path through every layer Phase 5 touches: hardening, pymvr, the embedded-GDTF pipeline, the requirements model, the sidecar file, the folder scan, scoring and the delegate-painted ranked table. Ready for:
- **Wave 2 (05-02, 05-03, 05-04 — all depend on this plan, run in parallel):** 05-02 hardens MVR import against real show files (every fixture found regardless of nesting, accented GDTF names, damaged files, single-flight imports, clean shutdown). 05-03 widens the requirements editor into the LD's real working surface (per-type memory, search, a per-attribute defaults table). 05-04 hardens the requirements file against a damaged, foreign or newer file and strict per-field validation.
- **Wave 3 (05-05 — depends on 05-02 and 05-03):** widens scoring, ranking, failure rows and readability in the Check Inventory results.

No blockers. The contracts this plan created (`Direction`, `MatchState`, `RequirementSet`, `FixtureTypeEntry`, the requirements-file JSON shape, etc. — see this plan's `<interfaces>` block) are the ones Plans 05-02 through 05-05 build on exactly, without renaming or duplicating.

---
*Phase: 05-mvr-import-fixture-substitution*
*Completed: 2026-10-24*
