---
phase: 03-compare-profiles-export
verified: 2026-10-05T12:00:00Z
status: human_needed
score: 37/38 must-haves verified
covered_files: [".planning/REQUIREMENTS.md", ".planning/phases/03-compare-profiles-export/03-01-PLAN.md", ".planning/phases/03-compare-profiles-export/03-01-SUMMARY.md", ".planning/phases/03-compare-profiles-export/03-02-PLAN.md", ".planning/phases/03-compare-profiles-export/03-02-SUMMARY.md", ".planning/phases/03-compare-profiles-export/03-03-PLAN.md", ".planning/phases/03-compare-profiles-export/03-03-SUMMARY.md", ".planning/phases/03-compare-profiles-export/03-04-PLAN.md", ".planning/phases/03-compare-profiles-export/03-04-SUMMARY.md", ".planning/phases/03-compare-profiles-export/03-REVIEW.md", ".planning/phases/03-compare-profiles-export/03-UAT.md", "src/gdtf_comparer/app.py", "src/gdtf_comparer/core/errors.py", "src/gdtf_comparer/core/profile_repository.py", "src/gdtf_comparer/gui/attribute_picker.py", "src/gdtf_comparer/gui/main_window.py", "tests/conftest.py", "tests/core/test_profile_repository.py", "tests/gui/test_compare_list_match_indicator.py", "tests/gui/test_profile_manage.py", "tests/gui/test_profile_portability.py", "tests/gui/test_profile_toolbar.py", "tests/test_architecture.py"]
covered_digest: "v1:sha256:c70115522ba54f81ab03a78febca667839cc02c47acdec5c9f063e9eb2b6c380"
behavior_unverified: 0
overrides_applied: 0
behavior_unverified_items: []
re_verification:
  previous_status: human_needed
  previous_score: 29/30
  gaps_closed:
    - "Real-app whole-phase walkthrough (restart persistence, D-03 reload, D-06 message, rename/delete) — actually performed by the user via 03-UAT.md; only the toolbar-clipping issue (G-03-1) was reported, everything else implicitly passed"
    - "Crash/power-loss resilience of profiles.json writes — 03-UAT.md test 2 explicitly judged 'pass'"
    - "G-03-1: profile toolbar clipping ('No si▾' / 'AVE.' / 'M...e') — fixed by splitting into two stacked rows (profile_combo_row / profile_actions_row), verified by a new measured no-clip test passing in both qt-material themes at both the 260px default and the new 240px drag floor"
    - "G-03-2 (new scope approved during UAT): per-file match/no-match indicator dot on the 'Compare with' list — implemented, reusing ComparisonRow.differs with zero new comparison logic, 12 passing tests"
    - "Code-review WR-01 (stale indicator on re-run/failed re-run) — fixed in commit 564217d; confirmed present in code (main_window.py:559, :879) with 2 passing regression tests"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Real-app confirmation of the G-03-1 layout fix and G-03-2 match-indicator feature together (03-04-PLAN.md Task 2's own <human-check>, explicitly carried forward to /gsd-verify-work and not yet re-run against the fixed code per 03-UAT.md's git history — 03-UAT.md has not been updated since the gap-closure plan landed)."
    expected: "Per 03-04-PLAN.md's <expected>: (1) with two comparison files added before running, both show a small gray dot; (2) after Run Comparison, dot colors update to green (close to target) / red (different), and hovering each shows the file's path plus a plain-language sentence explaining the color; (3) the dropdown, 'Save…' and 'Manage' are all fully readable at the panel's default width AND at the narrowest point the Attributes-panel divider can be dragged to, in real macOS rendering — nothing reads as 'AVE.' or 'M...e' or 'No si▾'; (4) unticking every checked attribute turns both dots gray again; (5) adding one more comparison file turns every dot (including the two pre-existing ones) gray again until the next Run Comparison."
    why_human: "Every automated test in this phase (including the new clipping test and the match-indicator suite) runs on the offscreen Qt platform (QT_QPA_PLATFORM=offscreen). The offscreen tests prove the layout math and state-machine logic are correct, but real native widget chrome rendering (qt-material styling, font metrics, actual screen DPI) at a user-dragged panel width, and real dot-color rendering against that chrome, cannot be fully judged from a headless run. This is the exact gap 03-04-PLAN.md's own human-check names, not one introduced by this verification."
