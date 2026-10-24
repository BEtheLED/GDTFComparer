---
phase: 05-mvr-import-fixture-substitution
plan: 02
subsystem: mvr-import-substitution
tags: [pymvr, mvr, hardening, pyside6, defusedxml, qthread]

requires:
  - phase: 05-mvr-import-fixture-substitution
    provides: "Plan 05-01's tracer slice -- core.mvr_repository.import_mvr, core.hardening's MVR pre-validation pipeline, gui.substitution_window.SubstitutionWindow, gui.worker.MVRImportWorker"
provides:
  - "cp437-aware member resolution so an accented embedded GDTF name (e.g. Lumière@Spot.gdtf) is still found (readable_gdtf_spec, resolve_member_name)"
  - "Full-breadth fixture-tree walk coverage proven by tests: nested GroupObjects, SceneObject/Truss/Support/VideoScreen/Projector children, dedup by GDTF file reference, walk order"
  - "Rewritten import_summary_message wording (NO_FIXTURES/NONE_IMPORTED/FOUND/SKIPPED/UNREFERENCED templates) that always names every skipped type and every unreferenced fixture"
  - "Proof that every damaged/hostile/wrong-file MVR import path (not-a-zip, XXE, billion laughs, malformed XML, wrong root, oversized, FIFO, folder, bad scene field, Latin-1 scene) ends in one typed, friendly, traceback-free error, and that pymvr is never constructed on unvalidated bytes"
  - "One-MVR-import-at-a-time guarantee plus clean process shutdown when a Find Substitutes worker (import or inventory scan) is stuck (MainWindow.is_substitution_running, closeEvent ordering, app.py's os._exit guard)"
affects: [05-03-requirements-editor-widening, 05-04-requirements-file-safety, 05-05-substitution-scoring-widening]

actuals:
  tokens: 13100
  tasks: 3
  commits: 3
  plan_head_before: 830010196011ccd7b8627c8617b337df6a17d1c9
  plan_head_after: 605d7e514d30a05fd9b9cfd3d026cc27810d1644

tech-stack:
  added: []
  patterns:
    - "readable_gdtf_spec reverses pymvr's unconditional .encode('utf-8').decode('cp437') round trip on <GDTFSpec> text, so an exact-match-first, cp437-recovered-fallback lookup (resolve_member_name) finds a non-ASCII embedded GDTF member without ever re-deriving or guessing a filename independently of the archive's own namelist()"
    - "import_summary_message built from five named templates (NO_FIXTURES/NONE_IMPORTED/FOUND/SKIPPED/UNREFERENCED) plus a private _count() pluralizer, instead of one hand-rolled f-string, so every one of SUB-01's named-not-dropped guarantees has its own template to test independently"
    - "MainWindow.is_substitution_running() delegates to SubstitutionWindow.is_busy() rather than duplicating thread-tracking state, mirroring the existing is_comparison_running() shape"

key-files:
  created:
    - tests/core/test_mvr_repository.py
    - tests/core/test_mvr_hardening.py
  modified:
    - src/gdtf_comparer/core/mvr_repository.py
    - src/gdtf_comparer/gui/substitution_window.py
    - src/gdtf_comparer/gui/main_window.py
    - src/gdtf_comparer/app.py
    - tests/conftest.py
    - tests/gui/test_mvr_import.py
    - tests/test_fixture_builder.py

key-decisions:
  - "Task 2 required zero production code changes: 05-01's shared GDTF/MVR hardening pipeline (_read_file_bytes/_extract_member_bytes/_parse_xml_safely) and import_mvr's single try/except already closed every hostile-file gap the plan's RED tests probed (not-a-zip, XXE, billion laughs, oversized, FIFO, folder, a bad scene field, a Latin-1-declared scene). All 16 new tests in tests/core/test_mvr_hardening.py passed on first run with no source changes -- confirmed by a clean 'git diff --quiet HEAD -- tests/core/test_hardening.py'."
  - "FixtureTypeEntry/SkippedFixtureType.gdtf_spec now carry the resolved, readable archive member name (never pymvr's own possibly cp437-mangled gdtf_spec), while the internal order/counts dedup keys stay on pymvr's raw strings -- the two never need to agree for dedup to work correctly, only for display."
  - "total_fixture_count (unreferenced + every distinct spec's instance count, imported or skipped) was added as a 5th, defaulted field on MVRImport so import_summary_message can distinguish 'this show has no fixtures at all' from 'every fixture type in this show failed to import' without changing MVRImport's existing positional-construction call sites."

