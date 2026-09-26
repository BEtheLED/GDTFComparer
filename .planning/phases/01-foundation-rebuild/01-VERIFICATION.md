---
phase: 01-foundation-rebuild
verified: 2026-09-26T15:45:00Z
status: human_needed
score: 9/9 must-haves verified
covered_files: [".planning/REQUIREMENTS.md", ".planning/phases/01-foundation-rebuild/01-01-PLAN.md", ".planning/phases/01-foundation-rebuild/01-01-SUMMARY.md", ".planning/phases/01-foundation-rebuild/01-02-PLAN.md", ".planning/phases/01-foundation-rebuild/01-02-SUMMARY.md", ".planning/phases/01-foundation-rebuild/01-03-PLAN.md", ".planning/phases/01-foundation-rebuild/01-03-SUMMARY.md", ".planning/phases/01-foundation-rebuild/01-04-PLAN.md", ".planning/phases/01-foundation-rebuild/01-04-SUMMARY.md", ".planning/phases/01-foundation-rebuild/01-05-PLAN.md", ".planning/phases/01-foundation-rebuild/01-05-SUMMARY.md", ".planning/phases/01-foundation-rebuild/01-06-PLAN.md", ".planning/phases/01-foundation-rebuild/01-06-SUMMARY.md", ".planning/phases/01-foundation-rebuild/01-07-PLAN.md", ".planning/phases/01-foundation-rebuild/01-07-SUMMARY.md", ".planning/phases/01-foundation-rebuild/01-08-PLAN.md", ".planning/phases/01-foundation-rebuild/01-08-SUMMARY.md", ".planning/phases/01-foundation-rebuild/01-REVIEW.md", "README.md", "pyproject.toml", "src/gdtf_comparer/__init__.py", "src/gdtf_comparer/app.py", "src/gdtf_comparer/core/__init__.py", "src/gdtf_comparer/core/comparator.py", "src/gdtf_comparer/core/errors.py", "src/gdtf_comparer/core/extract.py", "src/gdtf_comparer/core/hardening.py", "src/gdtf_comparer/core/models.py", "src/gdtf_comparer/core/repository.py", "src/gdtf_comparer/gui/__init__.py", "src/gdtf_comparer/gui/main_window.py", "src/gdtf_comparer/gui/table_model.py", "src/gdtf_comparer/gui/theme.py", "src/gdtf_comparer/gui/worker.py", "tests/conftest.py", "tests/core/test_comparator.py", "tests/core/test_extract.py", "tests/core/test_hardening.py", "tests/core/test_models.py", "tests/core/test_repository.py", "tests/gui/test_error_handling.py", "tests/gui/test_file_selection.py", "tests/gui/test_namespaced_rows.py", "tests/gui/test_shutdown.py", "tests/gui/test_theme.py", "tests/gui/test_unspecified_values.py", "tests/test_architecture.py", "tests/test_fixture_builder.py", "tests/test_walking_skeleton.py"]
covered_digest: "v1:sha256:620c0be649dd40e3f4ded6886da2285359c8d6374c65cb90ca2c1f9f88611e88"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 5/6
  gaps_closed:
    - "Truth 6 / CR-01: an attribute a manufacturer's file omitted is now shown/compared as N/A, never as pygdtf's silently-substituted GDTF-spec default"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "From the repo root run `PYTHONPATH=src .venv/bin/python -m gdtf_comparer.app` on macOS with System Settings > Appearance set to Light, then switch to Dark while the window is open."
    expected: "Flat Material-style widgets with blue accents (no stock Tk/native-legacy look); switching Appearance re-themes the open window within a second with no restart; table text, buttons and the error dialog stay clearly legible in both modes."
    why_human: "UI-01 'modernized, visually refreshed' and legibility are visual judgements no automated assertion can make. Carried forward unchanged from the original 01-VERIFICATION.md (harvested from 01-05-PLAN.md Task 1 human-check); none of the three gap-closure plans (01-06/07/08) touched theming, and 01-06-PLAN.md's own Flagged Assumptions explicitly says this stays in end-of-phase human verification, not re-planned."
  - test: "Follow README Setup + Run from a fresh terminal; pick one real target .gdtf and two or more real comparison .gdtf files (e.g. from GDTF-Share or a manufacturer site), click Run Comparison, then add a non-GDTF file renamed to .gdtf and run again."
    expected: "The window stays responsive while parsing; the table shows Beam rows per beam geometry path, Physical Properties rows per model plus one 'Fixture' Weight row, with every comparison file as a column; the renamed file produces one friendly dialog naming it, the table is cleared, and a following valid run works without restarting."
    why_human: "Real-world GDTF variety (multi-emitter fixtures, many models, real manufacturer quirks) and perceived responsiveness cannot be fully represented by synthetic test fixtures. Carried forward unchanged from the original 01-VERIFICATION.md (harvested from 01-05-PLAN.md Task 2 human-check); this is also the item that would surface any remaining N/A-vs-default edge case on a real manufacturer file."