---

# Phase 3: Compare Profiles Verification Report

**Phase Goal:** Users can save and reload reusable attribute selections ("compare profiles") for future comparisons.
**Verified:** 2026-10-05T12:00:00Z
**Status:** human_needed
**Re-verification:** Yes — after gap-closure plan 03-04 (G-03-1, G-03-2) and code-review fix WR-01
**Mode:** mvp (ROADMAP Phase 3 `Mode: mvp`)

## User Story / Goal

As a lighting/AV professional checking whether a substitute fixture measures up, I want to save the attributes I care about as a named spec sheet and reload it against any fixture files, so that I can see at a glance whether a candidate has what I need, without re-ticking attributes or emailing back and forth with a vendor.

(Present verbatim in 03-01-PLAN.md's "Phase Goal" section, assembled from 03-CONTEXT.md D-01 and the user's own quoted scenario — the ROADMAP Goal line itself is not in user-story form.)

## What changed since the previous verification

The previous 03-VERIFICATION.md (2026-10-04T23:40:00Z) covered only Plans 03-01/02/03 and routed two items to human verification: (1) a real-app, real-restart walkthrough, and (2) the crash/power-loss backstop truth. The user then actually performed that walkthrough as UAT (`03-UAT.md`): the crash-resilience judgment call passed outright, and the full restart/reload/rename/delete flow passed except for one reported defect (G-03-1, toolbar clipping) plus one piece of new scope requested on the spot (G-03-2, a match/no-match indicator dot). Plan 03-04 closed both gaps, and a subsequent code review (`03-REVIEW.md`) found and the executor fixed one additional bug in the new G-03-2 feature (WR-01: stale indicator on re-run/failure). This report re-verifies the whole phase, including 03-04 and the WR-01 fix, from scratch.

## User Flow Coverage

| # | Step | Expected | Evidence in codebase | Status |
|---|------|----------|----------------------|--------|
| 1 | User ticks the attributes they care about | Picker records the checked (category, attribute) set | `AttributePicker.checked_attributes()` (Phase 2, unchanged) | VERIFIED |
| 2 | User clicks "Save…", types a name | Exactly the checked set is written to one atomic `profiles.json`; Cancel writes nothing | `MainWindow._save_profile`; `test_cancelled_save_writes_nothing` | VERIFIED |
| 3 | App is closed and reopened (real restart) | Saved profile is listed in the dropdown | `ProfileRepository.load_all()` reads the real per-user `profiles.json`; **actually exercised by the user in 03-UAT.md** (quit via Cmd+Q, reopened, loaded the profile) — only the toolbar-clipping defect was reported, implying this step passed | VERIFIED (human-confirmed via UAT) |
| 4 | User picks the profile from the dropdown | Checked set is replaced exactly (D-03); not widened by defaults | `AttributePicker.set_checked()`; `activated`-only wiring; `test_load_profile_replaces_checked_set`, `test_profile_loaded_before_comparison_is_not_widened_by_defaults` | VERIFIED |
| 5 | User runs the comparison | Only the profile's attributes show; missing items named (D-06) | `MainWindow._profile_items_not_found_message()`; `tests/gui/test_profile_portability.py` (13 tests) | VERIFIED |
| 6 | User renames or deletes a profile via "Manage" | Rename keeps attributes, refuses collisions; Delete asks first | `ProfileRepository.rename`/`.delete`; `tests/gui/test_profile_manage.py` (15 tests, rescoped for the two-row layout) | VERIFIED |
| 7 | User widens/narrows the Attributes panel (G-03-1) | Profiles dropdown, "Save…" and "Manage" never clip at the 260px default or the 240px drag floor, in either theme | `test_profile_toolbar_widgets_never_clipped` (parametrized, light/dark); measures `widget.width() >= widget.sizeHint().width()` at both widths | VERIFIED (mechanism); real native rendering routed to human verification below |
| 8 | User runs a comparison and looks at "Compare with" (G-03-2, new scope) | Each file shows a green/red/gray dot reflecting only the checked attributes' match status; resets to gray on any file-list/target/attribute change, and on any re-run or failed re-run (WR-01) | `_update_match_indicators`/`_reset_match_indicators`/`_mark_all_compare_items_unknown`; 12 tests in `tests/gui/test_compare_list_match_indicator.py` including the two WR-01 regression tests | VERIFIED (mechanism); real dot-color rendering routed to human verification below |

