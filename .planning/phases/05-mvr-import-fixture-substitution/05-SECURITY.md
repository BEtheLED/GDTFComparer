---
phase: "05"
slug: "mvr-import-fixture-substitution"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-24"
---

# Phase 05 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| .mvr file → app | A show file from anywhere (another program, an email, a download): untrusted zip + XML | Entire MVR archive bytes |
| MVR member → GDTF pipeline | Each embedded .gdtf is a second untrusted archive inside the first | Embedded GDTF member bytes |
| requirements file ↔ other people | Written by one person for others, read on another machine from a file anyone could have edited | JSON sidecar file |
| inventory folder → app | Every .gdtf a shop has collected, from any manufacturer or source | GDTF archive bytes, folder listing |
| PyPI → shared venv | First install of pymvr | Third-party package |
| GUI thread ↔ worker thread | A stuck read on a slow or network drive must never freeze or abort the app | File handles, thread signals |
| results → shop's decision | What a cell's color claims is what a shop rents out | Scored match verdicts |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-05-01 | Tampering / Information Disclosure | GeneralSceneDescription.xml (XXE, entity expansion) | high | mitigate | `prevalidate_mvr_document` parses with defusedxml `forbid_dtd/forbid_entities/forbid_external=True` before pymvr ever sees the bytes (hardening.py:347) | closed |
| T-05-02 | Denial of Service | .mvr archive (zip bomb, oversized) | high | mitigate | `MAX_MVR_FILE_BYTES`, `MAX_MVR_TOTAL_UNCOMPRESSED_BYTES`, `MAX_COMPRESSION_RATIO` enforced before any member read (hardening.py) | closed |
| T-05-03 | Tampering | crafted GDTFSpec (path traversal) | high | mitigate | embedded GDTFs resolved only by exact match in the archive's own member list via `resolve_member_name`; `mvr_repository.py` imports neither tempfile nor shutil — nothing written to disk | closed |
| T-05-04 | Denial of Service | embedded .gdtf member (bomb inside the bomb) | high | mitigate | each member capped at `MAX_GDTF_FILE_BYTES`, then run through the same `prevalidate_gdtf_bytes` size/ratio/defusedxml checks as a standalone GDTF | closed |
| T-05-05 | Tampering | load_requirements (file from another person) | medium | mitigate | size-capped read, required format id, plain-int version check, matching tolerance_kind; strict `_parse_payload` validation added in 05-04 | closed |
| T-05-06 | Information Disclosure | requirements file contents | medium | mitigate | payload holds only fixture name, manufacturer, GDTF file name, tolerance_kind and marked requirements (D-09); asserted by the round-trip test | closed |
| T-05-07 | Information Disclosure | error text shown in dialogs | low | mitigate | pymvr failures become typed errors naming only the exception type; dialogs render `Qt.TextFormat.PlainText` (substitution_window.py, main_window.py) | closed |
| T-05-08 | Denial of Service | GUI responsiveness on a large show or folder | low | mitigate | `MVRImportWorker` and `CandidateScanWorker` run on QThreads, never touch widgets (worker.py) | closed |
| T-05-09 | Denial of Service | pymvr parse of deeply nested or field-malformed scene XML | medium | mitigate | `import_mvr` wraps pymvr construction/walk in one try; RecursionError/ValueError/UnicodeDecodeError become `MVRParseError` naming only the exception type (mvr_repository.py:216) | closed |
| T-05-10 | Repudiation (silent data loss) | fixture types dropped by cp437 mismatch, missing/broken embedded GDTF, or no GDTFSpec | medium | mitigate | cp437 recovery in `resolve_member_name`; every skipped type and unreferenced fixture named in `import_summary_message` | closed |
| T-05-11 | Denial of Service | a folder or named pipe picked as the MVR | medium | mitigate | `_read_file_bytes` opens with O_NONBLOCK and checks S_ISREG on the same descriptor before reading (hardening.py:127-144) | closed |
| T-05-12 | Denial of Service | a worker stuck at shutdown | medium | mitigate | bounded closeEvent waits; MainWindow closes Find Substitutes first; `app.py`'s `os._exit` guard checks `is_substitution_running()` (app.py:52,74) | closed |
| T-05-13 | Information Disclosure | error text built from file content | low | mitigate | fixed sentence plus at most an exception type name; labels/dialogs render plain text | closed |
| T-05-14 | Tampering (integrity of shared target) | requirement_options / editor rows | medium | mitigate | only declared, non-None values become rows (substitution.py:101) | closed |
| T-05-15 | Spoofing | file-supplied attribute/fixture names shown in editor | low | mitigate | QTreeWidgetItem text is plain text by Qt design; no rich-text built from file content | closed |
| T-05-16 | Denial of Service | load_requirements on oversized/deeply nested JSON | medium | mitigate | fstat + capped read at `MAX_REQUIREMENTS_FILE_BYTES`; RecursionError caught as damaged; `MAX_REQUIREMENTS_COUNT`/`MAX_TEXT_FIELD_LENGTH` bound parsed size | closed |
| T-05-17 | Tampering | type confusion / special values in payload | medium | mitigate | exact key sets, bool-before-number checks, finite-number checks, `parse_constant` refusal of NaN/Infinity, `object_pairs_hook` refusal of duplicate keys (requirements_repository.py:266-318) | closed |
| T-05-18 | Denial of Service | a named pipe/folder in the Open dialog freezing the GUI thread | medium | mitigate | `_read_requirements_bytes` opens with O_NONBLOCK, checks S_ISREG (requirements_repository.py:220-239) | closed |
| T-05-19 | Tampering (integrity) | interrupted save | medium | mitigate | same-folder O_EXCL temp file, fsync, os.replace, finally-cleanup; failure-injection tests prove prior bytes survive (requirements_repository.py:169-176) | closed |
| T-05-20 | Tampering | suggested save name built from file-supplied fixture name | low | mitigate | `suggested_file_name` strips path separators, reserved/control characters, leading/trailing dots, caps length | closed |
| T-05-21 | Information Disclosure | file permissions 0o644 on a shared computer | low | accept | the file exists to be shared and holds only one fixture's published spec values (D-09); nothing personal or show-specific | closed |
| T-05-22 | Denial of Service | named pipe/folder/device named *.gdtf in inventory folder | medium | mitigate | every entry goes through `FixtureRepository.load`'s `read_gdtf_bytes`, which reuses the same O_NONBLOCK/S_ISREG guard; becomes a failure row, never a hang | closed |
| T-05-23 | Denial of Service | zip-bomb or XXE inventory GDTF | high | mitigate | existing GDTF hardening (size, ratio, defusedxml) runs on every inventory file before pygdtf, unchanged; failures reported per file | closed |
| T-05-24 | Tampering (integrity of verdict) | score_value for undeclared/mismatched values | medium | mitigate | None or type mismatch is always RED, labeled "Not listed" (substitution.py:223) | closed |
| T-05-25 | Tampering | the inventory folder itself | medium | mitigate | the scan only lists and reads — no write call in `scan_candidate_folder`; `test_folder_is_never_modified` compares listing/bytes/mtimes before and after | closed |
| T-05-26 | Repudiation (silent omission) | unreadable inventory files | low | mitigate | every failure becomes a visible failure row (`CandidateFailure`, `FAILURE_ROW_ROLE`) and is counted in the summary | closed |
| T-05-27 | Denial of Service | a very large inventory folder | low | accept | scan runs on a background worker, each file individually size-capped, and the folder is the shop's own; costs time only | closed |
| T-05-SC | Tampering | pip install pymvr | high | mitigate | Task 1 blocking-human legitimacy checkpoint before any install (user-approved, recorded in 05-01-SUMMARY.md); exact pin `pymvr==1.0.7` in pyproject.toml:16; no other new package | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on (high) count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-05-01 | T-05-21 | Requirements file created 0o644 (minus umask) rather than 0o600 like profiles.json, because it exists to be shared by design (D-09) and carries only one fixture's already-public spec values — no positions, show name, or personal data | Plan 05-01 (Claude's discretion, documented in plan) | 2026-10-24 |
| AR-05-02 | T-05-27 | A very large inventory folder costs scan time, not safety — each file is independently size-capped and the scan runs off the GUI thread; the folder belongs to the shop running the scan | Plan 05-05 | 2026-10-24 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-24 | 28 | 28 | 0 | /gsd-secure-phase 05 (retroactive verification against merged implementation, post-execution) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-24

## Security Audit 2026-10-24

| Metric | Count |
|---|---|
| Threats found | 28 |
| Closed | 28 |
| Open | 0 |