---

# Phase 01: Foundation Rebuild Verification Report (Re-verification)

**Phase Goal:** Users can run the rebuilt app, pick a target and comparison `.gdtf` files, and get a correct, crash-free comparison in a modernized interface — replacing the old hand-rolled parser and tightly-coupled GUI end to end.
**Verified:** 2026-09-26T15:45:00Z
**Status:** human_needed
**Re-verification:** Yes — after gap-closure batch (01-06, 01-07, 01-08)

## What changed since the last verification

The prior 01-VERIFICATION.md (score 5/6, `gaps_found`) found one blocking gap
(Truth 6 / 01-REVIEW.md CR-01: omitted GDTF attributes were shown as pygdtf's
silently-substituted spec defaults instead of N/A) plus four non-blocking
code-review findings (WR-01 hang-on-special-file/close, WR-02
self-comparison, IN-01/IN-02 hygiene). Three gap-closure plans executed:

- **01-06** — presence-aware extraction (closes Truth 6 / CR-01)
- **01-07** — self-comparison guard + kept-surface tests + README fix (closes WR-02, IN-01, IN-02)
- **01-08** — special-file rejection + bounded window close (closes WR-01)

This re-verification independently re-derives whether each of these is
actually closed in the current codebase — it does not take the SUMMARY.md
files' or the fresh 01-REVIEW.md's claims at face value.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User selects a target GDTF and one or more comparison GDTFs and sees a comparison table populate without the app crashing | ✓ VERIFIED | Full suite run directly (`pytest -q`): **89 passed** (up from 66 at the last verification). `tests/test_walking_skeleton.py::test_gui_run_comparison_populates_table` and `test_app_module_launches` pass. |
| 2 | Attributes with the same name from different GDTF sections no longer collide or overwrite each other | ✓ VERIFIED | Unchanged mechanism (namespaced element paths + `_unique_path` suffixing), still exercised by `tests/core/test_extract.py`, `tests/core/test_comparator.py::test_no_attribute_collision`, `tests/gui/test_namespaced_rows.py` — all pass in the full run. |
| 3 | Selecting a corrupt or invalid GDTF/zip file shows a friendly error message instead of crashing the app | ✓ VERIFIED | `tests/core/test_hardening.py`, `tests/core/test_repository.py`, `tests/gui/test_error_handling.py` all pass; now additionally hardened for folders/pipes/devices (see Truth 8). |
| 4 | The app's interface has a modernized, visually refreshed look, not the stock Tkinter appearance | ✓ VERIFIED (mechanism) / human check pending | No theming code touched by the gap-closure batch (confirmed by `git diff --stat` scope of 01-06/07/08: `gui/theme.py` is untouched). `tests/gui/test_theme.py` (7 tests, one new since last verification) pass. Visual judgement remains a human-verification item, unchanged. |
| 5 | The GUI layer no longer calls parsing/comparison logic directly — that logic lives in a separate, independently testable service layer | ✓ VERIFIED | `tests/test_architecture.py` (6 tests) pass; read `gui/main_window.py` directly — its only new import surface added by 01-07 is stdlib `os`, no new `gdtf_comparer.core` import. |
| 6 | The comparison is "correct": an attribute a manufacturer's file omits is shown as not-specified, not silently as the GDTF-spec default as if the manufacturer had declared it (previously **FAILED** — 01-REVIEW.md CR-01) | ✓ **VERIFIED (gap closed)** | Independently reproduced outside the test suite (see Behavioral Spot-Checks): built a `<Beam Name="Beam"/>` with no attributes and `weight=None`; confirmed pygdtf itself still backfills `beam_angle=25.0, power_consumption=1000.0, beam_type='Wash'` and `properties.weight=0`, but `extract_attributes(fixture_type, validated.description_root)` now returns `None` (`"N/A"`) for every one of them. Also confirmed by direct code read of `core/extract.py` (presence check against `element.attrib`, lockstep-paired via `pygdtf.geometries.TAG_TO_GEOMETRY_CLASS`) and by 8 passing regression tests spanning extract/comparator/GUI levels. |
| 7 | A user can never compare a file against itself, in either direction (new — closes 01-REVIEW.md WR-02) | ✓ VERIFIED | Read `gui/main_window.py` directly: `_normalized_path` (realpath+normcase) is used consistently in both `add_compare_files` (refuses an alias of the target) and `set_target_file` (evicts an alias of the target from the comparison list), each with a status-bar message. `tests/gui/test_file_selection.py` (4 tests, including a `./`-segment and symlink alias case) pass. |
| 8 | Picking a folder, named pipe or device file as a GDTF gives a friendly error immediately instead of hanging the worker forever (new — closes the input half of 01-REVIEW.md WR-01) | ✓ VERIFIED | Read `core/hardening.py::read_gdtf_bytes` directly: single `os.open` with `O_NONBLOCK`, `os.fstat`+`stat.S_ISREG` check on the *same* descriptor before any read (no TOCTOU gap), friendly `GDTFValidationError("...not a regular file...")`. `tests/core/test_hardening.py::test_fifo_rejected_without_blocking` and `::test_directory_rejected` pass. |
| 9 | Closing the window while a comparison worker is stuck returns control within a few seconds, and the process still exits cleanly, instead of hanging or aborting (new, behavior-dependent — closes the close-path half of 01-REVIEW.md WR-01) | ✓ VERIFIED (behavioral test) | This is a cancellation/timeout invariant that presence-of-code cannot prove by itself, so it was run directly rather than trusted from the SUMMARY: `pytest tests/gui/test_shutdown.py -v` → both `test_close_returns_promptly_when_worker_is_stuck` (elapsed-time assertion against a worker deliberately blocked on a `threading.Event`) and `test_app_process_exits_when_worker_stuck_at_close` (subprocess exits with code 0 within 20s while a worker blocks forever) **PASS**. Code read confirms `closeEvent` uses `self._thread.wait(CLOSE_WAIT_TIMEOUT_MS)` (no unbounded `.wait()` remains — `grep -nE '\.wait\(\)' main_window.py` is empty) and `app.main` calls `os._exit(exit_code)` only when `window.is_comparison_running()` is still true after `app.exec()` returns. |

