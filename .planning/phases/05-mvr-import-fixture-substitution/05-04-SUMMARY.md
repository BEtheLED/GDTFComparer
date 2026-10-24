---
phase: 05-mvr-import-fixture-substitution
plan: 04
subsystem: fixture-substitution
tags: [json, hardening, defusedxml-adjacent, requirements-file, sidecar]

requires:
  - phase: 05-mvr-import-fixture-substitution
    provides: "core.requirements_repository's v1 payload shape, save_requirements/load_requirements, SubstitutionWindow's Save/Open Requirements wiring (05-01)"
provides:
  - "Hardened suggested_file_name: NFC-normalized, strips reserved/control characters, collapses whitespace, caps length, falls back to 'Fixture'"
  - "_read_requirements_bytes: O_NONBLOCK + S_ISREG regular-file discipline mirroring core.hardening's WR-01 guard"
  - "_parse_payload: strict refusal of any requirements file not exactly understood -- exact key sets, bool-before-number checks, finite-number checks, duplicate-key/NaN/Infinity refusal, unique (category, element, attribute) triples"
  - "save_requirements' atomic temp-file-then-replace write, proven under failure injection to never leave a half-written file"
affects: [05-05-substitution-scoring-widening]

actuals:
  tokens: 11800
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - "_read_requirements_bytes mirrors core.hardening._read_file_bytes's _FileKind-free shape: O_NONBLOCK open, S_ISREG check on the same fd, capped read -- a JSON-specific sibling, not a second archive guard"
    - "json.loads(object_pairs_hook=_no_duplicate_keys, parse_constant=_refuse_constant) refuses duplicate JSON keys and raw NaN/Infinity tokens before any shape validation runs"
    - "_parse_payload validates by exact key-set equality at every level (top-level, fixture, each requirement) rather than checking for required keys and ignoring extras -- an extra key is damaged, not silently dropped"

key-files:
  created: []
  modified:
    - src/gdtf_comparer/core/requirements_repository.py
    - tests/core/test_requirements_repository.py
    - tests/gui/test_requirements_file.py

key-decisions:
  - "suggested_file_name order of operations: NFC-normalize first, then replace reserved/control characters with '_', then collapse whitespace, then strip spaces/dots from both ends, then truncate to 100 chars and strip again -- matches the plan's literal step order so '../../etc/passwd' degrades to a safe, non-dot-leading stem rather than an empty one"
  - "_parse_payload checks format before everything else, so another app's JSON (e.g. a compare-profiles file) is reported as 'not a requirements file' rather than 'damaged' -- distinct, more actionable wording for a simple wrong-file mistake"
  - "tolerance and target are returned as the parsed JSON value with no further coercion (float stays float, str stays str) -- the original 05-01 code's float(entry['tolerance']) was dropped once _parse_payload's own type/finite checks made coercion both unnecessary and tolerance-hiding"

requirements-completed: [SUB-03]

