---
phase: 01-foundation-rebuild
verified: 2026-09-26T14:30:00Z
status: gaps_found
score: 5/6 must-haves verified
covered_files: [".planning/REQUIREMENTS.md", ".planning/phases/01-foundation-rebuild/01-01-PLAN.md", ".planning/phases/01-foundation-rebuild/01-01-SUMMARY.md", ".planning/phases/01-foundation-rebuild/01-02-PLAN.md", ".planning/phases/01-foundation-rebuild/01-02-SUMMARY.md", ".planning/phases/01-foundation-rebuild/01-03-PLAN.md", ".planning/phases/01-foundation-rebuild/01-03-SUMMARY.md", ".planning/phases/01-foundation-rebuild/01-04-PLAN.md", ".planning/phases/01-foundation-rebuild/01-04-SUMMARY.md", ".planning/phases/01-foundation-rebuild/01-05-PLAN.md", ".planning/phases/01-foundation-rebuild/01-05-SUMMARY.md", ".planning/phases/01-foundation-rebuild/01-REVIEW.md", "README.md", "pyproject.toml", "src/gdtf_comparer/__init__.py", "src/gdtf_comparer/app.py", "src/gdtf_comparer/core/__init__.py", "src/gdtf_comparer/core/comparator.py", "src/gdtf_comparer/core/errors.py", "src/gdtf_comparer/core/extract.py", "src/gdtf_comparer/core/hardening.py", "src/gdtf_comparer/core/models.py", "src/gdtf_comparer/core/repository.py", "src/gdtf_comparer/gui/__init__.py", "src/gdtf_comparer/gui/main_window.py", "src/gdtf_comparer/gui/table_model.py", "src/gdtf_comparer/gui/theme.py", "src/gdtf_comparer/gui/worker.py", "tests/conftest.py", "tests/core/test_comparator.py", "tests/core/test_extract.py", "tests/core/test_hardening.py", "tests/core/test_repository.py", "tests/gui/test_error_handling.py", "tests/gui/test_namespaced_rows.py", "tests/gui/test_theme.py", "tests/test_architecture.py", "tests/test_fixture_builder.py", "tests/test_walking_skeleton.py"]
covered_digest: "v1:sha256:6ad6f5cfcd1cfccb9fcc70e02d123fbe23cef9a4cfb4204c158c2df392ec8df0"
behavior_unverified: 0
overrides_applied: 0
gaps:
  - truth: "The comparison is 'correct' — an attribute a manufacturer omitted from description.xml is shown/compared as 'not specified', not silently as if the manufacturer had declared the GDTF-spec default value"
    status: failed
    reason: "pygdtf 1.4.5 backfills its own library defaults (BeamAngle=25.0, FieldAngle=25.0, PowerConsumption=1000, LuminousFlux=10000, ColorTemperature=6000, BeamType='Wash', Weight=0.0) in-object for any omitted optional attribute — it never leaves the field None/absent. core/extract.py's `is None` / `getattr(..., None)` guards were written to detect omission this way, but that code path is unreachable: I reproduced it directly (see Behavioral Spot-Checks) by building a <Beam Name=\"Beam\"/> with no other attributes and a <Properties> block with weight=None — extract_attributes returned BeamAngle=25.0, PowerConsumption=1000.0, Weight=0.0, etc., not None/N/A. Two real fixtures that both simply never bothered to declare BeamAngle/Weight are reported as identical (\"differs\": False) instead of both showing N/A, which is the exact scenario the app exists to catch (the project's stated Core Value is 'see which attributes actually differ'). This was independently confirmed via the 01-REVIEW.md code review (CR-01, Critical) and is explicitly recorded as an UNRESOLVED prohibition in 01-03-PLAN.md's must_haves (status: unresolved) — it was surfaced for a human decision, not silently missed, but no fix has been applied and no regression test exists for the whole-attribute-omitted (as opposed to whole-node-absent) case."
    artifacts:
      - path: "src/gdtf_comparer/core/extract.py"
        issue: "Lines 124-155: `is None` branches for Weight/BeamAngle/FieldAngle/PowerConsumption/LuminousFlux/ColorTemperature/BeamType are dead code against the pinned pygdtf==1.4.5, which never returns None for these fields when the XML attribute/element is omitted — it substitutes a GDTF-spec default in the object model before extract_attributes ever sees it."
    missing:
      - "Either (a) explicitly accept and document that GDTF-spec defaults are the displayed 'effective' value (drop the misleading is-None branches and update the docstring/UI to stop implying None-on-omission is supported for these fields), or (b) detect true omission independently of pygdtf's backfilled object model (e.g. a lightweight presence check over the raw validated XML bytes already available from core.hardening before pygdtf parses them) so an omitted attribute renders as N/A regardless of pygdtf's default-substitution."
      - "A regression test that builds a <Beam>/<Properties> block with the individual attribute omitted (not the whole node omitted) and asserts the resulting AttributeKey value / format_value() output reflects the chosen resolution."
