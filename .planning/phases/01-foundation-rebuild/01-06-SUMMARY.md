---
phase: 01-foundation-rebuild
plan: 06
subsystem: core-extraction
tags: [gdtf, pygdtf, xml-presence-detection, comparator, defusedxml, lockstep-alignment]
requires:
  - phase: 01-foundation-rebuild (01-03)
    provides: namespaced per-GeometryBeam/per-Model attribute extraction (BEAM_ATTRIBUTES, MODEL_ATTRIBUTES, iter_geometry_paths, _unique_path)
  - phase: 01-foundation-rebuild (01-04)
    provides: core.hardening.prevalidate_gdtf pre-parse gate and the GDTFError typed-error hierarchy this plan wraps DescriptionMismatchError into
provides:
  - "core.hardening.ValidatedGDTF / prevalidate_gdtf_document: single-read validated bytes + parsed <GDTF> tree"
  - "core.extract.DescriptionMismatchError, _weight_declared, _geometry_children"
  - "iter_geometry_paths(fixture_type, fixture_type_element) yielding (path, node, element) triples, lockstep-paired via pygdtf's own TAG_TO_GEOMETRY_CLASS filter"
  - "presence-aware extract_attributes: an attribute pygdtf backfills a GDTF-spec default for, but the file never declared, is now None (N/A) instead of the default"
  - "'None = not declared in this file' contract documented on FixtureModel.attributes, format_value and ComparisonRow.any_differs"
affects: [phase-02-attribute-browsing-and-diff-highlighting, phase-03-csv-export]
actuals:
  tokens: 10633
  tasks: 3
  commits: 4
tech-stack:
  added: []
  patterns:
    - "Lockstep tree pairing: walk pygdtf's parsed object model and the defusedxml-validated XML tree with the same child-tag filter (TAG_TO_GEOMETRY_CLASS) side by side, so an attribute's declared-vs-defaulted status is read from the correct paired element; any divergence fails closed (DescriptionMismatchError) instead of guessing."
    - "Presence-over-value detection: never infer 'not specified' from a value equalling a known default; check the raw validated element's attrib keys instead, so a declared value equal to the spec default (e.g. BeamAngle=25) is still shown as declared."
key-files:
  created:
    - tests/gui/test_unspecified_values.py
  modified:
    - src/gdtf_comparer/core/hardening.py
    - src/gdtf_comparer/core/repository.py
    - src/gdtf_comparer/core/extract.py
    - src/gdtf_comparer/core/models.py
    - tests/core/test_extract.py
    - tests/core/test_comparator.py
    - .planning/phases/01-foundation-rebuild/SKELETON.md
    - .planning/phases/01-foundation-rebuild/01-03-PLAN.md
key-decisions:
  - "Presence detection reads the defusedxml-validated tree (already built by core.hardening for RELI-02) rather than re-parsing or adding raw-XML access elsewhere -- one validated read still serves both pygdtf and the presence check (T-01-15 preserved)."
  - "Option (b) from the plan's Decision Record (presence check, undeclared = None/N/A) was implemented over (a) accept-defaults-as-declared or (c) provenance-tagged values; (c) was deferred because it would change the D-13 row shape."
requirements-completed: [PARSE-01]
coverage:
  - id: D1
    description: "Omitted fixture-level Weight is None (N/A), not pygdtf's backfilled 0; a declared Weight of 0.0 is still shown as declared"
    requirement: "PARSE-01"
    verification:
      - kind: unit
        ref: "tests/core/test_extract.py::test_omitted_weight_is_none_not_zero"
        status: pass
      - kind: unit
        ref: "tests/core/test_extract.py::test_declared_zero_weight_is_kept"
        status: pass
      - kind: e2e
        ref: "tests/gui/test_unspecified_values.py::test_omitted_weight_cell_reads_na"
        status: pass
    human_judgment: false
  - id: D2
    description: "Omitted Beam attributes (BeamAngle, FieldAngle, PowerConsumption, LuminousFlux, ColorTemperature, BeamType) are None (N/A) even though pygdtf backfills spec defaults; declared values equal to the spec default are still shown as declared; lockstep pairing skips GeometryReference targets and unknown tags and fails closed (DescriptionMismatchError) on any misalignment"
    requirement: "PARSE-01"
    verification:
      - kind: unit
        ref: "tests/core/test_extract.py::test_omitted_beam_attributes_are_none"
        status: pass
      - kind: unit
        ref: "tests/core/test_extract.py::test_declared_spec_default_values_are_kept"
        status: pass
      - kind: unit
        ref: "tests/core/test_extract.py::test_presence_alignment_skips_references_and_unknown_tags"
        status: pass
      - kind: unit
        ref: "tests/core/test_extract.py::test_mismatched_description_raises"
        status: pass
      - kind: unit
        ref: "tests/core/test_comparator.py::test_both_files_omitting_attribute_show_na_not_default"
        status: pass
      - kind: unit
        ref: "tests/core/test_comparator.py::test_omitted_vs_declared_default_differs"
        status: pass
      - kind: e2e
        ref: "tests/gui/test_unspecified_values.py::test_omitted_beam_attribute_cell_reads_na"
        status: pass
    human_judgment: false
  - id: D3
    description: "Omitted Model dimensions (Width, Height, Length) are None (N/A) per-model, even though pygdtf backfills 0; every model still emits all three keys"
    requirement: "PARSE-01"
    verification:
      - kind: unit
        ref: "tests/core/test_extract.py::test_omitted_model_dimensions_are_none"
        status: pass
    human_judgment: false
  - id: D4
    description: "'None = not declared' contract documented on FixtureModel.attributes/format_value/ComparisonRow.any_differs (docstrings only, no behavior change); SKELETON.md and 01-03-PLAN.md's open prohibition closed in place"
    requirement: "PARSE-01"
    verification:
      - kind: unit
        ref: "grep checks in Task 3 acceptance_criteria (not-declared/EXPORT-02 docstring text, git diff --stat models.py docstring-only, frontmatter.validate on 01-03-PLAN.md)"
        status: pass
    human_judgment: true
