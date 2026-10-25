---
phase: 05-mvr-import-fixture-substitution
verified: 2026-10-24T20:00:00Z
status: passed
score: 4/4 must-haves verified
covered_files: [".planning/phases/05-mvr-import-fixture-substitution/05-01-PLAN.md", ".planning/phases/05-mvr-import-fixture-substitution/05-01-SUMMARY.md", ".planning/phases/05-mvr-import-fixture-substitution/05-02-PLAN.md", ".planning/phases/05-mvr-import-fixture-substitution/05-02-SUMMARY.md", ".planning/phases/05-mvr-import-fixture-substitution/05-03-PLAN.md", ".planning/phases/05-mvr-import-fixture-substitution/05-03-SUMMARY.md", ".planning/phases/05-mvr-import-fixture-substitution/05-04-PLAN.md", ".planning/phases/05-mvr-import-fixture-substitution/05-04-SUMMARY.md", ".planning/phases/05-mvr-import-fixture-substitution/05-05-PLAN.md", ".planning/phases/05-mvr-import-fixture-substitution/05-05-SUMMARY.md", "pyproject.toml", "src/gdtf_comparer/app.py", "src/gdtf_comparer/core/errors.py", "src/gdtf_comparer/core/hardening.py", "src/gdtf_comparer/core/mvr_repository.py", "src/gdtf_comparer/core/repository.py", "src/gdtf_comparer/core/requirements_repository.py", "src/gdtf_comparer/core/substitution.py", "src/gdtf_comparer/gui/candidate_results.py", "src/gdtf_comparer/gui/main_window.py", "src/gdtf_comparer/gui/requirements_editor.py", "src/gdtf_comparer/gui/substitution_window.py", "src/gdtf_comparer/gui/worker.py", "tests/conftest.py", "tests/core/test_mvr_hardening.py", "tests/core/test_mvr_repository.py", "tests/core/test_requirement_defaults.py", "tests/core/test_requirements_repository.py", "tests/core/test_substitution.py", "tests/gui/test_candidate_results.py", "tests/gui/test_mvr_import.py", "tests/gui/test_requirements_editor.py", "tests/gui/test_requirements_file.py", "tests/gui/test_substitution_round_trip.py", "tests/test_architecture.py", "tests/test_fixture_builder.py"]
covered_digest: "v3:sha256:09a3edc45d246fa5da29d7d2d3d86e80d267125be0968165c089cacd3eeacbca"
behavior_unverified: 0
overrides_applied: 0
---

# Phase 05: MVR Import & Fixture Substitution Verification Report

**Phase Goal:** A lighting designer can import an MVR show file, mark which attributes matter most for each fixture type, and share those requirements so anyone — including a rental shop checking their own inventory — can find substitute fixtures that meet them.
**Verified:** 2026-10-24
**Status:** passed
**Re-verification:** No — initial verification (two prior attempts did not complete; this is a clean retry)

## Goal Achievement

### Observable Truths