deferred: []
human_verification:
  - test: "From the repo root run `PYTHONPATH=src .venv/bin/python -m gdtf_comparer.app` on macOS with System Settings > Appearance set to Light, then switch to Dark while the window is open."
    expected: "Flat Material-style widgets with blue accents (no stock Tk/native-legacy look); switching Appearance re-themes the open window within a second with no restart; table text, buttons and the error dialog stay clearly legible in both modes."
    why_human: "UI-01 'modernized, visually refreshed' and legibility are visual judgements no automated assertion can make (harvested from 01-05-PLAN.md Task 1 human-check, deferred to end-of-phase per HUMAN_VERIFY_MODE=end-of-phase; the executor's own worktree was headless and could not perform it)."
  - test: "Follow README Setup + Run from a fresh terminal; pick one real target .gdtf and two or more real comparison .gdtf files (e.g. from GDTF-Share or a manufacturer site), click Run Comparison, then add a non-GDTF file renamed to .gdtf and run again."
    expected: "The window stays responsive while parsing; the table shows Beam rows per beam geometry path, Physical Properties rows per model plus one 'Fixture' Weight row, with every comparison file as a column; the renamed file produces one friendly dialog naming it, the table is cleared, and a following valid run works without restarting."
    why_human: "Real-world GDTF variety (multi-emitter fixtures, many models, real manufacturer quirks) and perceived responsiveness cannot be fully represented by synthetic test fixtures (harvested from 01-05-PLAN.md Task 2 human-check, RESEARCH Open Question 2)."
---

# Phase 01: Foundation Rebuild Verification Report

**Phase Goal:** Users can run the rebuilt app, pick a target and comparison `.gdtf` files, and get a correct, crash-free comparison in a modernized interface — replacing the old hand-rolled parser and tightly-coupled GUI end to end.
**Verified:** 2026-09-26T14:30:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Process Note: Roadmap `mode: mvp` vs. non-user-story goal