duration: 45min
completed: 2026-09-26
status: complete
---

# Phase 01 Plan 06: Presence-Aware Attribute Extraction Summary

**Undeclared GDTF attributes (Beam angles/power/flux/temperature/type, model dimensions, fixture Weight) now render as N/A by checking the validated description.xml tree for presence, instead of trusting pygdtf's silent spec-default backfill (25, 1000, 10000, 6000, "Wash", 0) as if the manufacturer had declared it.**

## Performance
- **Duration:** ~45min
- **Started:** 2026-09-26 (gap-closure batch continuation)
- **Completed:** 2026-09-26
- **Tasks:** 3
- **Files modified:** 9 (1 created, 8 modified)

## Accomplishments
- `core.hardening.prevalidate_gdtf_document` now returns both the validated archive bytes and the parsed `<GDTF>` tree from a single read; `prevalidate_gdtf` keeps its old contract by delegating to it, so `tests/core/test_hardening.py` and `tests/core/test_repository.py` needed zero edits.
- `core.repository.FixtureRepository.load` threads that validated tree into `extract_attributes`, preserving the single-read guarantee (T-01-15).
- `core.extract.iter_geometry_paths` now walks pygdtf's parsed geometry tree and the validated XML tree in lockstep, using pygdtf's own `TAG_TO_GEOMETRY_CLASS` child filter, yielding the paired XML element alongside every node so presence can be checked on the correct element. Any misalignment (tag/type or child-count mismatch) raises `DescriptionMismatchError` instead of guessing.
- Beam and Model extraction now check the paired element's `attrib` for each GDTF attribute name; an attribute absent from the file is `None` regardless of what pygdtf's object model contains, closing 01-VERIFICATION.md Truth 6 and 01-REVIEW.md CR-01 (and making the previously-dead `BeamType` `None` branch reachable, closing IN-03).
- `FixtureModel.attributes`, `format_value` and `ComparisonRow.any_differs` docstrings now state the "None = not declared" contract for Phase 2/3 to read; `SKELETON.md` records the 01-06 symbols and updated Attribute-identity/Input-hardening rows; 01-03-PLAN.md's previously-unresolved prohibition is marked `resolved` with a pointer to the enforcing test.

## Task Commits
1. **Task 1: End-to-end "an omitted Weight shows N/A"** - `9ccaa76` (feat)
2. **Task 2 RED: failing tests for presence-aware beam/model extraction** - `e13ec96` (test)
3. **Task 2 GREEN: presence-aware beam and model extraction** - `73203e0` (feat)
4. **Task 3: "None = not declared" contract + prohibition closure** - `d6159e2` (docs)

## Files Created/Modified
- `src/gdtf_comparer/core/hardening.py` - adds `ValidatedGDTF` NamedTuple and `prevalidate_gdtf_document`; `prevalidate_gdtf` now delegates
- `src/gdtf_comparer/core/repository.py` - `load()` calls `prevalidate_gdtf_document` and passes `validated.description_root` to extraction
- `src/gdtf_comparer/core/extract.py` - adds `DescriptionMismatchError`, `_weight_declared`, `_geometry_children`; `iter_geometry_paths` and `extract_attributes` are presence-aware
- `src/gdtf_comparer/core/models.py` - docstrings only: the "None = not declared" contract
- `tests/core/test_extract.py` - updated `_extract` helper; new omission/alignment/mismatch tests
- `tests/core/test_comparator.py` - new both-omitted and omitted-vs-declared-default tests
- `tests/gui/test_unspecified_values.py` - new file; end-to-end N/A proof for Weight and Beam attributes
- `.planning/phases/01-foundation-rebuild/SKELETON.md` - Attribute identity/Input hardening rows updated, 01-06 Symbols-by-plan row added
- `.planning/phases/01-foundation-rebuild/01-03-PLAN.md` - prohibition marked resolved, Flagged Assumptions bullet prefixed "CLOSED by 01-06 —"

## Decisions Made
- Implemented option (b) from the plan's Decision Record: presence check over the validated tree, undeclared attributes shown as None/N/A. Options (a) (accept defaults as declared) and (c) (provenance-tagged values) were rejected/deferred as documented in the plan.
- No new dataclass shapes or wire formats (D-13 honored); the mechanism sits entirely behind `extract_attributes`'s existing return type.

## Deviations from Plan

None - plan executed exactly as written.

**Total deviations:** 0.
**Impact:** None.

## Issues Encountered

None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
Ready for 01-07.

---
*Phase: 01-foundation-rebuild*
*Completed: 2026-09-26*