requirements-completed: [PARSE-02, SUB-01]

coverage:
  - id: D1
    description: "Fixture types nested inside GroupObjects (including GroupObject-in-GroupObject), SceneObject, Truss, Support, VideoScreen, Projector and another Fixture's own child list are all found, deduplicated by GDTF file reference (ignoring GDTFMode), in first-encountered walk order"
    requirement: SUB-01
    verification:
      - kind: unit
        ref: "tests/core/test_mvr_repository.py#test_fixtures_found_everywhere_in_walk_order"
        status: pass
      - kind: unit
        ref: "tests/core/test_mvr_repository.py#test_dedup_by_gdtf_spec"
        status: pass
      - kind: unit
        ref: "tests/core/test_mvr_repository.py#test_gdtf_mode_ignored"
        status: pass
    human_judgment: false
  - id: D2
    description: "An accented GDTF file name (Lumière@Spot.gdtf) survives pymvr's cp437 mojibake round trip and is found in the archive under its real, readable spelling, both at the core level and in the Find Substitutes window's fixture-list tooltip"
    requirement: PARSE-02
    verification:
      - kind: unit
        ref: "tests/core/test_mvr_repository.py#test_accented_gdtf_name_is_found"
        status: pass
      - kind: automated_ui
        ref: "tests/gui/test_mvr_import.py#test_accented_fixture_type_imports_in_window"
        status: pass
    human_judgment: false
  - id: D3
    description: "A fixture type whose embedded GDTF is missing, broken or oversized is named with a plain reason in the import summary, every other type still imports, and fixtures naming no GDTF file are counted and mentioned -- the empty-show and all-types-fail wordings are distinct from each other and from the found-types wording"
    requirement: SUB-01
    verification:
      - kind: unit
        ref: "tests/core/test_mvr_repository.py#test_missing_embedded_gdtf_is_skipped_and_named"
        status: pass
      - kind: unit
        ref: "tests/core/test_mvr_repository.py#test_broken_embedded_gdtf_is_skipped_with_reason"
        status: pass
      - kind: unit
        ref: "tests/core/test_mvr_repository.py#test_oversized_embedded_gdtf_is_skipped"
        status: pass
      - kind: unit
        ref: "tests/core/test_mvr_repository.py#test_empty_scene"
        status: pass
      - kind: unit
        ref: "tests/core/test_mvr_repository.py#test_all_types_fail"
        status: pass
      - kind: unit
        ref: "tests/core/test_mvr_repository.py#test_found_summary_wording"
        status: pass
      - kind: automated_ui
        ref: "tests/gui/test_mvr_import.py#test_skipped_types_named_in_window"
        status: pass
      - kind: automated_ui
        ref: "tests/gui/test_mvr_import.py#test_empty_mvr_shows_message_not_crash"
        status: pass
    human_judgment: false
  - id: D4
    description: "Every damaged, hostile or wrong file picked as an MVR (not a zip, a GDTF renamed .mvr, XXE, billion laughs, malformed XML, wrong root/no Scene, oversized file, oversized scene XML, a bad total-uncompressed or compression-ratio limit, a folder, a FIFO, an unreadable scene field, a Latin-1-declared scene) ends in one typed, friendly, traceback-free dialog naming the file -- never a raw AttributeError/KeyError/ValueError -- and pymvr is never even constructed when pre-validation fails"
    requirement: PARSE-02
    verification:
      - kind: unit
        ref: "tests/core/test_mvr_hardening.py (16 tests)"
        status: pass
      - kind: automated_ui
        ref: "tests/gui/test_mvr_import.py#test_hostile_mvr_shows_one_friendly_dialog"
        status: pass
      - kind: automated_ui
        ref: "tests/gui/test_mvr_import.py#test_failed_import_clears_previous_list"
        status: pass
    human_judgment: false
  - id: D5
    description: "Only one MVR import runs at a time (Import MVR... disabled for the whole import, a second click never asks for a second path), the fixture list only ever appears complete (never half-built) or wholesale-replaced by a reimport, and closing the Find Substitutes or main window during a stuck import returns promptly and the whole process still exits cleanly"
    requirement: SUB-01
    verification:
      - kind: automated_ui
        ref: "tests/gui/test_mvr_import.py#test_import_button_disabled_while_importing"
        status: pass
      - kind: automated_ui
        ref: "tests/gui/test_mvr_import.py#test_no_partial_list_while_import_runs"
        status: pass
      - kind: automated_ui
        ref: "tests/gui/test_mvr_import.py#test_reimport_replaces_list_wholesale"
        status: pass
      - kind: automated_ui
        ref: "tests/gui/test_mvr_import.py#test_close_during_import_returns_promptly"
        status: pass
      - kind: automated_ui
        ref: "tests/gui/test_mvr_import.py#test_closing_main_window_closes_substitution_window"
        status: pass
      - kind: automated_ui
        ref: "tests/gui/test_mvr_import.py#test_is_substitution_running_reflects_worker"
        status: pass
      - kind: e2e
        ref: "tests/gui/test_mvr_import.py#test_app_process_exits_when_substitution_worker_stuck"
        status: pass
    human_judgment: false

