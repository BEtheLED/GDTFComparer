---
phase: 01-foundation-rebuild
plan: 04
subsystem: reliability-hardening
tags: [defusedxml, pygdtf, xxe, zip-bomb, error-handling, pyside6, qmessagebox]
dependency graph:
  requires:
    - "01-02 (walking-skeleton tracer: core.repository.FixtureRepository.load, core.comparator.compare_files, gui.worker.ComparisonWorker, gui.main_window.MainWindow -- this plan hardens the same load()/run()/_show_error() call sites without renaming any public member)"
  provides:
    - "core.errors: GDTFError, GDTFValidationError, GDTFUnsafeFileError, GDTFParseError -- typed hierarchy carrying path + friendly user_message"
    - "core.hardening: read_gdtf_bytes, extract_description_bytes, parse_description_safely, prevalidate_gdtf, plus MAX_GDTF_FILE_BYTES/MAX_DESCRIPTION_XML_BYTES/MAX_TOTAL_UNCOMPRESSED_BYTES/MAX_COMPRESSION_RATIO/RATIO_CHECK_FLOOR_BYTES/DESCRIPTION_MEMBER"
    - "core.repository.FixtureRepository.load: prevalidate_gdtf() -> pygdtf on the same validated bytes -> typed errors; PYGDTF_BROKEN_XML_STUB_NAME defence-in-depth check"
    - "gui.worker.ComparisonWorker.run: GDTFError -> friendly user_message; any other exception logged + reported generically, nothing escapes run()"
    - "gui.main_window.MainWindow._show_error: plain-text QMessageBox (Qt.TextFormat.PlainText)"
  affects:
    - "01-03 (fills extract_attributes; unaffected -- this plan's changes to repository.load's error path run before extract_attributes is ever called)"
    - "01-05 (theming/app.py composition root; its architecture test allows gui to import gdtf_comparer.core.errors, added here)"
tech-stack:
  added: []
  patterns:
    - "Pre-validation before pygdtf (RESEARCH Pattern 1): read_gdtf_bytes -> extract_description_bytes -> parse_description_safely, all complete before pygdtf.FixtureType ever runs, closing the RELI-01/RELI-02 gap left by pygdtf's silent malformed-XML fallback"
    - "Single-read, no-disk-write loading: prevalidate_gdtf reads the archive once into memory; pygdtf then parses io.BytesIO of those same bytes, so there is no second disk read and no check-then-parse (TOCTOU) gap (T-01-15)"
    - "Typed-error boundary at the worker/thread edge (D-14): GDTFError.user_message flows straight to a plain-text QMessageBox; any other exception is logged via logging.getLogger(__name__).exception and reported generically, never escaping run() into the Qt event loop"
key-files:
  created:
    - src/gdtf_comparer/core/errors.py
    - src/gdtf_comparer/core/hardening.py
    - tests/core/test_hardening.py
    - tests/core/test_repository.py
    - tests/gui/test_error_handling.py
  modified:
    - src/gdtf_comparer/core/repository.py
    - src/gdtf_comparer/gui/worker.py
    - src/gdtf_comparer/gui/main_window.py
  deleted: []
decisions:
  - "Confirmed directly against the installed pygdtf 1.4.5 source (__init__.py) that FixtureType.__init__ only ever reads self.path once, to call zipfile.ZipFile(path, \"r\") -- no other use exists anywhere in the class. repository.load() therefore safely passes io.BytesIO(data) (the already-validated bytes) instead of the original path string, with no residual time-of-check/time-of-use gap left to document -- the plan's fallback contingency ('pass the original path string instead') was not needed."
  - "parse_description_safely's description.xml size guard runs twice on purpose: once against the zip header's declared file_size (fast-fail before reading a huge member into memory) and once against the actual bytes returned by a capped MAX_DESCRIPTION_XML_BYTES+1 read (RESEARCH's explicit 'never trust the header alone' guidance) -- both paths raise the same GDTFUnsafeFileError."
metrics:
  duration: "~45 min"
  completed: 2026-09-26
status: complete
actuals:
  tokens: 8386
  tasks: 2
  commits: 2
  plan_head_before: d82c0d5304f7434629b1e418a42c81205b265e72
---

# Phase 01 Plan 04: Corrupt/Malicious GDTF Files Rejected With Friendly Errors Summary

**defusedxml (forbid_dtd/forbid_entities/forbid_external) plus size/ratio limits reject XXE, billion-laughs, zip bombs, oversized files and malformed XML before pygdtf ever parses them; every failure surfaces as a typed `GDTFError` rendered in a plain-text `QMessageBox` naming the file, and the app stays usable after an error.**

## What Was Built

