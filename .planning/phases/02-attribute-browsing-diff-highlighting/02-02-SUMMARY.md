---
phase: 02-attribute-browsing-diff-highlighting
plan: 02
subsystem: core
tags: [pygdtf, gdtf, attribute-definitions, dmx, xml, tdd]

# Dependency graph
requires:
  - phase: 02-attribute-browsing-diff-highlighting
    provides: "Plan 02-01's category-agnostic core.comparator.compare()/attribute_catalog() and gui.attribute_picker.AttributePicker -- this plan feeds them a richer key set with no GUI/comparator source change"
provides:
  - "core.extract.extract_attributes() reads every <AttributeDefinitions><Attributes><Attribute> entry, not just Beam and Physical Properties"
  - "core.models.DMX_ATTRIBUTE_CATEGORY_PREFIX (\"DMX: \") and UNGROUPED_FEATURE_GROUP (\"(no feature group)\") -- the collision-proof category scheme for DMX attribute definitions"
  - "core.extract._declared_values(node, element, specs): the single presence-check generator now shared by Beam, Model and DMX attribute-definition extraction"
  - "core.extract.dmx_attribute_category(feature_link) and _attribute_definition_elements(fixture_type_element): public/private helpers for grouping and lockstep pairing"
  - "tests/conftest.py attributes_xml= builder hook (build_description_xml, make_gdtf)"
  - "tests/gui/test_dmx_attributes.py: real-run coverage of the full DMX vocabulary reaching the Attributes panel"
affects: ["02-03 (differences-only proxy sees the same richer row set with no change needed)", "Phase 3 (ATTR-03 compare profiles will save (category, attribute) pairs using this exact category/name scheme -- renaming it later means migrating saved profiles)"]

# Actuals (#2632) — pairs with the plan's estimate to calibrate future estimates.
actuals:
  tokens: 10007
  tasks: 2
  commits: 4
  plan_head_before: 69f369a3d6badd6c766cc9578509b9d3acc1a9b6

tech-stack:
  added: []
  patterns:
    - "AttributeSpec triples (xml name, pygdtf field, value transform) plus one shared _declared_values(node, element, specs) generator -- Beam, Model and DMX attribute-definition extraction all read presence from the validated element and value from pygdtf through this single path, no per-category hand-written loop"
    - "Category-prefix collision-proofing: every DMX section is DMX_ATTRIBUTE_CATEGORY_PREFIX + <feature group>, so a file-supplied group or attribute name (e.g. \"Beam\", \"Weight\") can never land in, merge with, or default-check a legacy category"
    - "Lockstep count-then-name pairing with fail-closed DescriptionMismatchError: attribute definitions are paired index-for-index between the validated XML tree and pygdtf's parsed model; either a count or a Name divergence raises rather than guessing"

key-files:
  created:
    - tests/gui/test_dmx_attributes.py
  modified:
    - tests/conftest.py
    - src/gdtf_comparer/core/models.py
    - src/gdtf_comparer/core/extract.py
    - tests/core/test_extract.py

key-decisions:
  - "Every <Attribute> definition becomes one (category, attribute) picker entry: category is \"DMX: \" + the Feature link's group, attribute is the definition's Name, and each of the definition's six properties (Pretty, Feature, ActivationGroup, MainAttribute, PhysicalUnit, Color) becomes its own row keyed by property name (assumption_delta_decision, 02-02-PLAN.md) -- the nested DMX-mode/channel structure stays out of scope for this plan"
  - "BEAM_ATTRIBUTES and MODEL_ATTRIBUTES were converted from (xml name, pygdtf field) pairs into AttributeSpec triples so they route through the same _declared_values helper as DMX definitions, removing the hand-written per-name BeamType special case without changing the row order or values any existing test asserts"

patterns-established:
  - "A definition's lockstep pairing check runs count-then-name: a count mismatch and a Name mismatch each raise DescriptionMismatchError with fixed, file-content-free text (T-01-25), mirroring the existing geometry-tag fail-closed rule (T-01-23)"

requirements-completed: [ATTR-01]