`gsd_run query roadmap.get-phase 1` reports `Mode: mvp`, but the phase goal is
plain prose, not `As a / I want to / so that` form
(`gsd_run query user-story.validate --story "<goal>" --pick valid` returns
`false`). Every one of the five PLAN.md files in this phase independently
flags this same discrepancy under "Flagged Assumptions" ("ROADMAP Goal is not
in As a/I want to/so that form; MVP mode forbids inventing one, so the goal is
quoted verbatim... Run `/gsd-mvp-phase 1` if a user-story framing is wanted"),
so this is a pre-existing, planning-time-acknowledged condition, not something
newly discovered here. Rather than refuse verification outright (which would
leave a fully-executed, already-reviewed phase with no assessment at all),
this report proceeds with standard goal-backward verification against the
roadmap's five literal Success Criteria, which are well-formed observable
truths independent of user-story framing. Recommend running `/gsd-mvp-phase 1`
before the next MVP-mode phase to close this gap in the workflow itself.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User selects a target GDTF and one or more comparison GDTFs and sees a comparison table populate without the app crashing | ✓ VERIFIED | `tests/test_walking_skeleton.py::test_gui_run_comparison_populates_table` passes; manually launched `PYTHONPATH=src .venv/bin/python -m gdtf_comparer.app` under `QT_QPA_PLATFORM=offscreen` and confirmed the process stays alive (matches `test_app_module_launches`). Full suite: 66 passed. |
| 2 | Attributes with the same name from different GDTF sections no longer collide or overwrite each other | ✓ VERIFIED | `src/gdtf_comparer/core/extract.py`'s `iter_geometry_paths` + `_unique_path` namespace every Beam/Model element by full path with `#N` suffixing for duplicates; `tests/core/test_extract.py::test_two_beams_same_names_do_not_collide`, `test_duplicate_geometry_paths_get_suffix`, `tests/core/test_comparator.py::test_no_attribute_collision`, and `tests/gui/test_namespaced_rows.py::test_table_shows_distinct_element_paths` all pass and were read directly — the mechanism genuinely prevents collision. |
| 3 | Selecting a corrupt or invalid GDTF/zip file shows a friendly error message instead of crashing the app | ✓ VERIFIED | `src/gdtf_comparer/core/hardening.py` (defusedxml forbid_dtd/forbid_entities/forbid_external, size/ratio caps) + `core/errors.py` (typed `GDTFError` hierarchy) + `core/repository.py` (`prevalidate_gdtf` before any pygdtf parse) + `gui/worker.py`/`gui/main_window.py` (typed-error → plain-text `QMessageBox`). `tests/core/test_hardening.py` (12), `tests/core/test_repository.py` (10), `tests/gui/test_error_handling.py` (7) all pass — read directly, not vacuous. |
| 4 | The app's interface has a modernized, visually refreshed look, not the stock Tkinter appearance | ✓ VERIFIED (mechanism) / human check pending | `src/gdtf_comparer/gui/theme.py` applies qt-material (`dark_blue.xml`/`light_blue.xml`) at startup via `app.py`'s `install_os_theme(app)`, follows `QStyleHints.colorSchemeChanged` live, is idempotent. `tests/gui/test_theme.py` (6 tests) pass. Actual visual "looks modern"/legibility judgement requires a real display — harvested as a human-verification item below (the plan itself scoped this as a human-check; the executor ran headless). |
| 5 | The GUI layer no longer calls parsing/comparison logic directly — that logic lives in a separate, independently testable service layer | ✓ VERIFIED | `tests/test_architecture.py` is an AST-based (not grep) import-boundary guard: `test_gui_does_not_import_parsing_libraries`, `test_gui_uses_only_core_service_surface`, `test_core_is_qt_free`, plus a non-vacuity proof (`test_import_checker_detects_violations`). All 6 tests pass. Manually confirmed `gui/main_window.py`, `gui/worker.py` import only `gdtf_comparer.core.comparator`/`core.models`/`core.errors`, never `pygdtf`/`zipfile`/`defusedxml`. |
| 6 | The comparison is "correct": an attribute a manufacturer's file omits is shown as not-specified, not silently as the GDTF-spec default as if the manufacturer had declared it | ✗ FAILED | See Gaps below. Confirmed independently by direct reproduction (Behavioral Spot-Checks) and by 01-REVIEW.md CR-01 (Critical). |

**Score:** 5/6 truths verified (0 present, behavior-unverified)

Note: Truth 6 is not one of the roadmap's 5 literally-numbered Success
Criteria, but is derived directly from the phase goal's own word "correct"
and from the explicit instruction accompanying this verification request to
factor the code review's CR-01 finding into the must-haves assessment. It is
also directly tied to the project's stated Core Value ("see which attributes
actually differ") in `.claude/CLAUDE.md`.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pyproject.toml` | Pinned deps, src-layout, pytest+pytest-qt config | ✓ VERIFIED | All exact pins present; `requires-python = ">=3.11"`; `pythonpath = ["src"]`; `qt_api = "pyside6"`; gui-script entry point declared. |
| `src/gdtf_comparer/core/models.py` | AttributeKey, FixtureModel, ComparisonRow, ComparisonResult | ✓ VERIFIED | All classes present, zero Qt imports, no module-level mutable state. |
| `src/gdtf_comparer/core/extract.py` | Namespaced per-Beam/Model extraction | ⚠️ VERIFIED (wired) / see gap | Present, wired, namespacing correct; but omitted-vs-defaulted value handling is broken (Truth 6). |
| `src/gdtf_comparer/core/repository.py` | `FixtureRepository.load` via pygdtf, pre-validated | ✓ VERIFIED | `prevalidate_gdtf` runs before `pygdtf.FixtureType`; typed errors; no disk writes; stub-fixture defence in depth. |
| `src/gdtf_comparer/core/comparator.py` | `compare` / `compare_files` | ✓ VERIFIED | Ordered-union keying, stable category sort, all-or-nothing batch load. |
| `src/gdtf_comparer/core/hardening.py` | Size/ratio limits, defusedxml pre-parse | ✓ VERIFIED | `forbid_dtd=True`, `forbid_entities=True`, `forbid_external=True`; capped reads never trust the zip header alone. |
| `src/gdtf_comparer/core/errors.py` | Typed GDTFError hierarchy | ✓ VERIFIED | `GDTFError`/`GDTFValidationError`/`GDTFUnsafeFileError`/`GDTFParseError` with `user_message`. |
| `src/gdtf_comparer/gui/worker.py` | ComparisonWorker on QThread | ✓ VERIFIED | Only emits signals, never touches widgets; catches `GDTFError` and generic `Exception` separately. |
| `src/gdtf_comparer/gui/table_model.py` | QAbstractTableModel over ComparisonResult | ✓ VERIFIED | `find_row`, `data`/`headerData` render real values from `ComparisonResult.rows`, not placeholders. |
| `src/gdtf_comparer/gui/main_window.py` | File pickers, Run Comparison, QThread lifecycle | ✓ VERIFIED | `moveToThread`, single `run_button.setEnabled(True)` call site in `_on_thread_finished`, `closeEvent` quits+waits the thread. |
| `src/gdtf_comparer/gui/theme.py` | qt-material OS-following theme | ✓ VERIFIED | `colorSchemeChanged.connect`, idempotent `apply_theme`, single-follower reuse. |
| `src/gdtf_comparer/app.py` | Composition root | ✓ VERIFIED | `create_main_window` installs theme before constructing `MainWindow`; documented run command works (manually launched). |
| `tests/test_architecture.py` | AST import-boundary guard | ✓ VERIFIED | Non-vacuous (self-test), scans ≥4 modules per package, all 6 tests pass. |
| `BEtheLD` (deletion) | Legacy Tkinter script removed | ✓ VERIFIED | `ls BEtheLD` → No such file; `git ls-files BEtheLD` empty. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `gui/main_window.py` | `gui/worker.py` | `moveToThread` + signal wiring | ✓ WIRED | Confirmed by direct read: `thread.started.connect(worker.run)`, both result signals → `thread.quit`. |
| `gui/worker.py` | `core/comparator.py` | module-level `from gdtf_comparer.core.comparator import compare_files` | ✓ WIRED | Confirmed. |
| `core/comparator.py` | `core/repository.py` | `FixtureRepository` used in `compare_files` | ✓ WIRED | Confirmed. |
| `core/repository.py` | `core/extract.py` | `extract_attributes(fixture_type)` | ✓ WIRED | Confirmed. |
| `core/repository.py` | `core/hardening.py` | `prevalidate_gdtf(path)` before pygdtf call | ✓ WIRED | Confirmed — runs before `pygdtf.FixtureType`. |
| `gui/main_window.py` | `gui/table_model.py` | `on_comparison_ready → table_model.set_result(result)` | ✓ WIRED | Confirmed. |
| `app.py` | `gui/theme.py` | `install_os_theme(app)` | ✓ WIRED | Confirmed, called before `MainWindow()` construction. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| `ComparisonTableModel` | `row.target_value` / `row.comparison_values` | `ComparisonResult.rows` ← `compare()` ← `FixtureModel.attributes` ← `extract_attributes(fixture_type)` ← real `pygdtf.FixtureType` parse of user-selected file | Yes, for structure/namespacing | ✓ FLOWING (with caveat: individual scalar values for omitted attributes are pygdtf's spec defaults, not "no data" — Truth 6 gap) |
| `MainWindow` header labels | `result.target.file_name` / comparison file names | Real `os.path.basename(source_path)` of user-picked files | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full suite passes | `.venv/bin/python -m pytest -q` | `66 passed in 4.06s` | ✓ PASS |
| App launches and stays alive | `QT_QPA_PLATFORM=offscreen PYTHONPATH=src .venv/bin/python -m gdtf_comparer.app` (backgrounded, checked after 2s) | Process alive, no crash | ✓ PASS |
| pygdtf backfills defaults for omitted attributes (independent repro of CR-01) | Built a `<Beam Name="Beam"/>` with no other attrs + `<Properties>` with `weight=None`, ran `extract_attributes` on the parsed `pygdtf.FixtureType` | `BeamAngle=25.0, FieldAngle=25.0, PowerConsumption=1000.0, LuminousFlux=10000.0, ColorTemperature=6000.0, BeamType='Wash', Weight=0.0` — none `None`/N/A | ✗ FAIL (confirms Truth 6 gap) |
| `GeometryBeam.__init__` defaults inspected directly | `inspect.getsource(pygdtf.geometries.GeometryBeam.__init__)` | Confirms `power_consumption: float = 1000`, `beam_angle: float = 25.0`, etc. as constructor defaults, always assigned | ✓ PASS (confirms root cause) |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| PARSE-01 | 01-02, 01-03 | pygdtf-based parsing, namespaced keys, no collision | ✓ SATISFIED (collision-avoidance); ⚠️ partial on "correct" values | Namespacing verified (Truth 2); the default-vs-omitted value defect (Truth 6) is a separate correctness gap not explicitly covered by PARSE-01's literal wording, but bears on it. |
| UI-01 | 01-05 | Modernized, visually refreshed interface | ✓ SATISFIED (mechanism); human visual check pending | See Truth 4. |
| UI-02 | 01-01, 01-02, 01-05 | GUI decoupled from parsing/comparison via service layer | ✓ SATISFIED | AST-enforced (`tests/test_architecture.py`), verified non-vacuous. |
| RELI-01 | 01-04 | Friendly error on invalid/corrupt file, not a crash | ✓ SATISFIED | `tests/core/test_repository.py`, `tests/gui/test_error_handling.py`. |
| RELI-02 | 01-04 | defusedxml + size limits against zip bombs/XXE | ✓ SATISFIED | `tests/core/test_hardening.py` (XXE, billion-laughs, ratio, size caps all covered). |

No orphaned requirements: `.planning/REQUIREMENTS.md` maps exactly PARSE-01, UI-01, UI-02, RELI-01, RELI-02 to Phase 1, and all five appear in at least one plan's `requirements:` frontmatter. (Note: `REQUIREMENTS.md`'s traceability table still shows all rows as "Pending" — this is stale tracking metadata, not a code defect; recommend updating it at milestone close.)

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/gdtf_comparer/gui/main_window.py` | 226-231 | `closeEvent` calls `QThread.wait()` with no timeout | ⚠️ Warning (carried from 01-REVIEW.md WR-01) | A worker thread blocked on a pathological file read (named pipe, stalled mount) can hang the whole app on close with no way to force-quit from the UI. Narrow edge case, not a normal-usage crash; does not block any stated must-have. |
| `src/gdtf_comparer/gui/main_window.py` | 133-146 | `add_compare_files` does not check against `self.target_file` | ⚠️ Warning (carried from 01-REVIEW.md WR-02) | User can compare a file against itself with no indication; misleading "no diffs" result, but not a crash or data-loss issue. |
| `src/gdtf_comparer/core/models.py` / `gui/theme.py` | — | `ComparisonRow.any_differs`, `OsThemeFollower.current_theme` unused | ℹ️ Info (carried from 01-REVIEW.md IN-01) | Dead public surface, likely scaffolding for Phase 2 diff-highlighting; not a functional defect. |
| `README.md` | 17, 24 | Setup says `python3.12` while `requires-python = ">=3.11"` | ℹ️ Info (carried from 01-REVIEW.md IN-02) | Cosmetic documentation mismatch, does not affect a 3.11 install. |

No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` markers found anywhere under `src/` or `tests/` (grepped directly). No hardcoded empty-data stubs found flowing to the UI.

## Human Verification Required

### 1. Visual theme appearance and legibility

**Test:** From the repo root run `PYTHONPATH=src .venv/bin/python -m gdtf_comparer.app` on macOS with System Settings > Appearance set to Light, then switch to Dark while the window is open.
**Expected:** Flat Material-style widgets with blue accents (no stock Tk/native-legacy look); switching Appearance re-themes the open window within a second without restarting; table text, buttons and the error dialog stay clearly legible in both modes.
**Why human:** UI-01's "modernized, visually refreshed" bar and legibility are visual judgements no automated assertion can make. This item was scoped as an explicit `<human-check>` in 01-05-PLAN.md Task 1 and deferred to end-of-phase per `HUMAN_VERIFY_MODE=end-of-phase`; the executor's worktree ran headless (`QT_QPA_PLATFORM=offscreen`) and could not perform it.

### 2. Real-file end-to-end run

**Test:** Follow README Setup + Run from a fresh terminal; pick one real target `.gdtf` and two or more real comparison `.gdtf` files (e.g. from GDTF-Share or a manufacturer site), click Run Comparison, then add a non-GDTF file renamed to `.gdtf` and run again.
**Expected:** The window stays responsive while parsing; the table shows Beam rows per beam geometry path, Physical Properties rows per model plus one "Fixture" Weight row, with every comparison file as a column; the renamed file produces one friendly dialog naming it, the table is cleared, and a following valid run works without restarting.
**Why human:** Real-world GDTF variety (multi-emitter fixtures, many models, real manufacturer quirks) and perceived responsiveness cannot be fully represented by synthetic test fixtures. Scoped as an explicit `<human-check>` in 01-05-PLAN.md Task 2.

## Gaps Summary

The phase's architecture, reliability hardening, theming and decoupling are
all solidly built and independently verified — 5 of the 5 literal roadmap
Success Criteria pass on direct inspection and test evidence, not just
SUMMARY claims. The one blocking gap is a genuine, already-self-diagnosed
correctness defect: `core/extract.py` cannot distinguish "the manufacturer
never specified this attribute" from "pygdtf's spec-mandated default value,"
because the pinned `pygdtf==1.4.5` backfills defaults in its own object
model and never exposes the distinction. This was flagged as an UNRESOLVED
prohibition inside 01-03-PLAN.md itself and independently caught by the
01-REVIEW.md code review as a Critical finding — it was not silently missed,
but it also was not fixed, and no regression test guards it. Because the
phase goal explicitly promises a "correct" comparison and the project's
stated Core Value is "see which attributes actually differ," this defect is
treated as a blocking gap rather than a deferred nice-to-have: a manufacturer
that never states a beam's power consumption will currently show "1000"
(implying the file said so) and two fixtures that both omit Weight will
compare as identical at "0" instead of both showing "N/A".

Two Warning-level and two Info-level items from the code review (thread-close
timeout, self-comparison, dead code, README version mismatch) remain
unaddressed but are not blocking — they don't violate any stated must-have
truth for this phase.

---

_Verified: 2026-09-26T14:30:00Z_
_Verifier: Claude (gsd-verifier)_