**Task 1 — Corrupt or malicious GDTF files are rejected with typed, friendly errors before pygdtf parses them:**

- **`core/errors.py`** — `GDTFError(path, reason)` base class with `file_name` (basename) and `user_message` (`"Could not open '<file_name>': <reason>"`) properties, `__str__` returning `user_message`; `GDTFValidationError(GDTFError)`; `GDTFUnsafeFileError(GDTFValidationError)`; `GDTFParseError(GDTFError)`. No tracebacks or exception reprs ever appear in a message.
- **`core/hardening.py`** — `read_gdtf_bytes(path)` checks `os.path.getsize` against `MAX_GDTF_FILE_BYTES` (100 MB) before reading, then reads at most `limit + 1` bytes in one open so a file that grew past the limit is also caught; `extract_description_bytes(data, path)` opens `zipfile.ZipFile(io.BytesIO(data))`, sums `file_size`/`compress_size` across `infolist()` to reject oversized-total (1 GB) or bad-ratio (>100x above a 10 MB floor) archives, looks up `description.xml` by exact name (`KeyError` -> "description.xml is missing", matching pygdtf's own exact-name lookup so a mis-cased member is treated the same way), checks the declared size against `MAX_DESCRIPTION_XML_BYTES` (64 MB) and then re-checks the *actual* bytes from a capped `limit + 1` read (never trusts the header alone); `parse_description_safely(xml_bytes, path)` strips one trailing NUL byte (mirrors pygdtf's `_find_root`), then calls `defusedxml.ElementTree.fromstring(xml_bytes, forbid_dtd=True, forbid_entities=True, forbid_external=True)` — `DefusedXmlException` -> `GDTFUnsafeFileError` ("rejected for safety reasons ... DTD or entities"), `ET.ParseError` -> `GDTFValidationError` naming the line/column from `exc.position`, non-`GDTF` root or missing `FixtureType` child -> `GDTFValidationError` ("does not contain a GDTF fixture definition"); `prevalidate_gdtf(path)` chains all three and returns the validated bytes. Every raise uses `from exc`. Only the exact `"description.xml"` member is ever read; nothing is unpacked to disk (verified live against XXE and billion-laughs payloads during implementation — both raise `DTDForbidden`, a `DefusedXmlException` subclass, confirming `forbid_dtd=True` alone blocks both attack classes since neither can declare entities without a DOCTYPE).
- **`core/repository.py`** — `FixtureRepository.load(path)` now calls `prevalidate_gdtf(path)` first, then opens `pygdtf.FixtureType(io.BytesIO(data))` as a context manager on the *same* validated bytes (confirmed via direct read of the installed pygdtf source that `FixtureType.__init__` only ever uses `path` to construct `zipfile.ZipFile`, so passing a `BytesIO` is safe and leaves no TOCTOU gap — see Decisions). Any other exception from pygdtf/extraction is wrapped as `GDTFParseError(path, f"its GDTF data could not be parsed ({type(exc).__name__}).") from exc`. New module constant `PYGDTF_BROKEN_XML_STUB_NAME = "Original File Had Broken XML"` is checked as defence-in-depth (unreachable under normal operation since `prevalidate_gdtf` already rejects malformed XML, but guards against ever displaying pygdtf's stub fixture as the user's file). `compare_files` needed no change — it already loads sequentially and lets the first error propagate, verified by a new test.
- **`tests/core/test_hardening.py`** (12 tests) and **`tests/core/test_repository.py`** (10 tests) — 22 tests total covering every bad-input class (malformed XML, XXE, billion-laughs, oversized file, bad compression ratio, oversized total, description-size cap via actual bytes not just the header, missing/mis-cased description.xml, non-GDTF root, trailing-NUL tolerance, valid-file pass-through, invalid zip, empty file, missing file, pygdtf-crash wrapping with `__cause__` preserved, non-ASCII name/manufacturer/path round-trip, no-disk-write via monkeypatched `tempfile.mkdtemp`/`TemporaryDirectory`/`NamedTemporaryFile`, `compare_files(target, [])` returning `comparisons == ()`, and `compare_files([good, bad])` failing the whole batch and naming the bad file).

**Task 2 — The app shows a friendly plain-text error naming the bad file and stays usable:**