ROADMAP Phase 5's four numbered Success Criteria (the contract — `Mode: mvp` flag confirmed removed, standard phase):

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User can import an MVR file (parsed via `pymvr`) and see one entry per unique GDTF fixture type it references, not one per instance | ✓ VERIFIED | `import_mvr()` in `src/gdtf_comparer/core/mvr_repository.py` dedups by GDTF file reference; `tests/gui/test_substitution_round_trip.py::test_ld_to_shop_round_trip` imports an MVR with 2 fixture instances referencing the same GDTF and asserts exactly one row "Acme Spot — Acme (2 in this show)"; `tests/core/test_mvr_repository.py` covers nested GroupObjects/SceneObjects/Trusses/Supports/VideoScreens/Projectors, accented names (cp437 recovery), and dedup edges. All pass (see Behavioral Spot-Checks). |
| 2 | For each fixture type, user can mark attributes "important" with a direction (higher/lower/closer-to-target, smart default, overridable) and its own tolerance | ✓ VERIFIED | `core/substitution.py` (`Direction`, `DEFAULT_DIRECTIONS`, `default_direction`, `default_tolerance`); `gui/requirements_editor.py` (`RequirementsEditor`, per-type memory, per-attribute tolerance spin boxes). `tests/core/test_requirement_defaults.py` and `tests/gui/test_requirements_editor.py` (independent per-type checklists, order, overrides, text "Must match", search, empty state) all pass. |
| 3 | User can export one fixture's marked requirements to a separate shareable file (never embedded in the MVR) and a different user, in a different session, can load it back | ✓ VERIFIED | `core/requirements_repository.py` (`save_requirements`/`load_requirements`, atomic temp-file+`os.replace`, strict schema). `tests/core/test_requirements_repository.py::test_round_trip_in_a_separate_process` round-trips via a separate Python process; `test_saving_never_touches_an_mvr` / round-trip test in `test_substitution_round_trip.py` asserts the MVR's bytes are identical before and after save. A fresh, independent `SubstitutionWindow()` (no shared state) opens the file. |
| 4 | User can point the app at a local folder of candidate GDTF files and see each scored against a loaded requirement set with a three-state (green/yellow/red) per-attribute result, ranked best match first | ✓ VERIFIED | `core/substitution.py` (`score_value`, `score_candidate`, `rank`, `scan_candidate_folder`); `gui/candidate_results.py` (`CandidateResultsModel`, `MATCH_STATE_ROLE`, `BackgroundBrushDelegate` wiring). `test_ld_to_shop_round_trip` scans 3 candidates (14/16.5/20 kg vs. 15 kg target, lower-is-better) and asserts exactly green/yellow/red in rank order (Beta, Gamma, Delta); `BackgroundRole` is a real `QBrush` at each cell. |

**Score:** 4/4 truths verified (0 present-but-behavior-unverified)

### Required Artifacts

All artifacts declared across the 5 plans' `must_haves.artifacts` verified via `gsd-tools query verify.artifacts` (existence + substantive content pattern):

| Plan | Artifacts | Result |
|------|-----------|--------|
| 05-01 | 9 (mvr_repository.py, substitution.py, requirements_repository.py, requirements_editor.py, candidate_results.py, substitution_window.py, hardening.py additions, pyproject.toml pin, test_substitution_round_trip.py) | 9/9 passed |
| 05-02 | 5 (mvr_repository.py cp437 widening, test_mvr_repository.py, test_mvr_hardening.py, test_mvr_import.py, test_fixture_builder.py) | 5/5 passed |
| 05-03 | 4 (substitution.py defaults/units, requirements_editor.py widening, test_requirement_defaults.py, test_requirements_editor.py) | 4/4 passed |
| 05-04 | 3 (requirements_repository.py hardening, test_requirements_repository.py, test_requirements_file.py) | 3/3 passed |
| 05-05 | 5 (substitution.py scoring widening, candidate_results.py, substitution_window.py, test_substitution.py, test_candidate_results.py) | 5/5 passed |

All files confirmed present on disk with real implementations (`src/gdtf_comparer/core/mvr_repository.py`, `core/substitution.py`, `core/requirements_repository.py`, `gui/requirements_editor.py`, `gui/candidate_results.py`, `gui/substitution_window.py` — all non-trivially sized, 9-20KB each, last modified 2026-10-24).

### Key Link Verification

Verified via `gsd-tools query verify.key-links` against the three plans that declare `must_haves.key_links` (05-01, 05-03, 05-04):

