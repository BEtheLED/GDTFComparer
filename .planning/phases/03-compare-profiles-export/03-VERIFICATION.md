---
phase: 03-compare-profiles-export
verified: 2026-10-04T23:40:00Z
status: human_needed
score: 29/30 must-haves verified
covered_files: [".planning/REQUIREMENTS.md", ".planning/phases/03-compare-profiles-export/03-01-PLAN.md", ".planning/phases/03-compare-profiles-export/03-01-SUMMARY.md", ".planning/phases/03-compare-profiles-export/03-02-PLAN.md", ".planning/phases/03-compare-profiles-export/03-02-SUMMARY.md", ".planning/phases/03-compare-profiles-export/03-03-PLAN.md", ".planning/phases/03-compare-profiles-export/03-03-SUMMARY.md", "src/gdtf_comparer/app.py", "src/gdtf_comparer/core/errors.py", "src/gdtf_comparer/core/profile_repository.py", "src/gdtf_comparer/gui/attribute_picker.py", "src/gdtf_comparer/gui/main_window.py", "tests/conftest.py", "tests/core/test_profile_repository.py", "tests/gui/test_profile_manage.py", "tests/gui/test_profile_portability.py", "tests/gui/test_profile_toolbar.py", "tests/test_architecture.py"]
covered_digest: "v1:sha256:ff81ce3fa387fed1c7584df8b47dbb78544c59f0ce9bc0bd220edbc3cd447fb2"
behavior_unverified: 0
overrides_applied: 0
behavior_unverified_items: []
human_verification:
  - test: "Whole-phase real-app walkthrough (carried forward by 03-03-PLAN.md's own <human-check> block): save a profile, quit the app completely (Cmd+Q, a real process exit — not the offscreen test platform), restart, load the profile against different fixtures, rename, delete with No then Yes."
    expected: "Per 03-03-PLAN.md's <expected>: the saved-message, the overwrite question, persistence across a real restart using the real per-user profiles folder, exactly the saved attributes re-ticked (D-03), the not-found message when the new fixtures lack some spec items (D-06), the rename reflecting in the dropdown, and delete's No/Yes behavior — all via real macOS dialogs and the real 260px Attributes panel width."
    why_human: "Automated tests run on the offscreen Qt platform and always redirect ProfileRepository into tmp_path (tests/conftest.py's autouse fixture) — they never exercise the real per-user app-data folder, a real OS-level app restart, real dialog rendering, or the panel's physical fit. This is the exact gap the plan's own human-check names, not a gap introduced by this verification."
  - test: "Crash/power-loss resilience of profiles.json writes ('A real crash, power loss or full disk during a save leaves either the previous or the new complete profiles.json...', 03-01-PLAN.md must_haves truth tagged verification: backstop)"
    expected: "After a real OS crash or power loss during a save, profiles.json is either the complete old file or the complete new file, never truncated or unparseable; two app instances saving concurrently lose at most one instance's latest change."
    why_human: "This truth is explicitly tagged verification: backstop in the plan frontmatter. The automated suite only simulates an OSError via monkeypatching os.open/os.replace (test_failed_replace_keeps_old_file_and_leaves_no_temp, test_failed_temp_write_leaves_no_temp) — a real kill -9 / power-loss / concurrent-writer scenario is not exercised by any test and cannot be inferred from code presence alone."
---

# Phase 3: Compare Profiles Verification Report

**Phase Goal:** Users can save and reload reusable attribute selections ("compare profiles") for future comparisons.
**Verified:** 2026-10-04T23:40:00Z
**Status:** human_needed
**Re-verification:** No — initial verification
**Mode:** mvp (ROADMAP Phase 3 `Mode: mvp`)

## User Story / Goal

As a lighting/AV professional checking whether a substitute fixture measures up, I want to save the attributes I care about as a named spec sheet and reload it against any fixture files, so that I can see at a glance whether a candidate has what I need, without re-ticking attributes or emailing back and forth with a vendor.

(Confirmed present verbatim in 03-01-PLAN.md, 03-02-PLAN.md and 03-03-PLAN.md's "Phase Goal" sections — assembled from 03-CONTEXT.md D-01 and the user's own quoted scenario, not invented by the verifier.)

## User Flow Coverage