**Score:** 9/9 truths verified (0 present, behavior-unverified)

### Deferred Items (not gaps — explicitly scoped out by the plans themselves)

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | A declared-but-spec-invalid enum value (e.g. `BeamType="Foo"`, normalized by pygdtf to "Wash") is shown as pygdtf parses it rather than flagged as invalid | Phase 2 (ATTR-01, full attribute browsing) | 01-06-PLAN.md "Deferred" section: "Truth 6 is about omission; invalid-value surfacing belongs with Phase 2's full attribute browsing" |
| 2 | A "GDTF default" provenance hint (e.g. showing "25 (default)" instead of a bare value) | Not yet scheduled; `FixtureModel.fixture_type` retains pygdtf's defaults so a later phase can add this without re-deriving anything | 01-06-PLAN.md Decision Record, option (c), explicitly deferred |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/gdtf_comparer/core/hardening.py` | `ValidatedGDTF`/`prevalidate_gdtf_document`; single non-blocking open + `fstat`/`S_ISREG` | ✓ VERIFIED | Both present and wired; read directly. |
| `src/gdtf_comparer/core/extract.py` | Presence-aware `extract_attributes(fixture_type, description_root)`; `DescriptionMismatchError`; `_weight_declared`; `_geometry_children` | ✓ VERIFIED | All present; behavior independently reproduced (Truth 6). |
| `src/gdtf_comparer/core/repository.py` | `load()` threads `validated.description_root` into `extract_attributes` | ✓ VERIFIED | `grep -n "extract_attributes(fixture_type, validated.description_root)"` matches; old bytes-only `prevalidate_gdtf(path)` call in `load()` is gone. |
| `src/gdtf_comparer/gui/main_window.py` | `_normalized_path`; guarded `add_compare_files`/`set_target_file`; `CLOSE_WAIT_TIMEOUT_MS`; bounded `closeEvent` | ✓ VERIFIED | All present and wired; no unbounded `.wait()` or `.terminate(` remain. |
| `src/gdtf_comparer/app.py` | `os._exit(exit_code)` guarded by `window.is_comparison_running()` after `app.exec()` | ✓ VERIFIED | Present, matches design notes exactly. |
| `tests/core/test_extract.py`, `tests/core/test_comparator.py`, `tests/gui/test_unspecified_values.py` | Omission/declared-default/alignment/mismatch regression tests | ✓ VERIFIED | 8 named tests pass; independently reproduced outside the suite as well. |
| `tests/gui/test_file_selection.py` | WR-02 regression tests | ✓ VERIFIED | 4 tests pass. |
| `tests/gui/test_shutdown.py` | Bounded-close + process-exit tests | ✓ VERIFIED | 2 tests pass (see Truth 9). |
| `tests/core/test_hardening.py` (additions) | Special-file rejection tests | ✓ VERIFIED | 2 new tests pass; 12 pre-existing hardening tests unmodified and still pass. |
| `.planning/phases/01-foundation-rebuild/01-03-PLAN.md` | Previously-unresolved prohibition closed in place | ✓ VERIFIED | `grep -n "status: resolved"` and `grep -n "CLOSED by 01-06"` both match; no `status: unresolved` remains in the file. |
| `README.md` | 3.11+ floor stated; Safety section lists special-file refusal | ✓ VERIFIED | `grep -q "3.11 or newer"` and `grep -q "pipes"` both match. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `core/repository.py` | `core/hardening.py` | `prevalidate_gdtf_document(path)` before pygdtf sees any bytes | ✓ WIRED | Confirmed by direct read. |
| `core/repository.py` | `core/extract.py` | `extract_attributes(fixture_type, validated.description_root)` | ✓ WIRED | Confirmed. |
| `core/extract.py` | `pygdtf.geometries.TAG_TO_GEOMETRY_CLASS` | Lockstep child-tag filter shared with pygdtf's own walk | ✓ WIRED | Confirmed by direct read and by `test_presence_alignment_skips_references_and_unknown_tags` passing. |
| `gui/main_window.py::add_compare_files` | `gui/main_window.py::_normalized_path(self.target_file)` | Refuses a target alias before appending | ✓ WIRED | Confirmed. |
| `gui/main_window.py::set_target_file` | `compare_list.takeItem` | Evicts a promoted target from the comparison list | ✓ WIRED | Confirmed. |
| `gui/main_window.py::closeEvent` | `QThread.wait(CLOSE_WAIT_TIMEOUT_MS)` | Bounded wait instead of unbounded | ✓ WIRED | Confirmed; behaviorally proven (Truth 9). |
| `app.py::main` | `gui/main_window.py::is_comparison_running()` | Guards the `os._exit` fallback | ✓ WIRED | Confirmed; behaviorally proven (Truth 9). |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| `ComparisonTableModel` cell for an omitted attribute | `row.target_value` / `row.comparison_values` | `extract_attributes` now resolves this to `None` when `gdtf_name not in element.attrib`, i.e. from the real validated XML tree, not a static default | Yes — independently reproduced with a hand-built minimal GDTF (see Truth 6) | ✓ FLOWING (gap closed — previously ⚠️ STATIC on this exact path) |
| `ComparisonTableModel` cell for a declared attribute | same | Still `float(getattr(node, field_name))` from the real parsed `pygdtf.FixtureType` | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full suite passes | `.venv/bin/python -m pytest -q` | `89 passed in 10.95s` | ✓ PASS |
| Omitted attributes independently reproduced as N/A despite pygdtf backfill | Hand-built a `<Beam Name="Beam"/>` (no attrs) + `weight=None` GDTF, parsed with pygdtf directly, called `extract_attributes` outside the test suite | pygdtf: `beam_angle=25.0, power_consumption=1000.0, beam_type='Wash', properties.weight=0`. `extract_attributes` result: **all six Beam keys `None`, Weight `None`** | ✓ PASS (independently confirms Truth 6 is genuinely fixed, not just self-testing) |
| Self-comparison guard | `pytest tests/gui/test_file_selection.py -v` | 4/4 passed | ✓ PASS |
| Bounded close / prompt process exit | `pytest tests/gui/test_shutdown.py -v` | 2/2 passed | ✓ PASS |
| Architecture import-boundary guard | `pytest tests/test_architecture.py -q` | 6/6 passed | ✓ PASS |
| No debt markers | `grep -rnE "TBD|FIXME|XXX|TODO|HACK|PLACEHOLDER" src/ tests/ README.md` | no matches | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| PARSE-01 | 01-02, 01-03, 01-06 | pygdtf-based parsing, namespaced keys, no collision, correct omitted-vs-declared handling | ✓ SATISFIED | Namespacing (Truth 2) + correctness gap now closed (Truth 6). REQUIREMENTS.md already marks this `[x]`. |
| UI-01 | 01-05 | Modernized, visually refreshed interface | ✓ SATISFIED (mechanism); human visual check pending | Unchanged since last verification; theming untouched by gap closure. REQUIREMENTS.md still shows this unchecked (stale tracking, not a code defect — same note as the prior verification). |
| UI-02 | 01-01, 01-02, 01-05, 01-07 | GUI decoupled from parsing/comparison via service layer | ✓ SATISFIED | AST-enforced, still 6/6 green; 01-07's WR-02 fix stayed inside `gui/main_window.py` using only stdlib `os`. |
| RELI-01 | 01-04, 01-07, 01-08 | Friendly error on invalid/corrupt file, never a crash or a hang | ✓ SATISFIED | Original hardening/repository/error-handling tests plus new special-file and self-comparison tests all pass. |
| RELI-02 | 01-04, 01-08 | defusedxml + size limits against zip bombs/XXE; special-file DoS closed | ✓ SATISFIED | `tests/core/test_hardening.py` (14 tests now, up from 12) all pass; TOCTOU-safe single-descriptor check confirmed by direct read. |