- **`gui/worker.py`** — imports `GDTFError` from `gdtf_comparer.core.errors` (the one core surface the GUI is allowed to touch beyond `comparator`/`models`). `run()` catches `GDTFError` and emits `comparison_failed(exc.user_message)`; catches any other `Exception`, logs it via `logging.getLogger(__name__).exception(...)` (full traceback to the log, never to the user), and emits a generic `"Something went wrong while comparing files (<ExceptionType>). Check that every selected file is a valid GDTF fixture and try again."` message. Nothing escapes `run()`.
- **`gui/main_window.py`** — `_show_error` now constructs a `QMessageBox(Warning, "GDTF Comparer", message, Ok, self)`, calls `setTextFormat(Qt.TextFormat.PlainText)`, then `exec()` — so a file name containing HTML-like characters is never interpreted as rich text (T-01-17). The tracer's guard messages, `set_result(None)` on failure, and the single `run_button.setEnabled(True)` re-enable point in `_on_thread_finished` were all left untouched, matching the interfaces contract (Plans 01-03/01-05 tests depend on these names).
- **`tests/gui/test_error_handling.py`** (7 tests) — captures dialogs by monkeypatching `QMessageBox.exec` to record `(text(), textFormat())`; covers a corrupt (non-zip) target, a malformed-XML comparison file among `[good, broken]` (names `broken.gdtf`, table stays empty — no partial result), an XXE comparison file ("rejected for safety" in the message), full recovery after an error (remove the bad file, add a good one, run again, `Weight` row appears and `run_button` is enabled), the exact no-target/no-comparison guard message text, and an unexpected `RuntimeError` from a monkeypatched `compare_files` being reported (`"Something went wrong while comparing files (RuntimeError)..."`) rather than raised into the Qt event loop.

## Verification

- `"$PY" -m pytest tests/core/test_hardening.py tests/core/test_repository.py -q` -> **22 passed**
- `"$PY" -m pytest tests/gui/test_error_handling.py -q` -> **7 passed**
- `"$PY" -m pytest -q` (full suite) -> **39 passed** (10 pre-existing + 22 new core + 7 new gui)
- Named 5-test subset (`test_malformed_xml_raises`, `test_xxe_rejected`, `test_oversized_file_rejected`, `test_invalid_zip_raises`, `test_load_valid_gdtf`) -> **5 passed**
- Acceptance-criteria greps: `forbid_dtd=True`, `forbid_entities=True`, `forbid_external=True` all present in `hardening.py`; `prevalidate_gdtf(` present in `repository.py` before the pygdtf call; `hardening.py` defines all five limit constants at the interfaces-block values; `errors.py` defines the full `GDTFError`/`GDTFValidationError`/`GDTFUnsafeFileError`/`GDTFParseError` hierarchy; no `.extractall(` and no `tempfile`/`shutil` import anywhere in `src/gdtf_comparer/core`; `user_message` and `logging.getLogger` present in `worker.py`; `PlainText` present in `main_window.py`; `gui/` imports nothing from `core.repository`/`core.extract`/`core.hardening` (only `core.comparator`, `core.models`, `core.errors`) -- all confirmed individually via grep.

## Deviations from Plan

None — plan executed exactly as written. Two facts the plan flagged as needing confirmation during implementation were both verified directly against the installed pygdtf 1.4.5 source and matched the plan's assumption (no code deviated):

1. `pygdtf.FixtureType.__init__` accepts a file-like object for `path` (it forwards straight to `zipfile.ZipFile(path, "r")`, which accepts a `BytesIO`) — confirmed by reading `__init__.py:116-131` directly.
2. `self.path` is never used anywhere else in `FixtureType` beyond that one `zipfile.ZipFile` call — confirmed via `grep -n "self\.path\b"` against the installed source, so the plan's fallback ("pass the original path string instead and record the residual time-of-check/time-of-use gap") was not needed; there is no residual TOCTOU gap to document.

## Known Stubs

None. Every code path added or changed in this plan is exercised by a real test with a real assertion; no hardcoded empty/placeholder value flows to the UI.

## Threat Flags

None beyond what the plan's own threat model already tracks (T-01-10 through T-01-17, all mitigated here exactly as planned: XXE, billion-laughs, zip bomb, oversized file, path traversal via no-extractall, TOCTOU via single-read, pygdtf-stub spoofing, and traceback/rich-text leakage in error dialogs). This plan introduced no new trust-boundary surface beyond what the threat register already anticipated.

## Self-Check: PASSED

- FOUND: src/gdtf_comparer/core/errors.py
- FOUND: src/gdtf_comparer/core/hardening.py
- FOUND: src/gdtf_comparer/core/repository.py (modified)
- FOUND: src/gdtf_comparer/gui/worker.py (modified)
- FOUND: src/gdtf_comparer/gui/main_window.py (modified)
- FOUND: tests/core/test_hardening.py
- FOUND: tests/core/test_repository.py
- FOUND: tests/gui/test_error_handling.py
- FOUND commit: 89821b6 (feat(01-04): reject corrupt/malicious GDTF files before pygdtf parses them)
- FOUND commit: 7a972ac (feat(01-04): show friendly plain-text errors and keep the app usable)