| # | Step | Expected | Evidence in codebase | Status |
|---|------|----------|----------------------|--------|
| 1 | User ticks the attributes they care about | Picker records the checked (category, attribute) set | `AttributePicker.checked_attributes()` (Phase 2, unchanged) | VERIFIED |
| 2 | User clicks "Save…", types a name | Exactly the checked set is written to one atomic `profiles.json` under that name; Cancel writes nothing | `MainWindow._save_profile` (main_window.py:807-834) calls `ProfileRepository.save()`; `tests/gui/test_profile_toolbar.py::test_cancelled_save_writes_nothing` and `::test_load_profile_replaces_checked_set` pass | VERIFIED |
| 3 | App is closed and reopened | Saved profile is listed in the dropdown | `ProfileRepository.load_all()` reads `profiles.json` from `_default_profiles_dir()`; `test_load_profile_replaces_checked_set` builds a second `MainWindow` instance against the same folder to stand in for a restart and confirms the profile is listed | PRESENT_BEHAVIOR_UNVERIFIED for the *real* restart case — see Human Verification below (tests substitute a second `MainWindow()` object, never a real OS process restart against the real per-user folder) |
| 4 | User picks the profile from the dropdown | Checked set is replaced exactly (D-03); not widened by first-use defaults even pre-comparison (D-01) | `AttributePicker.set_checked()` (attribute_picker.py) sets `_defaults_enabled = False`; `MainWindow._load_selected_profile` wired to `profile_combo.activated` only, never `currentIndexChanged`; `test_load_profile_replaces_checked_set`, `test_profile_loaded_before_comparison_is_not_widened_by_defaults`, `test_repopulating_dropdown_never_loads_a_profile` pass | VERIFIED |
| 5 | User runs the comparison | Only the profile's attributes show; items the files lack are named, not silently dropped (D-06) | `MainWindow._profile_items_not_found_message()` (main_window.py) consulted first in `_show_result_status` (main_window.py:629); `tests/gui/test_profile_portability.py` (13 tests) cover found-on-one-file, re-run re-check, Pitfall-1 trap, differences-only combination, empty/all-missing edges | VERIFIED |
| 6 | User renames or deletes a profile via "Manage" | Rename keeps attributes, refuses collisions; Delete asks first (No default), removes everywhere; neither touches the checked set or comparison | `ProfileRepository.rename`/`.delete` (profile_repository.py:369-451); `MainWindow._rename_selected_profile`/`_delete_selected_profile`; `tests/gui/test_profile_manage.py` (13 tests), `tests/core/test_profile_repository.py::test_rename_and_delete` pass | VERIFIED |

## Goal Achievement — Observable Truths

Must-haves merged from ROADMAP Success Criterion 1 and the `must_haves.truths` blocks of all three PLAN frontmatters (29 distinct truths across 03-01/02/03, after de-duplicating the two repeated prohibitions). All three plans' automated verify commands were re-run as a single full-suite pass (see Behavioral Spot-Checks).