| From | To | Via | Status |
|------|-----|-----|--------|
| `gui/main_window.py` | `gui/substitution_window.py` | `substitutes_button.clicked.connect(open_substitution_window)` | ✓ WIRED (8/8 for 05-01) |
| `gui/worker.py` | `core/mvr_repository.py` | `MVRImportWorker.run` calls `import_mvr` off GUI thread | ✓ WIRED |
| `core/mvr_repository.py` | `core/hardening.py` | `prevalidate_mvr_document` before pymvr | ✓ WIRED |
| `core/mvr_repository.py` | `pymvr.GeneralSceneDescription` | `io.BytesIO` of validated bytes | ✓ WIRED |
| `core/mvr_repository.py` | `core/repository.py` | `FixtureRepository.load_bytes` on in-memory bytes | ✓ WIRED |
| `gui/substitution_window.py` | `core/requirements_repository.py` | save/load_requirements | ✓ WIRED |
| `gui/worker.py` | `core/substitution.py` | `CandidateScanWorker.run` calls `scan_candidate_folder` | ✓ WIRED |
| `gui/substitution_window.py` | `gui/table_model.py` | `BackgroundBrushDelegate(...)` installed on results view | ✓ WIRED |
| `gui/requirements_editor.py` | `core/substitution.py` | (05-03, 2/2) | ✓ WIRED |
| `core/requirements_repository.py` | `json.loads` | `object_pairs_hook=`/`parse_constant=` (05-04, 2/2) | ✓ WIRED |

All 12 declared key links across the three plans that declare them verified WIRED.

### Behavioral Spot-Checks

Full workspace test suite run once (`pytest -q -W error::DeprecationWarning tests/`): **462 passed, 0 failed.** Representative subset re-confirmed individually:

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full LD→shop round trip (import, mark, save, fresh-window open, scan, rank green/yellow/red) | `pytest tests/gui/test_substitution_round_trip.py -v -W error::DeprecationWarning` | 3 passed | ✓ PASS |
| Architecture guards (gui/ never imports pymvr directly, core stays Qt-free, no network modules) | `pytest tests/test_architecture.py -v` | 6 passed | ✓ PASS |
| Traffic-light colors render distinctly in both light and dark themes | `pytest tests/gui/test_candidate_results.py -k traffic_lights -v` | 2 passed | ✓ PASS |
| pymvr==1.0.7 actually installed (not just declared) | `pip show pymvr` | Version: 1.0.7 | ✓ PASS |
| Tolerance semantics match the user's Task 2 decision (option a) | `grep TOLERANCE_KIND/CLOSEST_*_FACTOR core/substitution.py` | `TOLERANCE_KIND = "absolute"`, `CLOSEST_GREEN_FACTOR = 0.5`, `CLOSEST_YELLOW_FACTOR = 1.0` | ✓ PASS |
| **Independent probe (not in test suite): deeply-nested-MVR DoS risk (code review CR-01, still "open")** | Hand-built `.mvr` with 1,000 / 3,000 / 10,000 / 50,000 / 150,000 nested `<GroupObject>` levels, run through `import_mvr()` in a subprocess | Every depth produced a clean `MVRParseError: ... its scene data could not be parsed (RecursionError).`, exit code 0, no hang, no crash | ✓ PASS (see Anti-Patterns note below — residual risk tracked, not reproduced) |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| PARSE-02 | 05-01 | App parses MVR files using `pymvr` | ✓ SATISFIED | `pymvr==1.0.7` pinned and installed; `core/mvr_repository.py` wraps it behind hardened pre-validation |
| SUB-01 | 05-01, 05-02 | Import MVR, one entry per unique GDTF fixture type | ✓ SATISFIED | dedup-by-GDTF-spec logic + full breadth of scene-graph walk tests |
| SUB-02 | 05-01, 05-03 | Mark attributes important with direction + own tolerance | ✓ SATISFIED | `core/substitution.py` + `gui/requirements_editor.py`, per-type independence tested |
| SUB-03 | 05-01, 05-04 | Export to separate shareable file, load in a different session | ✓ SATISFIED | `core/requirements_repository.py`, cross-process round-trip test, atomic writes, strict refuse-never-coerce validation |
| SUB-04 | 05-01, 05-05 | Score candidates from a folder, 3-state ranking | ✓ SATISFIED | `core/substitution.py` scan/score/rank, `gui/candidate_results.py` model, delegate-painted colors |