coverage:
  - id: D1
    description: "extract_attributes() reads the full flat AttributeDefinitions vocabulary (Pan, Tilt, Dimmer, ColorAdd_R, and so on) into six rows per definition under \"DMX: <feature group>\", with presence read from the validated XML element (undeclared -> None/N/A even when pygdtf backfills a value) and values transformed per-property (NodeLink text, Enum .value, plain text/Color six-decimal formatting)"
    requirement: "ATTR-01"
    verification:
      - kind: unit
        ref: "tests/core/test_extract.py#test_attribute_definition_properties_are_extracted"
        status: pass
      - kind: unit
        ref: "tests/core/test_extract.py#test_omitted_definition_properties_are_none"
        status: pass
      - kind: unit
        ref: "tests/core/test_extract.py#test_declared_physical_unit_none_is_not_na"
        status: pass
      - kind: unit
        ref: "tests/core/test_extract.py#test_sixty_four_definitions_are_extracted"
        status: pass
      - kind: unit
        ref: "tests/core/test_extract.py#test_definition_count_mismatch_raises"
        status: pass
    human_judgment: false
  - id: D2
    description: "End-to-end in the real GUI: DMX sections appear unchecked and collapsed below Beam/Physical Properties, the 60+ definitions are all present and browsable via attribute_catalog(), the default results table is unchanged, and ticking a DMX attribute (Pan) adds exactly its six rows with N/A wherever a comparison fixture omits that property"
    requirement: "ATTR-01"
    verification:
      - kind: integration
        ref: "tests/gui/test_dmx_attributes.py#test_dmx_sections_listed_unchecked_and_collapsed"
        status: pass
      - kind: integration
        ref: "tests/gui/test_dmx_attributes.py#test_sixty_plus_definitions_are_browsable"
        status: pass
      - kind: integration
        ref: "tests/gui/test_dmx_attributes.py#test_default_table_unchanged_by_dmx_definitions"
        status: pass
      - kind: integration
        ref: "tests/gui/test_dmx_attributes.py#test_checking_pan_shows_its_definition_rows"
        status: pass
    human_judgment: false
  - id: D3
    description: "Odd or colliding definitions never break extraction or misattribute values: category-edge mapping (missing/blank/dot-leading Feature), duplicate names get a #2 suffix, an unnamed definition gets a positional label, a legacy-named definition (BeamAngle, Weight) never collides with or affects CATEGORY_BEAM/CATEGORY_PHYSICAL, all three missing-block shapes (empty Attributes, no Attributes element, no AttributeDefinitions element) yield zero DMX keys without error, a Name mismatch between the validated tree and pygdtf's model raises DescriptionMismatchError (fail closed), Color's six-decimal padding compares equal, and a declared-but-invalid PhysicalUnit/Color follows pygdtf's own normalisation"
    requirement: "ATTR-01"
    verification:
      - kind: unit
        ref: "tests/core/test_extract.py#test_dmx_attribute_category_edges"
        status: pass
      - kind: unit
        ref: "tests/core/test_extract.py#test_duplicate_definition_names_get_suffix"
        status: pass
      - kind: unit
        ref: "tests/core/test_extract.py#test_unnamed_definition_label"
        status: pass
      - kind: unit
        ref: "tests/core/test_extract.py#test_legacy_named_definitions_do_not_collide"
        status: pass
      - kind: unit
        ref: "tests/core/test_extract.py#test_missing_definition_blocks_give_no_definitions"
        status: pass
      - kind: unit
        ref: "tests/core/test_extract.py#test_definition_name_mismatch_raises"
        status: pass
      - kind: unit
        ref: "tests/core/test_extract.py#test_color_decimal_padding_compares_equal"
        status: pass
      - kind: unit
        ref: "tests/core/test_extract.py#test_declared_malformed_values_follow_pygdtf"
        status: pass
    human_judgment: false
  - id: D4
    description: "Beam, Model and DMX definition extraction now share one presence-check helper (_declared_values) with no hand-written per-category loop; a fixture with zero definitions shows only the legacy Beam/Physical Properties sections, a DMX definition sharing the \"Beam\" feature group stays in its own unchecked DMX section beside the still-default-checked legacy Beam section, and DMX section/leaf order follows document order and is stable across repeated runs on the same files"
    requirement: "ATTR-01"
    verification:
      - kind: unit
        ref: "tests/core/test_extract.py (every pre-existing Beam/Model/Weight/presence-alignment/mismatch test, unchanged)"
        status: pass
      - kind: integration
        ref: "tests/gui/test_dmx_attributes.py#test_zero_definitions_shows_only_legacy_sections"
        status: pass
      - kind: integration
        ref: "tests/gui/test_dmx_attributes.py#test_dmx_beam_group_stays_separate_and_unchecked"
        status: pass
      - kind: integration
        ref: "tests/gui/test_dmx_attributes.py#test_dmx_sections_follow_document_order_across_runs"
        status: pass
    human_judgment: false
  - id: D5
    description: "On a real third-party moving-light .gdtf file, the Attributes panel shows several naturally-named DMX sections totalling 60+ attributes, and ticking Pan/typing a search term behaves as expected in the actual qt-material-rendered UI"
    verification: []
    human_judgment: true
    rationale: "Task 2's <human-check> requires a real third-party GDTF file (the offscreen test platform's synthetic 66-definition fixture proves the mechanism but not real-world attribute counts or section-name readability) and human judgment of the rendered UI. Deferred to end-of-phase per workflow.human_verify_mode=end-of-phase and carried into /gsd-verify-work, same as Plan 02-01's D3."