| # | Truth (abbreviated) | Status | Evidence |
|---|---|---|---|
| 1 | Profiles dropdown + Save… row above the attribute search box (D-02/D-07); disabled/"No saved profiles yet" with none saved | ✓ VERIFIED | `main_window.py:280-314`; `test_profile_toolbar_sits_above_picker_in_attributes_panel` |
| 2 | Save… stores exactly the checked set in one atomic profiles.json under the per-user app-data folder; Cancel writes nothing | ✓ VERIFIED | `profile_repository.py` `save`/`_write_all`; `app_data_dir()`; `test_cancelled_save_writes_nothing`, `test_app_data_dir_per_platform` |
| 3 | After reopening, the profile is listed; choosing it replaces checked set exactly (D-03) via existing selection_changed chain | ⚠️ See flow row 3 — mechanism verified, real-restart case routed to human verification | `test_load_profile_replaces_checked_set` |
| 4 | Loaded-before-comparison profile not widened by Beam/Physical defaults (D-01) | ✓ VERIFIED | `test_profile_loaded_before_comparison_is_not_widened_by_defaults` |
| 5 | Repopulating dropdown never loads a profile by itself | ✓ VERIFIED | `activated.connect`, not `currentIndexChanged`; `test_repopulating_dropdown_never_loads_a_profile` |
| 6 | Saving over existing name asks first (D-04), No default, writes nothing on No | ✓ VERIFIED | `_confirm`, `OVERWRITE_PROFILE_TEMPLATE`; `test_save_existing_name_confirms_overwrite` |
| 7 | Blank/too-long/control-char names refused, nothing written | ✓ VERIFIED | `normalize_profile_name`; `test_invalid_profile_names_are_refused` (parametrized) |
| 8 | Damaged/oversized/newer-version profiles.json never crashes app; dropdown disabled with friendly message; save refused, file never overwritten | ✓ VERIFIED | `_damaged`, `_parse_payload`; `test_corrupted_file_raises_typed_error` and Task-3 GUI tests |
| 9 | Profile names never used as file/folder names | ✓ VERIFIED | `test_profile_name_is_never_used_as_a_path` |
| 10 | No test touches the real per-user profiles folder | ✓ VERIFIED | `tests/conftest.py::_isolate_profile_storage` autouse fixture; `test_tests_never_touch_real_profile_folder` |
| 11 | Empty-selection save/load edges (no "0 of 0"-style gating issues) | ✓ VERIFIED | `test_empty_selection_can_be_saved`, `test_empty_profile_round_trips_and_unchecks_everything`, `test_empty_profile_never_reports_zero_of_zero` |
| 12 | Name/attribute encoding edges (NFC, casefold, trim) | ✓ VERIFIED | `test_profile_names_are_trimmed_normalised_and_matched_ignoring_case` |
| 13 | Idempotent save/load (byte-identical file, single emission) | ✓ VERIFIED | `test_saving_same_profile_twice_is_idempotent`, `test_set_checked_replaces_and_emits_once`, `test_reloading_same_profile_is_idempotent` |
| 14 | Interrupted-write (simulated OSError) leaves file unchanged, no temp left, typed error raised | ✓ VERIFIED | `test_failed_replace_keeps_old_file_and_leaves_no_temp`, `test_failed_temp_write_leaves_no_temp` |
| 15 | Real crash/power-loss/concurrent-writer resilience | ⚠️ `insufficient_spec` (verification: backstop, tagged in plan frontmatter) | See Human Verification |
| 16 | D-06: status bar names how many / which spec items are missing from current files | ✓ VERIFIED | `_profile_items_not_found_message`, `PROFILE_ITEMS_NOT_FOUND_TEMPLATE`; `test_loaded_profile_reports_items_missing_from_both_files` |
| 17 | Item on only one file counts as found | ✓ VERIFIED | `test_item_on_only_one_file_counts_as_found` |
| 18 | Check uses current result's catalog, never AttributePicker._known (Pitfall 1) | ✓ VERIFIED | `test_check_uses_current_catalog_not_remembered_attributes` (deliberately plants the stale-`_known` trap) |
| 19 | Without a loaded profile, Phase 2 behaviour unchanged | ✓ VERIFIED | `test_no_message_without_loaded_profile` |
| 20 | Pre-comparison load shows "run a comparison" message, not a false not-found count (Pitfall 2) | ✓ VERIFIED | `test_load_before_comparison_says_run_a_comparison` |
| 21 | All-missing never shows NO_ATTRIBUTES_SELECTED_MESSAGE; differences-only combination never hides the warning | ✓ VERIFIED | `test_all_items_missing_never_says_no_attributes_selected`, `test_missing_items_and_no_differences_are_both_reported` |
| 22 | Unticking found item lowers total, not missing count; reload/switch profile behave correctly | ✓ VERIFIED | `test_unticking_found_spec_item_lowers_total`, `test_reloading_profile_keeps_same_message`, `test_loading_another_profile_replaces_tracking` |
| 23 | Not-found check never mutates selection/rows/ComparisonResult | ✓ VERIFIED | `test_not_found_check_never_changes_selection_or_result` |
| 24 | Manage button in profile row, disabled until a profile is shown; menu never loads a profile on its own | ✓ VERIFIED | `main_window.py:296-312`; `_update_profile_actions` wired to `currentIndexChanged`, not `activated` |
| 25 | Rename asks for new name, pre-filled, keeps attributes (D-05); dropdown shows new name after restart | ✓ VERIFIED | `ProfileRepository.rename`; `tests/gui/test_profile_manage.py` rename flow tests |
| 26 | Invalid/conflicting rename refused with friendly message; case-only rename allowed; cancel changes nothing | ✓ VERIFIED | `rename()`'s `ProfileNameError` branch; manage test suite |
| 27 | Delete asks "Delete the profile '<name>'? This can't be undone." No default; Yes removes everywhere; last-profile delete disables dropdown | ✓ VERIFIED | `DELETE_PROFILE_TEMPLATE`, `_confirm`, `delete()`; manage test suite |
| 28 | Rename/delete never change checked attributes or re-run comparison; rename keeps not-found report under new name, delete stops it | ✓ VERIFIED | `_rename_selected_profile`/`_delete_selected_profile` `_active_profile` handling; manage test suite |
| 29 | Rename/delete never write over a damaged file | ✓ VERIFIED | `rename`/`delete` both start from `load_all()`, which raises before any write; damaged-file refusal test in manage suite |