REQUIREMENTS.md cross-reference: all five IDs (PARSE-02, SUB-01, SUB-02, SUB-03, SUB-04) are marked `[x]` and `Complete` with `Phase 5` mapping (lines 13, 43-46, 78, 90-93). No orphaned requirements found — REQUIREMENTS.md maps no additional IDs to Phase 5 beyond these five, and all five appear in at least one plan's `requirements:` frontmatter field.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK` debt markers found in any of the 13 phase-modified source files | — | Clean |
| `05-REVIEW-DISPOSITION.md` | CR-01 | Code review finding, severity **critical**, disposition **open** (unresolved): `core/mvr_repository.py:iter_fixtures` recurses once per scene-nesting level with no explicit depth cap; theorized native-stack-overflow DoS risk from a crafted `.mvr` within the existing size budget | ⚠️ Warning (see below) | Independently reproduced with hand-built MVRs nested 1,000–150,000 `<GroupObject>` levels; in every case Python's own recursion limit raised a catchable `RecursionError` well before any native-stack exhaustion, and `import_mvr`'s `except Exception` wrapper converted it to one friendly `MVRParseError` with exit code 0, no crash, no hang. The *practical* DoS risk did not reproduce on this stack (CPython 3.12 / pymvr 1.0.7). The reviewer's underlying point — there is no *explicit* depth bound, only reliance on CPython's own recursion-limit behavior — remains valid as a defense-in-depth gap and is still tracked `open`. Recommend the suggested explicit `MAX_SCENE_NESTING_DEPTH` guard as a follow-up hardening item; it does not block this phase's observable goal. |
| `05-REVIEW-DISPOSITION.md` | WR-01, WR-02, WR-03, IN-01 | Three open warnings + one info finding (misleading wording for one edge-case import message; `os.set_blocking` failure not wrapped in the typed-error contract; sequential `closeEvent` waits could stack; inconsistent error-message extraction between workers) | ℹ️ Info | All are narrow, non-crash-causing robustness/wording issues on rare paths; none affect the four roadmap Success Criteria or any must-have truth. Full test suite (462 tests) passes including every hostile-file hardening test. |

No blocker-level anti-patterns found. The one critical-severity open finding (CR-01) was independently re-tested and did not reproduce a crash under direct experimentation at 150x the depth needed to exceed Python's default recursion limit; it is reported here for transparency since it remains formally "open" in the phase's own code-review record, not because it failed verification.

### Human Verification Required

None required for the phase's four Success Criteria — all four are mechanically verified via passing automated tests that exercise the actual user-facing flow (`test_ld_to_shop_round_trip`, `test_find_substitutes_button_opens_one_window`, `test_check_inventory_with_these_sends_current_requirements`) plus a pixel-sampling test for color visibility in both themes (`test_traffic_lights_paint_in_both_themes`).

One item was already identified by the project's own `05-UI-REVIEW.md` as appropriately deferred to a human looking at the real rendered app (subjective readability/comfort of the traffic-light colors on an actual screen, not just channel-dominance via pixel sampling) — this is pre-existing, recorded in `05-05-SUMMARY.md` under `human_judgment: true`, and does not block this phase (`workflow.human_verify_mode = end-of-phase` design, consistent with Phase 2/3's own precedent).

### Gaps Summary

No gaps. All four ROADMAP Success Criteria are observably true in the codebase: the five-plan implementation (tracer in 05-01, then widening in 05-02 through 05-05) delivers a working, tested, end-to-end LD-to-shop workflow. All 462 tests pass (including the full hostile-file/hardening/architecture-guard suite, run with `-W error::DeprecationWarning`), all 26 declared artifacts across the 5 plans pass existence+substance checks, all 12 declared key links are wired, and all 5 requirement IDs (PARSE-02, SUB-01..04) are satisfied and correctly marked Complete in REQUIREMENTS.md with no orphans.

The phase's own code review (`05-REVIEW.md`/`05-REVIEW-DISPOSITION.md`) left one critical-severity finding (CR-01, unbounded MVR scene-nesting recursion) and three warnings formally "open" (untriaged) rather than disposed as fixed/accepted/deferred. Independent reproduction of CR-01 at depths up to 150,000 nesting levels did not surface a crash — Python's recursion limit catches it cleanly every time and the app shows a friendly error — so this does not block the phase goal, but it is flagged here because the phase's own quality gate left it unresolved rather than explicitly accepted.

---

_Verified: 2026-10-24_
_Verifier: Claude (gsd-verifier)_