duration: ~15min active (across two sessions, separated by a session rate-limit interruption between Task 1 and Task 2)
completed: 2026-09-30
status: complete
---

# Phase 2 Plan 2: DMX Attribute-Definition Extraction Summary

**Extended core.extract to read the fixture's full `<AttributeDefinitions>` vocabulary (60+ DMX attributes like Pan, Tilt, Dimmer, Gobo1, ColorAdd_R) into "DMX: `<feature group>`" picker sections, sharing one presence-check helper with the existing Beam/Model extraction.**

## Performance

- **Duration:** ~15 min active work, split across two sessions (a session rate-limit interruption paused work between Task 1's completion and Task 2's start; elapsed wall-clock time between commits is not representative of active effort)
- **Started:** 2026-09-30T07:39:13-05:00 (Task 1 RED)
- **Completed:** 2026-09-30T11:05:06-05:00 (Task 2 GREEN)
- **Tasks:** 2 (Task 1: tracer slice, extraction + GUI wiring; Task 2: `tdd="true"`, odd/colliding definitions + shared presence check)
- **Files modified:** 5 (1 created, 4 modified)

## Accomplishments

- `core.extract.extract_attributes()` now reads every `<AttributeDefinitions><Attributes><Attribute>` entry from the validated XML tree, paired in lockstep (count then Name) with pygdtf's parsed `fixture_type.attributes`, and produces six rows per definition (Pretty, Feature, ActivationGroup, MainAttribute, PhysicalUnit, Color) under a `"DMX: <feature group>"` category
- New `core.models.DMX_ATTRIBUTE_CATEGORY_PREFIX` ("DMX: ") and `UNGROUPED_FEATURE_GROUP` ("(no feature group)") constants guarantee a file-supplied feature-group or attribute name can never collide with, merge into, or silently default-check `CATEGORY_BEAM`/`CATEGORY_PHYSICAL`
- New `core.extract._declared_values(node, element, specs)` generalises the Plan 01-06 presence-check contract (declared vs. pygdtf-backfilled default) into one shared path; `BEAM_ATTRIBUTES` and `MODEL_ATTRIBUTES` were converted from bare pairs into `AttributeSpec` triples and now route through it too, removing the old hand-written per-name `BeamType` special case
- New `tests/gui/test_dmx_attributes.py` proves the whole thing end to end in a real `MainWindow`/`AttributePicker` run: DMX sections list unchecked and collapsed, 60+ definitions are browsable via both the tree and `attribute_catalog()`, the default 7-row table is unchanged, ticking Pan adds exactly its six rows with N/A for what the comparison fixture omits, a zero-definition fixture shows only the legacy sections, a DMX "Beam" group stays separate from and unchecked next to the still-default-checked legacy Beam section, and DMX section/leaf order is stable across repeated runs
- `tests/core/test_extract.py` covers the vocabulary's edges: category-mapping edge cases, duplicate/unnamed definition labels, legacy-name non-collision, all three "no definitions" document shapes, a fail-closed `DescriptionMismatchError` on both count and Name mismatch, Color's six-decimal padding comparing equal, and declared-but-invalid `PhysicalUnit`/`Color` following pygdtf's own normalisation

## Task Commits

Each task was committed atomically (both tasks followed TDD RED -> GREEN):

1. **Task 1 RED: DMX attribute-definition extraction tests** - `2df7a72` (test)
2. **Task 1 GREEN: DMX attribute-definition extraction** - `39d2807` (feat)
3. **Task 2 RED: odd/colliding definitions and shared presence check** - `5171b2c` (test)
4. **Task 2 GREEN: lockstep name check and shared presence-check helper** - `857a54b` (feat)

_Neither task needed a separate refactor commit -- both GREEN implementations matched the plan's spec with nothing left to clean up._

**Plan metadata:** committed alongside this SUMMARY (see final commit).

## Files Created/Modified