No orphaned requirements: all five requirement IDs mapped to Phase 1 in `.planning/REQUIREMENTS.md` appear in at least one plan's `requirements:` frontmatter (PARSE-01: 01-06; RELI-01: 01-07, 01-08; RELI-02: 01-08).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/gdtf_comparer/core/hardening.py` | 110-111 | `os.set_blocking(fd, True)` is not wrapped in `try/except OSError`, unlike every other OS call in `read_gdtf_bytes` | ⚠️ Warning (new finding, 01-REVIEW.md re-review WR-01 — distinct from the historical WR-01 gap-closure item) | An exotic fd type could let a raw `OSError` escape this function's documented typed-error contract. Does not reproduce the original hang, does not leak the fd, and is caught generically by `ComparisonWorker.run`'s `except Exception` — so it degrades to a generic error message rather than crashing. Non-blocking per the review's own classification (0 critical, 1 warning). |
| `src/gdtf_comparer/core/extract.py` | 200-207 | `_weight_declared`'s docstring points to `Properties._read_xml` for the whole lookup chain, but half of it (`PhysicalDescriptions → Properties`) actually lives in `FixtureType.__init__` | ℹ️ Info (01-REVIEW.md re-review IN-01) | Documentation-only; the behavior itself is correct and verified (Truth 6). A future maintainer following the docstring to re-verify against a new pygdtf version would need to also check `FixtureType.__init__`. |

