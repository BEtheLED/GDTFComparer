---
phase: "02"
slug: "attribute-browsing-diff-highlighting"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-12"
---

# Phase 2 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

Built retroactively from the `<threat_model>` blocks in 02-01/02-02/02-03-PLAN.md
(`register_authored_at_plan_time: true` — all three plans carry a formal STRIDE
register). No `## Threat Flags` were raised in any SUMMARY.md during execution.
`workflow.security_asvs_level=1` and `threats_open: 0` at plan-time classification,
so per the secure-phase short-circuit rule this skipped auditor spawn — L1
grep/test-level verification is sufficient at ASVS level 1.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| GDTF `description.xml` → category/attribute/value strings → picker item text and table cells | Untrusted, user-picked file content; already size-bounded and `defusedxml`-parsed by `core.hardening` (RELI-02, Phase 1) | Attribute/category/element names (display only) |
| User keystrokes → search box → picker visibility | Local, same-user input; never persisted, logged or sent anywhere | Search query string |
| `ComparisonResult` (core-computed booleans) → table model roles → delegate painting | Reads only `differs`/`any_differs` flags; no file text decides a highlight, filter, or row | Boolean diff flags only |
| Bundled qt-material theme XML → highlight colour | Theme name comes from this app's own constants, never from user input or GDTF content | Theme name string (app-internal) |
| User clicks → "Show differences only" checkbox | Local, same-user input; changes only which existing rows are shown | UI toggle state |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-02-01 | Tampering | `AttributePicker` item text built from attribute/category names in the file | low | mitigate | Text set via `setText` only, never `setToolTip`; verified `grep -c "setToolTip" src/gdtf_comparer/gui/attribute_picker.py` → 0 | closed |
| T-02-02 | Denial of Service | A file declaring many distinct attribute names builds a large tree on the GUI thread | low | accept | Picker entries bounded by existing 64 MiB description.xml/zip limits (core.hardening); user picked the file and can close the app | closed |
| T-02-03 | Information Disclosure | Search text and the checked set | low | accept | Held in memory for the session only; no disk writes, no logging; `tests/test_architecture.py::test_no_network_modules_in_package` still passes | closed |
| T-02-04 | Tampering | A filter that drops checked rows, or search that changes the comparison | medium | mitigate | `AttributeSelectionProxyModel` is view-only, reads a data role, never touches the source model/`ComparisonResult`. Verified: `test_unchecking_attribute_hides_its_rows`, `test_search_does_not_change_table_rows`, `test_search_hides_non_matching_without_changing_checks`, `test_rebuild_keeps_choices_and_seeds_new_pairs` — 4/4 pass | closed |
| T-01-33 (carried) | Tampering | Table cell tooltips from file content via Qt's automatic rich-text detection | low | accept | No new tooltip channel added by Phase 2; table `ToolTipRole` unchanged from Phase 1; no network modules in package | closed |
| T-02-05 | Spoofing | A file-supplied feature-group name (e.g. "Beam") impersonating a legacy section and inheriting its default-checked state | medium | mitigate | Every DMX definition category is `DMX_ATTRIBUTE_CATEGORY_PREFIX` + group; no legacy/`DEFAULT_SELECTED_CATEGORIES` entry starts with that prefix. Verified: `test_legacy_named_definitions_do_not_collide`, `test_dmx_beam_group_stays_separate_and_unchecked`, `test_default_table_unchanged_by_dmx_definitions` — 3/3 pass | closed |
| T-02-06 | Tampering | Misattributed values if the validated tree and pygdtf's definition list drift apart | medium | mitigate | Lockstep count/Name check raises `DescriptionMismatchError`. Verified: `test_definition_count_mismatch_raises`, `test_definition_name_mismatch_raises` — 2/2 pass | closed |
| T-02-07 | Tampering / Elevation | New extraction code loading or parsing file bytes itself, bypassing the Phase 1 hardening boundary | high | mitigate | Extraction reads only the handed `description_root`. Verified: `grep -cE "zipfile\|fromstring\|\.parse\(\|open\(" src/gdtf_comparer/core/extract.py` → 0; `tests/test_architecture.py::test_core_never_unpacks_archives_or_uses_temp_dirs` passes | closed |
| T-02-08 | Denial of Service | A file declaring very many definitions produces six rows each | low | accept | Rows grow linearly, bounded by core.hardening's existing limits; DMX rows unchecked by default | closed |
| T-02-09 | Information Disclosure | Definition text shown in table tooltips (Qt auto rich-text detection, carries T-01-33) | low | accept | No new tooltip channel; table `ToolTipRole` unchanged; no network modules | closed |
| T-02-10 | Tampering | Integrity of the displayed diff: a highlight/filter that disagrees with core, or mutates `ComparisonResult` | medium | mitigate | `BackgroundRole`/`ANY_DIFFERS_ROLE` read `differs`/`any_differs` only; proxy is view-only. Verified: `test_highlight_follows_differs_flags_not_text`, `test_toggle_never_mutates_result`, `test_live_dark_switch_retints_without_rerun`, `test_toggle_hides_rows_without_differences` — 4/4 pass | closed |
| T-02-11 | Repudiation / transparency | Rows hidden without the user knowing why the table is short or empty | medium | mitigate | Checkbox starts unticked above the table; empty result under toggle shows `NO_DIFFERENCES_MESSAGE`. Verified: `test_toggle_starts_unticked_above_table`, `test_all_equal_shows_no_differences_message` — 2/2 pass | closed |
| T-02-12 | Denial of Service | Re-parsing theme XML from disk per painted cell freezes scrolling on large tables | low | mitigate | `_theme_color_hex` is `lru_cache`d per theme name; model holds a ready `QBrush`. Verified: `test_theme_file_parsed_once_per_theme` passes; `grep -cE "QApplication\|gui\.theme" src/gdtf_comparer/gui/table_model.py` → 0 | closed |
| T-02-13 | Tampering | `qt_material.get_theme` writes `QTMATERIAL_*` colour values into `os.environ` | low | accept | Process-local, bundled hex values; same writes `apply_stylesheet` already performs on every theme change; nothing reads them back | closed |
| T-02-14 | Denial of Service | The delegate paints every visible cell | low | accept | One `BackgroundRole` lookup (tuple index) plus one `fillRect` only when a brush exists; sizing/text painting stay Qt's own | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above `workflow.security_block_on` (high) count toward `threats_open`*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-02-01 | T-02-02 | Tree size bounded by Phase 1's 64 MiB file/zip limits; user controls which file they open | Plan 02-01 author | 2026-09-29 |
| R-02-02 | T-02-03 | Session-memory only, no persistence or logging | Plan 02-01 author | 2026-09-29 |
| R-02-03 | T-01-33 | No new tooltip channel added; carried risk from Phase 1 | Plan 02-01 author | 2026-09-29 |
| R-02-04 | T-02-08 | Rows scale linearly with existing bounded input; DMX rows default unchecked | Plan 02-02 author | 2026-09-29 |
| R-02-05 | T-02-09 | No new tooltip channel; same carried risk as T-01-33 | Plan 02-02 author | 2026-09-29 |
| R-02-06 | T-02-13 | Process-local env writes already made by `apply_stylesheet`; never read back | Plan 02-03 author | 2026-09-29 |
| R-02-07 | T-02-14 | Per-cell paint cost is O(1) (tuple index + conditional fillRect) | Plan 02-03 author | 2026-09-29 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-12 | 14 | 14 | 0 | Claude (gsd-secure-phase, orchestrator — ASVS L1 short-circuit, auditor not spawned) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-12

## Security Audit 2026-10-14

| Metric | Count |
|---|---|
| Threats found | 14 |
| Closed | 14 |
| Open | 0 |