coverage:
  - id: D1
    description: "A requirements file saved in one session loads identically in a completely separate Python process, carrying non-ASCII names and float precision exactly (D-07)"
    requirement: SUB-03
    verification:
      - kind: unit
        ref: "tests/core/test_requirements_repository.py#test_round_trip_in_a_separate_process"
        status: pass
    human_judgment: false
  - id: D2
    description: "The saved file's key sets are exactly the D-09 shape at every level, with exactly one fixture and no stray paths"
    requirement: SUB-03
    verification:
      - kind: unit
        ref: "tests/core/test_requirements_repository.py#test_file_holds_exactly_one_fixture"
        status: pass
    human_judgment: false
  - id: D3
    description: "Saving or loading a requirements file never opens, reads or changes an adjacent MVR file (D-08)"
    requirement: SUB-03
    verification:
      - kind: unit
        ref: "tests/core/test_requirements_repository.py#test_saving_never_touches_an_mvr"
        status: pass
    human_judgment: false
  - id: D4
    description: "The suggested save name is always one safe file name, hardened against path separators, reserved characters, control characters, leading/trailing dots and over-length names"
    verification:
      - kind: unit
        ref: "tests/core/test_requirements_repository.py#test_suggested_file_name"
        status: pass
    human_judgment: false
  - id: D5
    description: "A damaged, foreign, oversized or newer-version requirements file is refused with one plain sentence naming the file and ending 'Nothing was loaded.', never coerced or partially loaded"
    requirement: SUB-03
    verification:
      - kind: unit
        ref: "tests/core/test_requirements_repository.py#test_refuses_damaged_or_foreign_files"
        status: pass
      - kind: unit
        ref: "tests/core/test_requirements_repository.py#test_refuses_raw_bytes"
        status: pass
      - kind: unit
        ref: "tests/core/test_requirements_repository.py#test_duplicate_json_key_is_refused"
        status: pass
      - kind: unit
        ref: "tests/core/test_requirements_repository.py#test_raw_nan_or_infinity_tokens_are_refused"
        status: pass
      - kind: unit
        ref: "tests/core/test_requirements_repository.py#test_deeply_nested_target_is_refused"
        status: pass
    human_judgment: false
  - id: D6
    description: "A named pipe or folder picked for a requirements file is refused without blocking the GUI thread"
    requirement: SUB-03
    verification:
      - kind: unit
        ref: "tests/core/test_requirements_repository.py#test_fifo_refused_without_blocking"
        status: pass
      - kind: unit
        ref: "tests/core/test_requirements_repository.py#test_folder_refused"
        status: pass
    human_judgment: false
  - id: D7
    description: "In the Check Inventory tab, a refused open leaves the previously loaded requirements and their summary line exactly as they were, and later inventory checks still score against them"
    requirement: SUB-03
    verification:
      - kind: unit
        ref: "tests/gui/test_requirements_file.py#test_failed_open_keeps_previous_requirements"
        status: pass
      - kind: unit
        ref: "tests/gui/test_requirements_file.py#test_failed_save_shows_dialog"
        status: pass
    human_judgment: false
  - id: D8
    description: "Saving never leaves a half-written file: a failed temp-file write or a failed os.replace leaves the previous file's exact bytes, raises with the original OSError as __cause__, and leaves no stray .tmp file"
    requirement: SUB-03
    verification:
      - kind: unit
        ref: "tests/core/test_requirements_repository.py#test_failed_replace_keeps_existing_file"
        status: pass
      - kind: unit
        ref: "tests/core/test_requirements_repository.py#test_failed_write_keeps_existing_file"
        status: pass
    human_judgment: false

duration: 55min
completed: 2026-10-24
status: complete
---

# Phase 5 Plan 4: Requirements File Safety Summary

**Strict JSON validation, a hardened O_NONBLOCK/S_ISREG read, and a cleaned-up suggested-name builder for the shared fixture-requirements sidecar file — any file not exactly understood is refused in one plain sentence, never coerced or partially loaded.**

## Performance

- **Duration:** ~55 min
- **Completed:** 2026-10-24T22:11:54Z
- **Tasks:** 3 (1 tracer, 2 TDD)
- **Files modified:** 3 (0 created, 3 modified)

## Accomplishments

- `suggested_file_name` rewritten to the plan's exact normalization pipeline: Unicode-NFC normalize, replace every filesystem-reserved or Unicode "Cc"/"Cs" control character with `"_"`, collapse whitespace runs, strip spaces/dots from both ends, truncate to 100 characters, fall back to `"Fixture"` when nothing is left.
- `_read_requirements_bytes` added, mirroring `core.hardening.read_gdtf_bytes`'s WR-01 regular-file discipline: one `os.open` with `O_NONBLOCK`, an `os.fstat`+`S_ISREG` check on that same descriptor, and a capped read — so a folder, named pipe or device file is refused immediately instead of freezing the GUI thread.
- `_parse_payload` rewritten for strict refusal rather than best-effort coercion: exact key sets at every level (top-level, fixture, each requirement), bool-excluded numeric type checks, `math.isfinite` range checks, a unique-triple check per `(category, element, attribute)`, and length/count caps (`MAX_TEXT_FIELD_LENGTH`, `MAX_REQUIREMENTS_COUNT`).
- `json.loads` now runs with `object_pairs_hook=_no_duplicate_keys` (refuses a repeated JSON key) and `parse_constant=_refuse_constant` (refuses raw `NaN`/`Infinity`/`-Infinity` tokens) — both refusals happen before shape validation even starts.
- `save_requirements`'s existing atomic write (same-folder `O_EXCL` temp file, `fsync`, `os.replace`, `finally`-cleanup) was proven under failure injection (a failed `os.replace`, a failed write) to leave the previous file's exact bytes and no stray `.tmp` file — no code changes were needed here; Task 1's write path already satisfied Task 3's requirements.
- Every message now comes from the plan's named templates (`DAMAGED_TEMPLATE`, `NOT_REQUIREMENTS_TEMPLATE`, `NEWER_VERSION_TEMPLATE`, `TOLERANCE_KIND_TEMPLATE`, `TOO_LARGE_TEMPLATE`, `NOT_A_FILE_TEMPLATE`, `UNREADABLE_TEMPLATE`, `SAVE_FAILED_TEMPLATE`), all ending "Nothing was loaded." for load failures.