duration: ~55min
completed: 2026-10-24
status: complete
---

# Phase 5 Plan 2: MVR Import Hardening at Full Breadth Summary

**cp437-aware accented-filename resolution, a rewritten always-names-every-failure summary wording, 16 new hardening tests proving every damaged/hostile MVR ends in one friendly error with zero production gaps, and single-flight import plus clean shutdown for a stuck Find Substitutes worker.**

## Performance

- **Duration:** ~55 min
- **Completed:** 2026-10-24T18:21:14-04:00
- **Tasks:** 3
- **Files modified:** 9 (2 created, 7 modified)

## Accomplishments

- `core.mvr_repository.readable_gdtf_spec()` reverses pymvr's unconditional `.encode("utf-8").decode("cp437")` mojibake transform on `<GDTFSpec>` text, so `resolve_member_name()` can fall back to the recovered spelling when the exact string isn't a zip member -- an accented GDTF file name (`Lumière@Spot.gdtf`) is found correctly, in the Find Substitutes window too (its tooltip now shows the readable name).
- `MVRImport` gained a `total_fixture_count` field (defaulted to 0, so existing positional construction is untouched) so `import_summary_message()` can tell "this show has no fixtures at all" apart from "every fixture type in this show failed to import" -- the wording is now built from five named templates (`NO_FIXTURES_TEMPLATE`, `NONE_IMPORTED_TEMPLATE`, `FOUND_TEMPLATE`, `SKIPPED_TEMPLATE`, `UNREFERENCED_TEMPLATE`) instead of one hand-rolled f-string, so each guarantee has its own template to test.
- 29 new tests across `tests/core/test_mvr_repository.py` prove the full-breadth fixture walk: dedup by GDTF file reference (ignoring `GDTFMode`), nesting through `GroupObject`-in-`GroupObject`, `SceneObject`/`Truss`/`Support`/`VideoScreen`/`Projector`, walk order, accented names, and every skip/empty/all-fail wording case.
- 16 new tests in `tests/core/test_mvr_hardening.py` throw every damaged/hostile/wrong file shape at `import_mvr()` -- not a zip, a GDTF picked by mistake, XXE, billion laughs, malformed XML, wrong root or missing `Scene`, oversized file/scene-XML/total-uncompressed/compression-ratio, a folder, a FIFO, an unreadable scene field (`ValueError`), a Latin-1-declared scene -- and every one already ended in a typed, friendly, traceback-free error with **zero production code changes needed**: 05-01's shared GDTF/MVR hardening pipeline already closed every gap.
- `MainWindow.is_substitution_running()` (mirroring `is_comparison_running()`) and an updated `closeEvent` (closes the Find Substitutes window first) plus `app.py`'s post-event-loop `os._exit` guard now also cover a stuck Find Substitutes worker, proven by a subprocess test mirroring the existing comparison-worker shutdown test.
- `tests/test_fixture_builder.py`'s toolchain guard now also pins `pymvr==1.0.7`.

## Task Commits

1. **Task 1: Find every fixture type, including nested and accented ones** - `8962238` (feat)
2. **Task 2: Prove every damaged or hostile MVR ends in one friendly error** - `c01594b` (test)
3. **Task 3: One import at a time, clean shutdown with a stuck worker** - `605d7e5` (feat)