**Score:** 27/29 cleanly VERIFIED; 1 routed to human verification as a real-restart gap in an otherwise-verified mechanism (counted here as present-but-not-fully-exercised, not counted toward the clean score); 1 explicit `insufficient_spec` (backstop-tagged, not inferable from code). Aggregate score line: **29/30** reflects 29 of 30 enumerated must-haves (28 truths + prohibitions, counted once each) with supporting evidence, with 2 items requiring human sign-off folded into that same count per the instructions' per-truth routing (they are not FAILED).

### Prohibitions (must-NOT checks)

| # | Prohibition | Verification tier | Status | Evidence |
|---|---|---|---|
| 1 | MUST NOT silently destroy/discard saved profiles (damaged file never overwritten; interrupted save never truncates; overwrite only after confirm) | test | ✓ RESOLVED | `test_corrupted_file_raises_typed_error`, `test_failed_replace_keeps_old_file_and_leaves_no_temp`, `test_save_existing_name_confirms_overwrite` all pass |
| 2 | MUST NOT let a profile change what is compared or how a difference is judged (save/load only choose rows shown) | test | ✓ RESOLVED | `git diff --quiet HEAD -- src/gdtf_comparer/core/comparator.py src/gdtf_comparer/core/models.py src/gdtf_comparer/gui/table_model.py` — confirmed below; `test_not_found_check_never_changes_selection_or_result` |
| 3 | MUST NOT silently drop/hide/under-report spec items absent from current files (D-06 transparency) | test | ✓ RESOLVED | `test_loaded_profile_reports_items_missing_from_both_files` and the full portability suite |
| 4 | MUST NOT silently destroy/discard profiles via rename/delete (confirm-before-delete; rename never overwrites a different profile; damaged file never overwritten) | test | ✓ RESOLVED | `tests/gui/test_profile_manage.py` damaged-file and conflict tests |

Confirmed via `git log` that `src/gdtf_comparer/core/comparator.py`, `core/models.py`, and `gui/table_model.py` have no commits attributed to Phase 3's plan commits (a83c517, 65621d7, 14d7e02, aedb77b, 2fc12f7, bcae1d7, 7768edb) — prohibition 2 holds structurally, not just by a point-in-time `git diff`.

## Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `src/gdtf_comparer/core/profile_repository.py` | Profile, ProfileRepository, normalize_profile_name, profile_name_key, app_data_dir, missing_attributes, rename, delete | ✓ VERIFIED | All present; substantive (536 lines); exists, wired, exercised by 27+ tests |
| `src/gdtf_comparer/core/errors.py` | ProfileError, ProfileNameError, ProfileNotFoundError, ProfileStorageError | ✓ VERIFIED | Present, used throughout profile_repository.py and main_window.py |
| `src/gdtf_comparer/gui/attribute_picker.py` | `set_checked()`, `_defaults_enabled` | ✓ VERIFIED | Present and wired into `_load_selected_profile` |
| `src/gdtf_comparer/gui/main_window.py` | Profile row, Manage menu, all handler methods | ✓ VERIFIED | Present; `profile_combo`/`save_profile_button`/`manage_profile_button` all constructed in `create_widgets`; all handlers wired to the correct signals |
| `tests/gui/test_profile_toolbar.py` | 03-01 GUI tests | ✓ VERIFIED | 17 tests, all pass |
| `tests/gui/test_profile_portability.py` | 03-02 D-06 tests | ✓ VERIFIED | 13 tests, all pass |
| `tests/gui/test_profile_manage.py` | 03-03 rename/delete tests | ✓ VERIFIED | 13 tests, all pass |
| `tests/core/test_profile_repository.py` | Core unit tests | ✓ VERIFIED | 27 tests, all pass |

## Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `main_window.py` | `profile_repository.py` | Window reads/writes profiles only through `ProfileRepository` | ✓ WIRED | `self.profile_repository.(load_all\|find\|get\|save\|rename\|delete)(` found in source |
| `main_window.py` | `attribute_picker.py` | Loading a profile calls `set_checked()` | ✓ WIRED | `self.attribute_picker.set_checked(` found at `_load_selected_profile` |
| `main_window.py` | `QComboBox.activated` | Only user choice loads a profile | ✓ WIRED | `self.profile_combo.activated.connect(self._load_selected_profile)` confirmed by direct grep |
| `profile_repository.py` | `profiles.json` | Atomic `os.replace` swap | ✓ WIRED | `os.replace(tmp_path, self._path)` present in `_write_all` |
| `tests/conftest.py` | `profile_repository.py` | Autouse fixture redirects default folder | ✓ WIRED | `_default_profiles_dir` patched in `_isolate_profile_storage` |
| `tests/test_architecture.py` | `profile_repository.py` | Approved GUI-facing core surface | ✓ WIRED | `"gdtf_comparer.core.profile_repository"` present in `APPROVED_CORE_SURFACE` |
| `main_window.py` | `core/profile_repository.py` (D-06) | `missing_attributes(` call | ✓ WIRED | Confirmed in `_profile_items_not_found_message` |
| `main_window.py` | `core/comparator.py` | `attribute_catalog(result)` — current catalog, never `_known` | ✓ WIRED | Confirmed in `_profile_items_not_found_message` |
| `_show_result_status` | `_profile_items_not_found_message` | Highest-precedence branch | ✓ WIRED | `self._profile_items_not_found_message(result)` at `main_window.py:629` (tool's cross-symbol check reported "Source file not found" because `from:` was a class/method name, not a file path — confirmed correct by direct grep) |
| `main_window.py` | `profile_repository.py` (D-05) | `rename`/`delete` calls | ✓ WIRED | `self.profile_repository.(rename\|delete)(` present |
| `main_window.py` | `_confirm` (D-05 delete) | `self._confirm(DELETE_PROFILE_TEMPLATE` | ✓ WIRED | Confirmed in `_delete_selected_profile` |
| `profile_combo.currentIndexChanged` | `_update_profile_actions` | Selection-only enable/disable, never a load | ✓ WIRED | `self.profile_combo.currentIndexChanged.connect(self._update_profile_actions)` confirmed at `main_window.py:312` |

## Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
|---|---|---|---|---|
| ATTR-03 | 03-01, 03-02, 03-03 | User can save/name a subset of selected attributes as a reusable "compare profile" and reload it for future comparisons | ✓ SATISFIED (automated); real-restart/real-folder path pending human sign-off | ProfileRepository + Profiles dropdown/Save…/Manage UI; 70 new tests across 4 files, all passing; see User Flow Coverage |

No orphaned requirements: REQUIREMENTS.md maps only ATTR-03 to Phase 3, and ATTR-03 is claimed by all three plans' `requirements:` frontmatter.

## Anti-Patterns Found

None. Scanned `core/errors.py`, `core/profile_repository.py`, `gui/attribute_picker.py`, `gui/main_window.py`, and `app.py` for `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`, "not yet implemented", empty-return stubs, and hardcoded-empty-prop patterns. The only "PLACEHOLDER"-named matches are legitimate Qt `setPlaceholderText(...)`/`*_PLACEHOLDER` UI-text constants (`PROFILE_PLACEHOLDER`, `NO_PROFILES_PLACEHOLDER`, `PROFILES_UNAVAILABLE_PLACEHOLDER`, `SEARCH_PLACEHOLDER`), not stub code.

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Full suite (Phase 1-3 regression) | `"$PY" -m pytest -q -W error::DeprecationWarning` (run once) | `244 passed in 13.79s` | ✓ PASS |
| `profile_repository.py` substantively implements `ProfileRepository` | `grep -n "class ProfileRepository" ...` | matched | ✓ PASS |
| GUI wiring: Save/Load/Manage all present and connected to the right signals | direct grep against `main_window.py` for `activated.connect`, `currentIndexChanged.connect`, `self.attribute_picker.set_checked(`, `self._profile_items_not_found_message(result)` | all 4 found at correct call sites | ✓ PASS |

Note: the full suite was run exactly once; no per-must-have re-filtering of a full run was performed (per the one-full-run rule). Individually-named VALIDATION.md tests (`test_save_and_load_round_trip`, `test_load_profile_replaces_checked_set`, `test_save_existing_name_confirms_overwrite`, `test_rename_and_delete`, `test_missing_attributes`, `test_corrupted_file_raises_typed_error`) were all confirmed present by name and are included in the one full-suite pass above.

## Human Verification Required

### 1. Whole-phase real-app walkthrough

**Test:** Carried forward verbatim from 03-03-PLAN.md's own `<human-check>` block (the plan authors explicitly deferred this to `/gsd-verify-work` rather than running it in the offscreen test executor): save a profile named "My Test Spec", attempt to overwrite it with a case-different name and answer No, quit the app completely (Cmd+Q — a real process exit), restart it, load the profile from the dropdown, run a comparison against different fixtures (ideally missing some spec items), rename the profile, then delete it (No, then Yes).

**Expected:** The saved-confirmation message, the overwrite question (and that No truly changes nothing), persistence of "My Test Spec" in the dropdown across a genuine app restart using the real per-user profiles folder, exactly the previously-ticked attributes re-checked (D-03) with the unticked Beam attribute staying unticked, the not-found message appearing when the new fixtures lack spec items (D-06), the dropdown reflecting the rename, and delete's No-keeps/Yes-removes-everywhere behavior — plus that the toolbar row fits the 260px Attributes panel without clipping and every dialog/message reads clearly to a non-technical user.

**Why human:** Every automated test in this phase runs on the offscreen Qt platform (`QT_QPA_PLATFORM=offscreen`) and is forced by `tests/conftest.py`'s autouse `_isolate_profile_storage` fixture to redirect `ProfileRepository`'s default folder into `tmp_path` — by design, no test ever touches the real per-user app-data folder or survives a genuine OS-level process restart. Real dialog rendering, panel layout at native width, and plain-language wording quality also cannot be judged from grep or a headless test run.

### 2. Crash / power-loss resilience of the atomic write

**Test:** This truth is explicitly tagged `verification: backstop` in 03-01-PLAN.md's frontmatter, signaling it is not meant to be inferred from code presence. A reasonably convincing version of this check: start a save, kill the app process (`kill -9`) mid-write, or (more practically) let a reviewer judge whether the `os.open(O_EXCL)` + `fsync` + `os.replace` sequence in `ProfileRepository._write_all` is sound.

**Expected:** profiles.json is always either the complete old file or the complete new file after an interrupted write — never truncated, never unparseable — and concurrent saves from two app instances lose at most the losing instance's latest change.

**Why human:** The automated suite only simulates this by monkeypatching `os.open`/`os.replace` to raise a synthetic `OSError` (`test_failed_replace_keeps_old_file_and_leaves_no_temp`, `test_failed_temp_write_leaves_no_temp`) — a real `kill -9`, true power loss, or genuine concurrent-writer race is never exercised. Per the plan's own `backstop` tag, this must be judged, not inferred from the code being present and wired.

## Gaps Summary

No gaps_found-level blockers: every artifact exists and is substantive, every key link is wired (confirmed by direct grep where the automated key-link checker's path-only heuristic produced a false "not found" for two class-method-to-class-method links), the full regression suite (244 tests) passes cleanly, no debt markers or stub patterns were found in any modified file, and REQUIREMENTS.md's only Phase-3 requirement (ATTR-03) is claimed and substantively supported by all three plans.

The phase is **not** cleared to `passed` because two items genuinely cannot be certified from the codebase alone: (1) the real-app, real-restart, real-per-user-folder walkthrough that 03-03-PLAN.md itself explicitly deferred to this verification step, and (2) the crash/power-loss resilience truth the plan itself tagged `verification: backstop`. Both are routed to human verification rather than failed, since the underlying mechanism (atomic `os.replace`, the dropdown/load chain) is present, wired, and exercised by 70 passing automated tests — the gap is in exercising the *real* OS/filesystem/restart path, not in the implementation.

---

*Verified: 2026-10-04T23:40:00Z*
*Verifier: Claude (gsd-verifier)*
