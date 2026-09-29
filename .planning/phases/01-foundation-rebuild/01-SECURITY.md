---
phase: "01"
slug: "foundation-rebuild"
status: verified
threats_open: 0
asvs_level: 1
created: "2026-09-29"
---

# Phase 01 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| PyPI -> developer machine | Third-party wheels (and install hooks) enter the dev environment for the first time | Package code/binaries |
| venv -> git | Local-only environment artifacts must not enter version control | Dependency files |
| user-selected file -> core loader | Any file the user picks is untrusted input handed to pygdtf | Raw .gdtf bytes |
| worker thread -> GUI thread | Results cross threads via Qt queued signals | Parsed comparison results |
| pygdtf object model -> extraction | Element names/values originate from untrusted description.xml | Attribute strings |
| user-selected .gdtf -> core.hardening -> pygdtf | Untrusted zip+XML bytes are validated before pygdtf's stdlib XML parser ever sees them | Raw bytes, validated bytes |
| core errors -> GUI dialog | Error text derived from untrusted file names is displayed to the user | File basenames, error reasons |
| OS appearance setting -> app theme | Platform signal drives stylesheet changes at runtime | Theme state only (no fixture data) |
| app code -> network | Phase 1 has no outbound path for fixture data | N/A (guarded absence) |
| validated description.xml tree -> core.extract | Extraction reads attribute keys from already-validated content | Attribute presence flags |
| pygdtf object model <-> validated tree | Two views of the same bytes must stay element-aligned | Element/attribute pairing |
| file dialog / caller -> MainWindow selection state | User-chosen paths (possibly symlinks/relative) decide what gets compared | File paths |
| user-selected path -> core.hardening.read_gdtf_bytes | Path may name a folder, FIFO, device, or stalled mount | File handle/bytes |
| worker thread -> GUI thread at shutdown | Closing the window must not depend on the worker finishing | Thread lifecycle signals |
| GDTF description.xml -> header text/tooltip | Fixture names/manufacturers come from the untrusted, user-picked file | Name/manufacturer strings |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-01-SC | Tampering | pip install of PySide6/pygdtf/defusedxml/qt-material/pytest/pytest-qt (+ transitive) | high | mitigate | Blocking human legitimacy checkpoint before any install; exact version pins; isolated venv | closed |
| T-01-01 | Information Disclosure | .venv/caches committed to git | low | mitigate | .gitignore + git info/exclude entries before venv creation | closed |
| T-01-02 | Tampering | Typosquatted transitive dependency | medium | mitigate | Human comparison of expected packages/publishers; test_toolchain_versions asserts pinned versions | closed |
| T-01-03 | Denial of Service | FixtureRepository.load parsing an unvalidated file (XXE/zip bomb/oversized) | high | mitigate | core.hardening pre-validation runs before pygdtf at this exact load() call site (Plan 01-04) | closed |
| T-01-04 | Denial of Service | GUI freeze while parsing large files | medium | mitigate | Parse+compare run in ComparisonWorker on a QThread; UI stays responsive | closed |
| T-01-05 | Tampering / crash | Widget access from the worker thread | medium | mitigate | Worker only emits signals; widget mutation confined to GUI-thread slots | closed |
| T-01-06 | Denial of Service | QThread destroyed while running (second run or window close) | medium | mitigate | Thread parented to MainWindow; Run re-enabled only on finish; closeEvent quits and waits the thread | closed |
| T-01-07 | Denial of Service | iter_geometry_paths on a pathologically deep tree | low | mitigate | Iterative explicit-stack walk (no recursion in app code) | closed |
| T-01-08 | Tampering | Duplicate element names crafted to hide/overwrite a value | low | mitigate | _unique_path suffixing keeps every element's values as separate rows | closed |
| T-01-09 | Spoofing | Element names containing markup shown in the table | low | accept | QTableView DisplayRole renders plain text; names are data only | closed |
| T-01-10 | Information Disclosure | XXE external entity in description.xml | high | mitigate | defusedxml pre-parse with forbid_dtd/forbid_entities/forbid_external; test_xxe_rejected | closed |
| T-01-11 | Denial of Service | Billion-laughs entity expansion | high | mitigate | Same defusedxml pre-parse rejects any DTD/ENTITY; test_billion_laughs_rejected | closed |
| T-01-12 | Denial of Service | Zip bomb (small archive, huge decompression) | high | mitigate | Declared-total and ratio limits plus capped actual-bytes read; tests for ratio/total/description cap | closed |
| T-01-13 | Denial of Service | Oversized input file exhausting memory | medium | mitigate | File-size check against MAX_GDTF_FILE_BYTES before reading, capped read; test_oversized_file_rejected | closed |
| T-01-14 | Tampering | Path traversal via crafted zip member names | medium | mitigate | No member ever unpacked to disk; only "description.xml" read into memory; grep gate forbids unpacking/temp dirs | closed |
| T-01-15 | Tampering (TOCTOU) | File swapped between validation and parse / presence-check and pygdtf read | low | mitigate | File read once into memory; all downstream parsing uses io.BytesIO of the same validated bytes | closed |
| T-01-16 | Spoofing | pygdtf stub fixture shown as the user's file | medium | mitigate | Pre-parse raises on malformed XML before pygdtf; repository rejects stub name as defence in depth | closed |
| T-01-17 | Information Disclosure | Error/status text leaking tracebacks, paths, or rendering rich text from file names | low | mitigate | Messages use basename + fixed reason fragments; tracebacks go to logger; QMessageBox forced PlainText; QStatusBar does not interpret rich text | closed |
| T-01-18 | Information Disclosure | Fixture data leaving the machine via a network import added later | medium | mitigate | test_no_network_modules_in_package AST guard over every module in src/gdtf_comparer | closed |
| T-01-19 | Tampering | GUI re-coupled to parsing code, bypassing core hardening | medium | mitigate | test_gui_does_not_import_parsing_libraries + test_gui_uses_only_core_service_surface | closed |
| T-01-20 | Denial of Service | colorSchemeChanged re-apply loop | low | mitigate | apply_theme is idempotent via THEME_PROPERTY; single reused follower | closed |
| T-01-21 | Tampering | qt-material writing generated icon resources to a user/temp directory | low | accept | Limited to library's own theme assets; no user data involved; revisit at Phase 4 packaging | closed |
| T-01-22 | Tampering (data integrity) | Omitted attributes rendered as pygdtf spec defaults, making unlike fixtures look identical | medium | mitigate | Presence check per attribute on the paired validated element; 4 dedicated tests | closed |
| T-01-23 | Tampering | Crafted structure desynchronizes validated tree from pygdtf's model, misattributing presence | medium | mitigate | Lockstep pairing asserts tag/type/child-count equality; any divergence raises DescriptionMismatchError (fail closed) | closed |
| T-01-24 | Denial of Service | Second tree walk over a deep/wide tree | low | mitigate | Iterative explicit stack; reuses existing parsed tree; bounded by 64 MiB description cap | closed |
| T-01-25 | Information Disclosure | New error text exposing file content | low | mitigate | DescriptionMismatchError carries fixed text; dialog reports only exception type name | closed |
| T-01-26 | Tampering (result integrity) | Same file selected as target and comparison, producing misleading "no differences" | low | mitigate | add_compare_files refuses the target; set_target_file evicts it from comparisons | closed |
| T-01-27 | Spoofing | Symlink/"./" alias used to slip the target past a plain string comparison | low | mitigate | Comparison on os.path.normcase(os.path.realpath(path)) | closed |
| T-01-28 | Denial of Service | FIFO/device/folder picked as a GDTF blocks the worker's open/read forever | medium | mitigate | Non-blocking os.open plus fstat S_ISREG check before any read; friendly GDTFValidationError | closed |
| T-01-29 | Denial of Service | closeEvent blocks the GUI thread indefinitely waiting for a stuck worker | medium | mitigate | wait(CLOSE_WAIT_TIMEOUT_MS) bound; app.main uses os._exit when a worker is still running | closed |
| T-01-30 | Tampering (TOCTOU) | Path swapped for a pipe between being picked and read | low | mitigate | Regular-file check via fstat on the same descriptor that is then read | closed |
| T-01-31 | Repudiation / Information loss | os._exit skips Python shutdown handlers | low | accept | Core never writes to disk; logging.shutdown() and stdout/stderr flush run first; path taken only when a worker is still stuck at close | closed |
| T-01-32 | Spoofing | A comparison file's fixture name imitates another column header (same name, or "Target: " prefix) | low | mitigate (same-name) / accept (prefix) | Same-name collisions fall back to distinct file names; header tooltip always shows real full path; target column is fixed/first | closed |
| T-01-33 | Tampering | Header tooltip built from untrusted name/manufacturer, shown with Qt's automatic rich-text detection | low | accept | Header DisplayRole text painted as plain text; Qt tooltip rich text cannot run scripts or fetch remote resources | closed |
| T-01-34 | Denial of Service | A very long fixture name enters header text measured/elided on the GUI thread | low | accept | Bounded by existing 64 MiB description.xml cap; same exposure already accepted for element-path cells | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on (high) count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-01 | T-01-09 | Element names rendered via QTableView DisplayRole are plain text only; no rich-text/script execution path exists | Phase 01 plan (01-03) | 2026-09-28 |
| AR-02 | T-01-17 (status-bar variant) | Status-bar text shows only the basename the user just picked; QStatusBar does not interpret rich text | Phase 01 plan (01-07) | 2026-09-28 |
| AR-03 | T-01-21 | qt-material's generated icon resources stay inside the library's own theme assets; no user data involved; revisit at Phase 4 packaging | Phase 01 plan (01-05) | 2026-09-28 |
| AR-04 | T-01-31 | os._exit shutdown-handler skip is reached only when a worker is already stuck at window close, after logging/stdout/stderr are flushed; core never writes to disk | Phase 01 plan (01-08) | 2026-09-28 |
| AR-05 | T-01-32 (prefix variant) | A fixture legitimately named to start with "Target: " is a cosmetic collision only; the target column position and header tooltip's full path remove any ambiguity | Phase 01 plan (01-09) | 2026-09-28 |
| AR-06 | T-01-33 | Header/tooltip rich-text rendering is pre-existing since Plan 01-02 and is scoped to Qt's tooltip renderer, which cannot execute scripts or fetch remote resources | Phase 01 plan (01-09) | 2026-09-28 |
| AR-07 | T-01-34 | Long fixture names are bounded by the same 64 MiB description.xml cap already accepted for element-path cell rendering | Phase 01 plan (01-09) | 2026-09-28 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-29 | 34 | 34 | 0 | Claude (gsd-secure-phase, retroactive register from 9 phase PLAN.md threat models; threats_open: 0 AND register_authored_at_plan_time: true AND asvs_level == 1 short-circuit, no additional auditor pass required) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-09-29