## Task Commits

Each task was committed atomically:

1. **Task 1: End-to-end "a requirements file the LD saves opens identically in a separate session, and holds only that one fixture"** - `839a4c8` (feat)
2. **Task 2: A damaged, foreign, oversized or newer requirements file is refused in plain words, and the shop's current requirements stay as they were** - `939098e` (feat)
3. **Task 3: Saving never leaves a half-written requirements file** - `4a77287` (test)

**Plan metadata:** (this SUMMARY, committed by the orchestrator after wave merge)

## Files Created/Modified

- `src/gdtf_comparer/core/requirements_repository.py` - Hardened `suggested_file_name`, `_read_requirements_bytes`, `_no_duplicate_keys`, `_refuse_constant`, and a fully rewritten strict `_parse_payload`; message templates and limit constants added
- `tests/core/test_requirements_repository.py` - New file: cross-process round trip (D-07), exactly-one-fixture key sets (D-09), MVR-untouched (D-08), suggested-name hardening matrix, byte-identical re-save, a 28-case refusal matrix (mutated payloads + raw bytes + duplicate-key/NaN/deeply-nested edge cases), oversized/folder/FIFO/missing-file cases, and the Task 3 atomic-write failure-injection tests
- `tests/gui/test_requirements_file.py` - New file: a saved file opens identically in a fresh `SubstitutionWindow`; a failed open keeps the previously loaded requirements (and a later inventory check still scores against them); a failed save shows one dialog and creates no file

## Decisions Made

- **Normalization order matters for the dangerous names.** The plan's exact step order (normalize → replace reserved/control chars → collapse whitespace → strip dots/spaces → truncate → strip again) was followed literally, since reordering (e.g. stripping before replacing) would leave `"../../etc/passwd"` collapsing differently. Verified by the full parametrized `test_suggested_file_name` matrix, including the path-traversal and reserved-character cases.
- **Format check runs before every other check in `_parse_payload`**, so another app's JSON (e.g. a stray `profiles.json`) is reported as "not a fixture requirements file" rather than the more alarming "damaged" — a deliberately friendlier message for the common wrong-file mistake, matching the plan's explicit ordering note.
- **No type coercion on `target`/`tolerance` at load time.** 05-01's `load_requirements` had wrapped `tolerance` in `float(...)`; since `_parse_payload` now validates `type(tolerance) in (int, float)` directly and refuses anything else, the coercion was removed as redundant and potentially value-hiding (a `type()`-based check after an implicit `float()` cast would never see the original type).

## Deviations from Plan

None — plan executed exactly as written. Task 3 required no production-code changes (05-01's `save_requirements` write path, kept unchanged through Tasks 1 and 2, already satisfied every Task 3 requirement); all of Task 3's work was writing the failure-injection tests that prove it.

## Issues Encountered

None. All three tasks' `<verify>` commands (scoped test files, then the full suite with `-W error::DeprecationWarning`) and every `<acceptance_criteria>` grep passed on the first attempt — no repair cycles were needed. The one empirical check performed before writing the deeply-nested-JSON test (confirming CPython's C-accelerated `json` decoder raises `RecursionError` rather than segfaulting at a 100,000-deep nested-array string) was done interactively before committing the test, to avoid landing a test that could crash the interpreter on a different platform's build.

## User Setup Required

None — no external service configuration required. No new dependencies.

## Next Phase Readiness

`core.requirements_repository`'s file format is now hardened end to end: the one-way-door schema (`REQUIREMENTS_SCHEMA_VERSION`) is enforced by refusal rather than best-effort reading, and the atomic write is proven safe under injected failures. This plan touched only `core/requirements_repository.py` and its two test files — `gui/substitution_window.py` is unchanged (confirmed by this plan's own acceptance criteria), so Plan 05-05 (substitution scoring widening, depends on 05-02 and 05-03) is unaffected by this plan's changes.

No blockers. The full suite (365 tests at this plan's completion) passes with `-W error::DeprecationWarning`, including `tests/test_architecture.py`'s no-tempfile/no-shutil guard over `core/`.

---
*Phase: 05-mvr-import-fixture-substitution*
*Completed: 2026-10-24*

## Self-Check: PASSED

- FOUND: src/gdtf_comparer/core/requirements_repository.py
- FOUND: tests/core/test_requirements_repository.py
- FOUND: tests/gui/test_requirements_file.py
- FOUND: 839a4c8 (Task 1 commit, ancestor of HEAD)
- FOUND: 939098e (Task 2 commit, ancestor of HEAD)
- FOUND: 4a77287 (Task 3 commit, ancestor of HEAD)