- `tests/conftest.py` - Added `attributes_xml: str = ""` to `build_description_xml` and the `make_gdtf` factory, replacing the hardcoded empty `<Attributes>` line (Task 1)
- `src/gdtf_comparer/core/models.py` - Added `DMX_ATTRIBUTE_CATEGORY_PREFIX` and `UNGROUPED_FEATURE_GROUP` constants; extended `AttributeKey`/`FixtureModel` docstrings to cover DMX definition rows (Task 1)
- `src/gdtf_comparer/core/extract.py` - Added `AttributeSpec`, the four value transforms (`_as_float`, `_enum_value`, `_link_text`, `_as_text`), `ATTRIBUTE_DEFINITION_PROPERTIES`, `dmx_attribute_category()`, `_attribute_definition_elements()`, and the attribute-definition extraction loop (Task 1); added the lockstep Name check, converted `BEAM_ATTRIBUTES`/`MODEL_ATTRIBUTES` to `AttributeSpec` triples routed through the new shared `_declared_values()` helper, and updated the module docstring (Task 2)
- `tests/core/test_extract.py` - Added the DMX vocabulary test suite: 5 Task 1 tests (definition properties, omitted properties, declared-"None" vs. omitted, 64-definition extraction, count-mismatch fail-closed) and 8 Task 2 tests (category edges, duplicate/unnamed labels, legacy non-collision, missing-block shapes, name-mismatch fail-closed, Color padding equality, malformed-value pass-through)
- `tests/gui/test_dmx_attributes.py` - New file: 4 Task 1 real-run tests (sections unchecked/collapsed, 60+ browsable, default table unchanged, ticking Pan shows its rows) and 3 Task 2 real-run tests (zero-definition fixture, DMX Beam group stays separate/unchecked, section/leaf order stable across runs)

## Decisions Made

- Kept the nested DMX-mode/channel structure out of scope, reading only the flat `<AttributeDefinitions><Attributes>` vocabulary, per the plan's `assumption_delta_decision` and RESEARCH Pitfall 4 -- a follow-up phase would add DMX modes/channels
- Converted `BEAM_ATTRIBUTES`/`MODEL_ATTRIBUTES` to `AttributeSpec` triples rather than leaving them as pairs with a separate DMX-only presence helper, so "one presence check for every category" (the plan's Task 2 goal and this plan's `<threat_model>` T-02-07 boundary) is actually true in the code, not just in the docstring

## Deviations from Plan

None - plan executed exactly as written across both tasks. The prior session's interrupted, uncommitted draft of Task 2's 8 core RED tests (left in the working tree when the session hit a rate limit) matched the plan's `<behavior>` block exactly on review and needed no correction; only the 3 GUI RED tests and the GREEN implementation remained to be written in this session.

## Issues Encountered

- The prior executor session was interrupted by a session rate limit partway through writing Task 2's RED tests, leaving an uncommitted working-tree diff. This session resumed by reviewing that draft against the plan (found consistent, no changes needed), adding the missing GUI tests, confirming RED failed for the intentional reason only (`test_definition_name_mismatch_raises`; all 7 other new core tests already passed against Task 1's implementation, exactly as the plan's action block anticipated -- "the rest guard edges that Task 1's loop already handles and must stay green"), then implementing GREEN.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 02-03 (differences-only filtering) sees the same richer row set through the unchanged `compare()`/`attribute_catalog()`/`AttributePicker` chain -- no new integration work needed there.
- Phase 3's ATTR-03 (saved compare profiles) will persist `(category, attribute)` pairs using this exact `"DMX: <feature group>"` / definition-Name scheme; renaming either half later means migrating saved profiles (plan's `<reversibility>` note on Task 1).
- Task 2's `<human-check>` (real third-party GDTF file, 60+ attributes, section-name readability, qt-material rendering) is deferred to end-of-phase per `workflow.human_verify_mode=end-of-phase` and is carried into `/gsd-verify-work` (see coverage entry D5).
- With this plan complete, ATTR-01 ("browse/search the full set of GDTF attributes, 60+ properties, not just Beam/Physical Properties") is now fully delivered across Plans 02-01 (browsing/search mechanism) and 02-02 (the full attribute set itself) -- `requirements.ready-ids` reports it ready to mark complete.

---
*Phase: 02-attribute-browsing-diff-highlighting*
*Completed: 2026-09-30*

## Self-Check: PASSED

All modified/created files verified present on disk; all task commit hashes (`2df7a72`, `39d2807`, `5171b2c`, `857a54b`) verified present in git history.