No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` markers found anywhere under `src/` or `tests/` (grepped directly). Both anti-patterns above are pre-existing findings from the fresh code review (01-REVIEW.md), already correctly classified there as non-blocking (0 critical), and neither regresses any of the 9 truths above.

## Human Verification Required

### 1. Visual theme appearance and legibility

**Test:** From the repo root run `PYTHONPATH=src .venv/bin/python -m gdtf_comparer.app` on macOS with System Settings > Appearance set to Light, then switch to Dark while the window is open.
**Expected:** Flat Material-style widgets with blue accents (no stock Tk/native-legacy look); switching Appearance re-themes the open window within a second without restarting; table text, buttons and the error dialog stay clearly legible in both modes.
**Why human:** UI-01's "modernized, visually refreshed" bar and legibility are visual judgements no automated assertion can make. Unchanged from the original verification — no gap-closure plan touched `gui/theme.py`.

### 2. Real-file end-to-end run

**Test:** Follow README Setup + Run from a fresh terminal; pick one real target `.gdtf` and two or more real comparison `.gdtf` files (e.g. from GDTF-Share or a manufacturer site), click Run Comparison, then add a non-GDTF file renamed to `.gdtf` and run again.
**Expected:** The window stays responsive while parsing; the table shows Beam rows per beam geometry path, Physical Properties rows per model plus one "Fixture" Weight row, with every comparison file as a column; the renamed file produces one friendly dialog naming it, the table is cleared, and a following valid run works without restarting. Any attribute a real manufacturer omitted should now read "N/A", not a plausible-looking default.
**Why human:** Real-world GDTF variety (multi-emitter fixtures, many models, real manufacturer quirks) and perceived responsiveness cannot be fully represented by synthetic test fixtures. This is also the best remaining check that the Truth-6 fix behaves correctly against real manufacturer files, not just synthetic ones.

## Gaps Summary

No gaps remain. The single blocking gap from the prior verification — Truth 6 /
01-REVIEW.md CR-01, where an attribute a manufacturer's file omitted was
silently shown as pygdtf's GDTF-spec default instead of "N/A" — is closed and
was independently re-derived here, not just accepted from the SUMMARY.md
files: I hand-built a minimal GDTF with an omitted Beam and Weight, confirmed
pygdtf itself still backfills its spec defaults (BeamAngle 25, PowerConsumption
1000, BeamType "Wash", Weight 0) into its own object model exactly as before,
and confirmed `extract_attributes` now correctly returns `None` for every one
of them by reading the validated `description.xml` tree in lockstep with
pygdtf's parsed model. All three non-blocking code-review findings this batch
targeted (WR-02 self-comparison, WR-01 special-file hang and close-path hang)
are also closed and independently verified — the close-path fix in particular
is a cancellation/timeout invariant, so it was proven with a targeted
behavioral test run (`tests/gui/test_shutdown.py`), not accepted on code
presence alone. IN-01/IN-02 hygiene items are closed with tests/doc fixes.

The full test suite grew from 66 to 89 passing tests with zero regressions.
The fresh code review (01-REVIEW.md) found 0 Critical findings against this
batch, one new non-blocking Warning (an unwrapped `OSError` on a narrow
`os.set_blocking` edge case) and one documentation Info nit — neither
reopens any of the 9 truths above or blocks phase completion.

Two human-verification items are carried forward unchanged from the original
verification (visual theme legibility, real-file end-to-end run) — neither
was in scope for the gap-closure batch, and neither is a new finding. Because
these remain open, phase status is `human_needed` rather than `passed`.

---

_Verified: 2026-09-26T15:45:00Z_
_Verifier: Claude (gsd-verifier)_
