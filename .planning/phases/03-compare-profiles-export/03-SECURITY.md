---
phase: "03"
slug: "compare-profiles-export"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-11"
---

# Phase 03 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|----------------|
| Local disk (`profiles.json`) → `ProfileRepository.load_all` | File may be damaged, hand-edited, truncated, huge, or from a newer app version | Untrusted stored profile data |
| User keyboard → `QInputDialog` profile name → core | Free text from the local user | Profile name string |
| `ProfileRepository._write_all` → filesystem | Crash, full disk, or permission error can interrupt any write | Profile data write |
| Saved profile / `ComparisonResult` → not-found report | Profile and attribute names reach the status bar text | Display text |
| `GDTF description.xml` (already validated/size-capped, RELI-02) → `ComparisonRow.differs` → match-indicator color/tooltip | No new untrusted path — same Phase-2 `differs` flags read a second time | Display state (color/tooltip) |
| User keyboard → rename prompt → core | Free-text new name, validated by `normalize_profile_name` | Profile name string |
| `GDTF description.xml` → `FixtureModel.attributes` → cross-file view → `ComparisonRow` (Plan 03-05) | Manufacturer-chosen geometry/model names no longer decide row identity; Beam rows become code-generated "Beam N" labels | Cross-file comparison display |
| `ComparisonRow.differs` → match dots/diff highlighting → user's go/no-go sourcing decision | Alignment correctness now what the go/no-go signal depends on | Decision-relevant display state |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-03-01 | DoS / Tampering | `ProfileRepository.load_all` on damaged/odd-shaped/non-UTF-8/oversized/newer-version `profiles.json` | medium | mitigate | Size-capped read, typed `ProfileStorageError` on every failure mode, caught at startup (combo disabled, status message, no crash). Tests: `test_corrupted_file_raises_typed_error`, `test_wrong_shape_files_raise_typed_error`, `test_newer_version_file_raises_typed_error`, `test_non_utf8_and_oversized_files_raise_typed_error`, `test_damaged_profiles_file_at_startup_disables_dropdown_without_crash` | closed |
| T-03-02 | Tampering (integrity) | `_write_all` interrupted mid-write | medium | mitigate | Same-folder temp file, O_CREAT/O_EXCL, flush+fsync, then `os.replace`; temp removed on failure. Tests: `test_failed_replace_keeps_old_file_and_leaves_no_temp`, `test_failed_temp_write_leaves_no_temp` | closed |
| T-03-03 | Tampering | Path traversal via profile name | low | mitigate | Name is only a JSON value; temp filename is random hex. Test: `test_profile_name_is_never_used_as_a_path` | closed |
| T-03-04 | Spoofing | Profile name rendered as rich text in a dialog | low | mitigate | `Qt.TextFormat.PlainText` on confirm/error dialogs. Tests: `test_confirm_dialog_is_plain_text_and_defaults_to_no`, `test_invalid_name_shows_friendly_error_and_writes_nothing` | closed |
| T-03-05 | Information Disclosure | `profiles.json` readable by other local users | low | mitigate | Folder `0o700`, file `0o600` on POSIX. Test: `test_profiles_file_is_owner_only` | closed |
| T-03-06 | Tampering / data loss | Save after damaged/newer file silently replaces all profiles | medium | mitigate | `save()` starts from `load_all()`, which raises before any write. Tests: `test_damaged_file_is_never_overwritten_by_save`, `test_save_with_damaged_file_shows_error_and_keeps_file` | closed |
| T-03-07 | Tampering / data loss | Saving under an existing name silently overwrites | medium | mitigate | Case/space/Unicode-insensitive lookup, confirm defaults to No. Test: `test_save_existing_name_confirms_overwrite` | closed |
| T-03-08 | Tampering | Two app instances saving at once | low | accept | Single-user desktop app; whole-file last-writer-wins, never corrupt (backstop truth) | accepted |
| T-03-SC | Tampering (supply chain) | New package installs | low | mitigate | No package installed this phase; hand-rolled per-OS folder logic | closed |
| T-03-09 | Repudiation / transparency | Missing spec items silently dropped from go/no-go check | medium | mitigate | Highest-precedence not-found branch, recomputed every selection change/re-run. Tests: `test_loaded_profile_reports_items_missing_from_both_files`, `test_rerun_against_other_files_rechecks_profile`, `test_check_uses_current_catalog_not_remembered_attributes` | closed |
| T-03-10 | Repudiation / transparency | Misleading status hides coverage gap | medium | mitigate | Not-found text replaces/combines with other status messages. Tests: `test_all_items_missing_never_says_no_attributes_selected`, `test_missing_items_and_no_differences_are_both_reported` | closed |
| T-03-11 | Tampering (integrity) | Report mutating selection/rows/result | low | mitigate | Read-only method. Test: `test_not_found_check_never_changes_selection_or_result` | closed |
| T-03-12 | Denial of Service | Recomputing `attribute_catalog` on each status update | low | accept | Linear in result rows, same cadence as existing proxy refilter | accepted |
| T-03-13 | Spoofing | Profile/attribute names in status bar as markup | low | accept | `QStatusBar` draws plain text; dialogs are PlainText | accepted |
| T-03-14 | Tampering / data loss | Delete without confirmation | medium | mitigate | `_confirm` with No default + escape. Tests: `test_delete_asks_first_and_no_keeps_profile`, `test_delete_yes_removes_from_dropdown_and_disk_and_keeps_selection` | closed |
| T-03-15 | Tampering / data loss | Rename onto another profile's name overwrites it | medium | mitigate | `rename` raises `ProfileNameError` on conflict. Tests: `test_rename_to_another_profiles_name_is_refused`, `test_rename_conflict_shows_error_and_changes_nothing` | closed |
| T-03-16 | Tampering / data loss | Rename/delete writing over damaged/newer file | medium | mitigate | Both start from `load_all()`, raises before write. Tests: `test_rename_refuses_damaged_file`, `test_delete_refuses_damaged_file`, `test_delete_with_damaged_file_shows_error_and_keeps_file` | closed |
| T-03-17 | Spoofing | Profile names as rich text in rename/delete dialogs | low | mitigate | PlainText / plain label and line-edit | closed |
| T-03-18 | Repudiation / transparency | Not-found report keeps naming a deleted profile | low | mitigate | `_active_profile` cleared on delete, updated on rename. Tests: `test_deleting_loaded_profile_stops_not_found_report`, `test_renaming_loaded_profile_keeps_not_found_report_under_new_name` | closed |
| T-03-19 | Spoofing / Tampering | Tooltip appends static per-state sentence to existing path tooltip | low | accept | No new untrusted content; fixed code-defined strings only (same exposure as prior T-01-33) | accepted |
| T-03-20 | Denial of Service | Recomputing match state on each selection change/re-run | low | accept | Linear, same cadence as existing proxy refilter, bounded by RELI-02 size cap | accepted |
| T-03-21 | Repudiation / transparency | Stale/mismapped dot could mislead go/no-go decision | medium | mitigate | Defensive count-and-path check resets to unknown on disagreement, plus explicit resets. Test: `test_defensive_reset_when_compare_list_and_result_disagree` | closed |
| T-03-22 | Tampering (integrity) | Indicator mutating compare_files/selection/result | low | mitigate | Read-only + `setData`/`setIcon`/`setToolTip` only. Test: `test_indicator_never_changes_comparison_or_selection` | closed |
| T-03-23 | Repudiation / transparency | Position matching pairs non-corresponding beams, misleading a sourcing decision | medium | mitigate | Rows labelled honestly by position ("Beam 1"/"Beam 2"), pinned to document order. Tests: `test_beam_position_follows_document_order_not_name`, `test_duplicate_beam_names_still_get_separate_positions` | closed |
| T-03-24 | Repudiation / transparency | Dropping per-model dimension rows silently removes profile checklist items | medium | mitigate | Existing D-06 status message reports them not-found. Test: `test_profile_listing_a_dimension_item_reports_it_not_found` | closed |
| T-03-25 | Tampering (integrity) | `compare()` mutating model attributes/result | low | mitigate | `_cross_file_attributes` builds a new dict, never writes to `model.attributes`. Test: `test_compare_leaves_models_untouched` | closed |
| T-03-26 | Denial of Service | One cross-file view built per model per `compare()` call | low | accept | Linear pass bounded by existing RELI-02 size cap, same order as existing union loop | accepted |