## Goal Achievement — Observable Truths

Must-haves merged from ROADMAP Success Criterion 1 and the `must_haves` blocks of all four PLAN frontmatters (03-01 through 03-04), plus the WR-01 code-review fix explicitly named in this verification's task brief. 29 truths/prohibitions carried forward from the prior 03-01/02/03 verification (re-checked, not re-derived — see "Regression check" below) plus 8 new truths/prohibitions from 03-04, plus 1 explicit WR-01 fix-presence check.

### Carried forward from 03-01/02/03 (regression-checked)

All 29 previously-VERIFIED truths and prohibitions (toolbar/dropdown existence, atomic save, overwrite confirm, name validation, damaged-file handling, path-safety, idempotency, D-06 not-found reporting, rename/delete semantics and safety) were re-checked for regression:

| Check | Result |
|---|---|
| `src/gdtf_comparer/core/profile_repository.py` (535 lines), `core/errors.py` — classes/functions unchanged in shape | ✓ VERIFIED — `class Profile`, `normalize_profile_name`, `profile_name_key`, `app_data_dir`, `class ProfileRepository`, `missing_attributes`; `ProfileError`/`ProfileNameError`/`ProfileNotFoundError`/`ProfileStorageError` all present |
| `tests/core/test_profile_repository.py`, `tests/gui/test_profile_portability.py` | ✓ VERIFIED — all pass in the full-suite run (see Behavioral Spot-Checks) |
| `tests/gui/test_profile_toolbar.py`, `tests/gui/test_profile_manage.py` (rescoped for the two-row layout by 03-04) | ✓ VERIFIED — rescoped assertions (`profile_combo_row.indexOf`, `profile_actions_row.indexOf`) pass; all other assertions (text, menu, popupMode, rename-action membership) unchanged and pass |
| `git diff --quiet HEAD -- src/gdtf_comparer/core/comparator.py src/gdtf_comparer/core/models.py src/gdtf_comparer/gui/table_model.py` since Phase 3 began | ✓ VERIFIED — exits 0; no plan in this phase touched comparison/model/table logic |
| Real-restart (truth #3) and crash-resilience (truth #15) — previously routed to human verification | ✓ VERIFIED (human-confirmed) — 03-UAT.md test 2 ("pass") and the implicit pass of every step but the toolbar in test 1 |

**Score for carried-forward items: 29/29** (the 2 items previously open — real restart and crash resilience — are now resolved by the UAT human judgment, not merely re-asserted).

### New truths from 03-04 (gap closure: G-03-1, G-03-2)

| # | Truth (abbreviated) | Status | Evidence |
|---|---|---|---|
| 1 | Dropdown/Save…/Manage each render ≥ their own sizeHint width at the 260px default AND the 240px drag floor, in both themes (closes G-03-1) | ✓ VERIFIED | `profile_row = QVBoxLayout()` holding `profile_combo_row`/`profile_actions_row` (main_window.py:350-379); `test_profile_toolbar_widgets_never_clipped` passes both widths × both themes (2/2) |
| 2 | Dropdown/Save…/Manage stay in one consolidated block above the picker, now two stacked rows, no label abbreviated/relocated | ✓ VERIFIED | `SAVE_PROFILE_LABEL`/`MANAGE_PROFILES_LABEL` constants unchanged; both rows nested inside the same `profile_row` added once via `attributes_layout.addLayout(self.profile_row)`; `test_profile_toolbar_sits_above_picker_in_attributes_panel`, `test_manage_button_sits_in_profile_row` pass |
| 3 | Colored dot per "Compare with" file after Run Comparison: green if no checked attribute differs, red if ≥1 does (closes G-03-2) | ✓ VERIFIED | `_update_match_indicators` reads `row.differs[row_index]` directly (main_window.py:728-730); `test_match_and_differs_states_after_run` passes |
| 4 | Dot resets to neutral gray before any run, and on target/file-list/attribute changes | ✓ VERIFIED | `_reset_match_indicators()` called from `set_target_file`, `add_compare_files`, `remove_selected_files` (3 call sites, confirmed by grep); `test_adding_a_file_resets_every_indicator_to_unknown`, `test_removing_a_file_resets_the_remaining_indicator_to_unknown`, `test_changing_target_resets_indicators_to_unknown` pass |
| 5 | File with no checked-attribute rows shows neutral gray, never a false green | ✓ VERIFIED | `evaluated` empty → `MATCH_STATE_UNKNOWN` (main_window.py:726); `test_unchecking_the_only_relevant_attribute_falls_back_to_unknown` passes |
| 6 | Tooltip names the state in plain words; computing/display never mutates compare_files/checked set/result | ✓ VERIFIED | `_set_compare_item_match_state` appends `MATCH_STATE_TOOLTIPS[state]`; `test_tooltip_names_the_state`, `test_indicator_never_changes_comparison_or_selection` pass |

### Prohibitions from 03-04

| # | Prohibition | Status | Evidence |
|---|---|---|---|
| 1 | MUST NOT abbreviate/remove profile toolbar labels or relocate Save…/Manage outside the consolidated block | ✓ RESOLVED | `SAVE_PROFILE_LABEL`, `MANAGE_PROFILES_LABEL` unchanged; both buttons still direct children of the same `profile_row` stack |
| 2 | MUST NOT add new comparison/tolerance logic beyond the existing differs signal; MUST NOT mutate compare_files/checked_attributes/ComparisonResult | ✓ RESOLVED | `git diff --quiet HEAD -- src/gdtf_comparer/core` exits 0 for the whole plan (confirmed); `test_indicator_never_changes_comparison_or_selection` passes |

### WR-01 code-review fix (explicitly required by this verification's task brief)

| Check | Result |
|---|---|
| `self._reset_match_indicators()` called from `run_comparison`, right after `self.table_model.set_result(None)` | ✓ VERIFIED — `main_window.py:558-559` |
| `self._reset_match_indicators()` called from `on_comparison_failed`, right after `self.table_model.set_result(None)` | ✓ VERIFIED — `main_window.py:878-879` |
| Regression tests exist and pass by name | ✓ VERIFIED — `test_running_again_resets_stale_indicators_before_new_result`, `test_failed_comparison_resets_stale_indicators_to_unknown` both pass |
| IN-01 and IN-02 (non-blocking Info findings) remain genuinely open, as 03-REVIEW.md claims (not silently fixed, not silently broken) | ✓ VERIFIED — `set_target_file`'s early `if not path: return` (main_window.py:478-479) still precedes the reset at line 497; `_reset_match_indicators` (line 678) is still a one-line wrapper around `_mark_all_compare_items_unknown` |

**Score:** 37/38 — every automated-checkable truth, prohibition, and the WR-01 fix are VERIFIED; 1 item (real native-rendering confirmation of G-03-1/G-03-2, carried forward from 03-04-PLAN.md's own deferred human-check) is routed to human verification, not FAILED — the underlying mechanism is present, wired, and exercised by passing automated tests.

## Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `src/gdtf_comparer/core/profile_repository.py` | Profile, ProfileRepository, normalize_profile_name, profile_name_key, app_data_dir, missing_attributes, rename, delete | ✓ VERIFIED | 535 lines; unchanged by 03-04 (core/ untouched) |
| `src/gdtf_comparer/core/errors.py` | ProfileError, ProfileNameError, ProfileNotFoundError, ProfileStorageError | ✓ VERIFIED | Present, unchanged |
| `src/gdtf_comparer/gui/main_window.py` | Two-row profile toolbar; match-indicator state machine | ✓ VERIFIED | 1187 lines; `profile_combo_row`/`profile_actions_row`, `ATTRIBUTES_PANEL_MIN_WIDTH_PX = 240`, `COMPARE_MATCH_STATE_ROLE`, `MATCH_STATE_*`, `_match_indicator_icon`, `_set_compare_item_match_state`, `_mark_all_compare_items_unknown`, `_reset_match_indicators`, `_update_match_indicators` all present and wired |
| `tests/gui/test_compare_list_match_indicator.py` | 03-04 G-03-2 tests + WR-01 regressions | ✓ VERIFIED | 12 tests (10 original + 2 WR-01 regression), all pass |
| `tests/gui/test_profile_toolbar.py` | 03-01 tests + G-03-1 no-clip test | ✓ VERIFIED | Rescoped + 1 new parametrized test, all pass |
| `tests/gui/test_profile_manage.py` | 03-03 tests, rescoped | ✓ VERIFIED | Rescoped assertion passes; rest unchanged |
| `tests/gui/test_profile_portability.py`, `tests/core/test_profile_repository.py` | 03-02/03-01 tests, unchanged | ✓ VERIFIED | All pass, no regressions |

## Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `main_window.py add_compare_files/remove_selected_files/set_target_file` | `_reset_match_indicators` | Any change to who/what is compared invalidates the dots | ✓ WIRED | Exactly 3 call sites confirmed by direct read (lines 497, 535, 545) |
| `main_window.py run_comparison/on_comparison_failed` | `_reset_match_indicators` | WR-01 fix: a re-run or failed re-run never leaves a stale dot | ✓ WIRED | Confirmed at lines 559, 879, both directly after `table_model.set_result(None)` |
| `main_window.py _apply_attribute_selection` | `_update_match_indicators` | Every selection change and post-run refresh recomputes the dots | ✓ WIRED | Exactly 1 call site, line 630 |
| `_update_match_indicators` | `core/models.py ComparisonRow.differs` | Dot color read straight off the existing differs tuple | ✓ WIRED | `row.differs[row_index]` at line 728; zero new comparison logic (`git diff` against `core/` empty) |
| `profile_row` (QVBoxLayout) | `profile_combo_row`, `profile_actions_row` | Two-row stack replaces the single clipped row | ✓ WIRED | Both sub-layouts added via `self.profile_row.addLayout(...)`; single `attributes_layout.addLayout(self.profile_row)` |

(All 03-01/02/03 key links from the prior verification — `ProfileRepository` read/write, `set_checked()` wiring, `activated`-only load, atomic `os.replace`, `tests/conftest.py` isolation, `APPROVED_CORE_SURFACE` — were re-checked and remain WIRED; unchanged by this phase's gap closure.)

## Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
|---|---|---|---|---|
| ATTR-03 | 03-01, 03-02, 03-03, 03-04 | User can save/name a subset of selected attributes as a reusable "compare profile" and reload it for future comparisons | ✓ SATISFIED (automated); real-native-rendering confirmation of the G-03-1/G-03-2 fix pending human sign-off | ProfileRepository + Profiles dropdown/Save…/Manage UI + match-indicator feature; 96 profile/toolbar/indicator tests across 5 files, all passing |

No orphaned requirements: REQUIREMENTS.md maps only ATTR-03 to Phase 3, and all four plans (including the gap-closure plan) declare it in frontmatter.

## Anti-Patterns Found

None. Scanned `core/errors.py`, `core/profile_repository.py`, `gui/attribute_picker.py`, `gui/main_window.py` for `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`, "not yet implemented", empty-return stubs, and hardcoded-empty-prop patterns. The only `PLACEHOLDER`-named matches (`PROFILE_PLACEHOLDER`, `NO_PROFILES_PLACEHOLDER`, `PROFILES_UNAVAILABLE_PLACEHOLDER`) are legitimate Qt UI-text constants, not stub code. `src/gdtf_comparer/core/` has zero diff for the entire phase's gap-closure work (confirmed via `git diff --quiet`).

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Full suite (Phase 1-3 regression, run once) | `"$PY" -m pytest -q -W error::DeprecationWarning` | `258 passed in 13.21s` | ✓ PASS |
| G-03-1 no-clip test, both themes/widths | `pytest tests/gui/test_profile_toolbar.py::test_profile_toolbar_widgets_never_clipped -v` | `2 passed` (light_blue.xml, dark_blue.xml) | ✓ PASS |
| G-03-2 + WR-01 match-indicator suite | `pytest tests/gui/test_compare_list_match_indicator.py tests/gui/test_profile_toolbar.py tests/gui/test_profile_manage.py -q` | `44 passed` | ✓ PASS (one earlier run hit a native-teardown crash with no Python traceback and no assertion failure, consistent with the flake 03-04-SUMMARY.md documented; an immediate re-run passed cleanly with no recurrence) |
| WR-01 fix present in code | Direct read of `main_window.py:547-579` (`run_comparison`) and `:872-881` (`on_comparison_failed`) | `self._reset_match_indicators()` present at both sites, immediately after `set_result(None)` | ✓ PASS |

The full suite was run exactly once for the regression count; the two targeted sub-runs above are by-name, not re-filters of the full run.

## Human Verification Required

### 1. Real-app confirmation of the G-03-1 layout fix and G-03-2 match-indicator feature

**Test:** Carried forward verbatim from 03-04-PLAN.md's own Task 2 `<human-check>` (explicitly deferred to `/gsd-verify-work`, and not yet re-exercised — `03-UAT.md`'s git history shows no commit after the gap-closure plan landed). Pick a target GDTF file, add two comparison files (one expected close to the target, one expected different). Look at "Compare with" before clicking anything. Click Run Comparison, look again, hover each file. In the Attributes panel, look at the dropdown/Save…/Manage row; drag the panel divider as far left as it goes, then back. Untick every checked attribute and look at "Compare with" again. Add one more comparison file and look again.

**Expected:** Gray dots before any run; green/red dots with explanatory tooltips after Run Comparison; the dropdown, "Save…" and "Manage" fully readable at every width down to the drag floor — none of "AVE.", "M...e", "No si▾"; all dots turn gray again when nothing is checked, and again when a new file is added.

**Why human:** Every automated test (including the new clipping test and the match-indicator suite, all passing) runs on the offscreen Qt platform. This proves the layout math and the state machine are correct, but cannot prove how qt-material's real chrome, real font metrics, and real screen DPI render the fix on an actual display — exactly the gap 03-04-PLAN.md's own human-check names.

## Gaps Summary

No gaps_found-level blockers. Every artifact exists and is substantive; every key link (including the two new WR-01 call sites) is wired and confirmed by direct code reading; the full regression suite (258 tests, up from 244 before this gap-closure round) passes cleanly in one run; no debt markers or stub patterns were found; `src/gdtf_comparer/core/` has zero diff across the entire phase's gap-closure work, satisfying both of 03-04's prohibitions; REQUIREMENTS.md's only Phase-3 requirement (ATTR-03) is claimed and substantively supported by all four plans; the two human-verification items left open by the prior round (real restart, crash resilience) are now resolved by the user's own UAT session.

The phase is **not** cleared to `passed` because one item genuinely cannot be certified from the codebase alone: real native-OS rendering confirmation of the G-03-1 fix and the G-03-2 feature, which 03-04-PLAN.md itself explicitly deferred to this verification step and which has not yet been performed (no UAT update since the fix landed). The underlying mechanism for both — layout math and match-state logic — is present, wired, and exercised by 56 new/rescoped passing automated tests across the two gap-closure tasks; the gap is in confirming the *real* rendering, not the implementation.

---

*Verified: 2026-10-05T12:00:00Z*
*Verifier: Claude (gsd-verifier)*