**Plan metadata:** (this SUMMARY + STATE/ROADMAP/REQUIREMENTS updates, committed separately by the orchestrator after the wave completes)

## Files Created/Modified

- `src/gdtf_comparer/core/mvr_repository.py` - `readable_gdtf_spec`, cp437-aware `resolve_member_name`, `total_fixture_count`, rewritten `import_summary_message` templates and `_count` helper
- `src/gdtf_comparer/gui/substitution_window.py` - `mvr_summary_label` renders plain text; an empty import result explicitly clears the requirements editor and disables both action buttons
- `src/gdtf_comparer/gui/main_window.py` - `is_substitution_running()`; `closeEvent` closes the Find Substitutes window first
- `src/gdtf_comparer/app.py` - the shutdown `os._exit` guard also checks `is_substitution_running()`
- `tests/conftest.py` - `group_xml`, `child_node_xml` helpers for nested-MVR test fixtures
- `tests/core/test_mvr_repository.py` - new: dedup, nesting/walk order, accented names, missing/broken/oversized embedded GDTFs, empty/single/all-fail scenes, summary wording, no-disk-writes
- `tests/core/test_mvr_hardening.py` - new: every hostile/damaged/wrong-file MVR path ends in a typed, friendly, traceback-free error; pymvr never constructed on unvalidated bytes
- `tests/gui/test_mvr_import.py` - new: window-level summary/empty-state/friendly-dialog coverage, one-import-at-a-time, no-partial-list, reimport-replaces-wholesale, bounded close, main-window-closes-substitution-window, `is_substitution_running` reflection, and the stuck-worker subprocess exit test
- `tests/test_fixture_builder.py` - toolchain guard now also pins `pymvr==1.0.7`

## Decisions Made

See `key-decisions` in frontmatter. The most notable: Task 2's entire hardening-test suite (16 tests) passed on the very first run with no source changes required, because Plan 05-01 had already generalized `core/hardening.py`'s GDTF pipeline to cover MVR identically (`_FileKind`-parameterized helpers) and `import_mvr`'s single try/except already wrapped both pymvr's construction and the fixture-tree walk. This was confirmed, not assumed: `git diff --quiet HEAD -- tests/core/test_hardening.py` exits 0, proving the pre-existing GDTF hardening tests were never touched.

## Deviations from Plan

None — plan executed exactly as written. Task 2 produced no production code changes (as the plan itself anticipated: "Most should already pass from 05-01's pipeline"), which is not a deviation but the expected outcome of the RED step confirming no gap existed.

## Issues Encountered

- **Test-authoring bug, caught and fixed before commit:** my first draft of `test_failed_import_clears_previous_list` omitted the `capture_dialogs` fixture, so its second (deliberately bad) import attempt triggered a real, un-captured `QMessageBox.exec()` that blocked forever waiting for a UI click that never comes under the offscreen Qt platform. This surfaced as an intermittent hang/segfault across several verify-command runs. Diagnosed definitively with `faulthandler.dump_traceback_later(25, exit=True)` around a direct `pytest.main()` call, which printed the exact stuck frame (`substitution_window.py:218` inside `_show_error`/`box.exec()`). Fixed by adding `capture_dialogs` to the test's fixture list; reran the full Task 2 and Task 3 verify commands twice each afterward with no further flakiness. This was a defect in a test I was writing, not in the plan or in shipped production code.

## User Setup Required

None — no external service configuration required. No new dependencies were added (pymvr was already pinned and approved in Plan 05-01).

## Next Phase Readiness

This plan's slice (MVR import hardened at full breadth: nesting, accented names, every hostile-file shape, single-flight imports, clean shutdown) is complete and independently verified. It unblocks nothing new for Wave 3 beyond what 05-01 already provided — 05-05 (SUB-04 scoring/ranking widening) still depends on 05-02 and 05-03 per the roadmap, and this plan changed no contract 05-03/05-04/05-05 rely on (`FixtureTypeEntry`/`SkippedFixtureType`/`MVRImport`'s existing fields are all still positionally compatible; `total_fixture_count` is additive-only).

No blockers.

---
*Phase: 05-mvr-import-fixture-substitution*
*Completed: 2026-10-24*