*Status: open · closed · open — below `high` threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above `workflow.security_block_on` (`high`) count toward `threats_open`*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

All 27 threats across the 5 executed plans are dispositioned. All 21 `mitigate` threats have a
named regression test, confirmed present on disk and passing in the 2026-10-11 full-suite run
(276 passed, 0 failed). The 6 `accept` threats (T-03-08, T-03-12, T-03-13, T-03-19, T-03-20,
T-03-26 — all low severity) are below the `high` block threshold and logged below.
`threats_open: 0`.

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|--------------|------|
| AR-03-01 | T-03-08 | Single-user desktop app; whole-file last-writer-wins never corrupts the file | Plan 03-01 threat model | 2026-10-04 |
| AR-03-02 | T-03-12 | Linear-cost recompute at the same cadence as an existing, already-accepted refilter | Plan 03-02 threat model | 2026-10-04 |
| AR-03-03 | T-03-13 | Qt status bar and dialogs render plain text only; no markup interpretation exists | Plan 03-02 threat model | 2026-10-04 |
| AR-03-04 | T-03-19 | No new untrusted content; appended text is always one of three fixed, code-defined strings | Plan 03-04 threat model | 2026-10-04 |
| AR-03-05 | T-03-20 | Linear-cost recompute bounded by the existing RELI-02 description.xml size cap | Plan 03-04 threat model | 2026-10-04 |
| AR-03-06 | T-03-26 | Linear-cost cross-file view build bounded by the existing RELI-02 size cap | Plan 03-05 threat model | 2026-10-07 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|----------------|--------|------|--------|
| 2026-10-11 | 27 | 21 (+6 accepted) | 0 | /gsd-secure-phase (retroactive, dispatched from /gsd-execute-phase 03's stale-verification re-run) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-11
