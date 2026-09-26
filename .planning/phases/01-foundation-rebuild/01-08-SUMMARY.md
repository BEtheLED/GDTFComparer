---
phase: 01-foundation-rebuild
plan: 08
subsystem: reliability-hardening
tags: [gdtf-parsing, qt-threading, denial-of-service, file-io, shutdown, gap-closure]
requires:
  - phase: 01-foundation-rebuild
    provides: "read_gdtf_bytes/prevalidate_gdtf (01-04), MainWindow QThread worker lifecycle (01-04), 01-REVIEW.md WR-01 finding (code review)"
provides:
  - "read_gdtf_bytes refuses folders, FIFOs and device files via a single non-blocking os.open + fstat S_ISREG check, before any blocking read is attempted"
  - "MainWindow.closeEvent bounded to CLOSE_WAIT_TIMEOUT_MS (3s) instead of an unbounded QThread.wait()"
  - "gdtf_comparer.app.main ends the process with os._exit when a worker is still running after the Qt event loop returns, avoiding a Qt abort on a still-running QThread"
affects: [gui-shutdown, core-hardening, packaging]
actuals:
  tokens: 3929
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns:
    - "Single non-blocking os.open + os.fstat(fd) + stat.S_ISREG check on the same descriptor that is then read, closing the TOCTOU gap between checking and reading a path (T-01-30)"
    - "Bounded QThread.wait(timeout_ms) plus a deferred os._exit(exit_code) in the composition root when the event loop ends with a worker still running, instead of terminate()/force-killing a QThread"
key-files:
  created:
    - tests/gui/test_shutdown.py
  modified:
    - src/gdtf_comparer/core/hardening.py
    - tests/core/test_hardening.py
    - src/gdtf_comparer/gui/main_window.py
    - src/gdtf_comparer/app.py
    - README.md
key-decisions:
  - "Refuse special files (folders/pipes/devices) with GDTFValidationError, not GDTFUnsafeFileError, since they are unreadable inputs rather than hostile content -- RELI-02's size/zip-bomb/defusedxml limits are untouched"
  - "closeEvent always closes the window after its bounded wait; it never force-terminates the QThread, since Qt's terminate() is unsafe while the interpreter is running and a still-running QThread would abort the process if destroyed"
  - "app.main is the only place that calls os._exit, and only when window.is_comparison_running() is still True after app.exec() returns -- a normal close-during-comparison (test_close_during_comparison_does_not_crash) never reaches this path"
patterns-established:
  - "Robustness-only gap closure: a code-review Warning (01-REVIEW.md WR-01) closed by hardening two independent choke points (file-open path and window-close path) without touching any existing message, limit, or public contract"
requirements-completed: [RELI-01, RELI-02]
coverage:
  - id: D1
    description: "Picking a folder, FIFO or device file as a GDTF gives a friendly 'not a regular file' error within 2s instead of hanging"
    requirement: "RELI-01"
    verification:
      - kind: unit
        ref: "tests/core/test_hardening.py::test_fifo_rejected_without_blocking"
        status: pass
      - kind: unit
        ref: "tests/core/test_hardening.py::test_directory_rejected"
        status: pass
      - kind: regression
        ref: "tests/core/test_hardening.py (12 pre-existing tests) + tests/core/test_repository.py + tests/gui/test_error_handling.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "The regular-file check runs via fstat on the same descriptor that is then read, so a path swapped for a pipe after being picked is still refused before any read (TOCTOU-safe)"
    requirement: "RELI-02"
    verification:
      - kind: static-check
        ref: "grep -n os.fstat( / S_ISREG in src/gdtf_comparer/core/hardening.py -- single os.open, no separate os.stat(path) call"
        status: pass
    human_judgment: false
  - id: D3
    description: "Closing the window while a worker is stuck returns within CLOSE_WAIT_TIMEOUT_MS (3s, shrunk to 200ms in tests) instead of blocking the GUI thread indefinitely"
    requirement: "RELI-01"
    verification:
      - kind: integration
        ref: "tests/gui/test_shutdown.py::test_close_returns_promptly_when_worker_is_stuck"
        status: pass
    human_judgment: false
  - id: D4
    description: "When the event loop ends with a worker still stuck, the process exits promptly with the app's exit code (no abort on a destroyed running QThread)"
    requirement: "RELI-02"
    verification:
      - kind: integration
        ref: "tests/gui/test_shutdown.py::test_app_process_exits_when_worker_stuck_at_close"
        status: pass
    human_judgment: false
  - id: D5
    description: "Closing during a comparison that finishes normally still waits for it and leaves no running thread (no regression)"
    requirement: "RELI-01"
    verification:
      - kind: regression
        ref: "tests/test_walking_skeleton.py::test_close_during_comparison_does_not_crash"
        status: pass
      - kind: regression
        ref: "full suite: pytest -q (89 passed)"
        status: pass
    human_judgment: false
  - id: D6
    description: "README Safety section documents that folders, pipes and device files are refused"
    requirement: "RELI-01"
    verification:
      - kind: static-check
        ref: "grep -q pipes README.md"
        status: pass
    human_judgment: false
duration: 15min
completed: 2026-09-26
status: complete
---

# Phase 01 Plan 08: Close the Input and Close-Path Hang (WR-01) Summary

**Selecting a folder, named pipe or device file as a GDTF now fails fast with a friendly message instead of hanging the worker forever, and closing the window while a worker is stuck returns within 3 seconds and the whole process still exits cleanly.**

## Performance
- **Duration:** ~15min
- **Started:** 2026-09-26T17:37:07-05:00 (first RED commit)
- **Completed:** 2026-09-26T17:40:20-05:00 (last GREEN commit)
- **Tasks:** 2
- **Files modified:** 6 (1 created, 5 modified)

## Accomplishments
- `read_gdtf_bytes` now opens a `.gdtf` path exactly once with `O_NONBLOCK` (where available), checks `stat.S_ISREG` via `os.fstat` on that same descriptor, and only then restores blocking mode and reads the file — a folder, FIFO or device file is refused immediately instead of blocking the comparison worker forever (closes the input half of 01-REVIEW.md WR-01 / T-01-28).
- The regular-file check and the read share one file descriptor, so there is no TOCTOU gap between "check" and "read" (T-01-30) — a path swapped for a pipe after being picked is still caught.
- Every existing hardening/repository message and limit (missing file, zero-byte file, oversized file, zip-bomb, XXE, description-size caps) is unchanged and still passes.
- `MainWindow.closeEvent` now waits at most `CLOSE_WAIT_TIMEOUT_MS` (3000ms, a module constant read at call time) for the worker thread instead of an unbounded `QThread.wait()`, logging a warning and closing anyway if the worker is still running (closes the close-path half of WR-01 / T-01-29).
- `gdtf_comparer.app.main` checks `window.is_comparison_running()` after `app.exec()` returns and ends the process with `os._exit(exit_code)` only in that case — Qt aborts the process if a still-running `QThread` is destroyed during interpreter shutdown, and a thread blocked in a kernel read cannot be stopped from Python. Nothing is lost since `core` never writes to disk (T-01-15).
- A normal close during an in-flight comparison (the existing 0.3s slow-worker test) still waits for the worker and finishes cleanly — the bounded wait comfortably exceeds it.
- README's Safety section now documents that folders, pipes and device files are refused before anything is read from them.

## Task Commits
1. **Task 1 RED: failing special-file rejection tests** - `2e15d5e` (test)
2. **Task 1 GREEN: non-blocking open + fstat regular-file check** - `1b49c86` (feat)
3. **Task 2 RED: failing bounded-close / process-exit tests** - `d6c020c` (test)
4. **Task 2 GREEN: bounded closeEvent + prompt os._exit in app.main** - `314fdd3` (feat)

No REFACTOR commits were needed — both GREEN implementations were already minimal and matched the plan's design notes without follow-up cleanup.

## Files Created/Modified
- `src/gdtf_comparer/core/hardening.py` - `read_gdtf_bytes` rewritten around a single `os.open`/`os.fstat`/`stat.S_ISREG` check; new "not a regular file" reason text; docstring updated
- `tests/core/test_hardening.py` - added `test_fifo_rejected_without_blocking` (FIFO, skipped where `os.mkfifo` is unavailable) and `test_directory_rejected` (folder, skipped on Windows)
- `src/gdtf_comparer/gui/main_window.py` - added `CLOSE_WAIT_TIMEOUT_MS = 3000`, a module `_LOGGER`, and a bounded `closeEvent`
- `src/gdtf_comparer/app.py` - `main()` now ends the process with `os._exit` when a worker is still running after `app.exec()` returns
- `tests/gui/test_shutdown.py` (new) - `test_close_returns_promptly_when_worker_is_stuck` (in-process, bounded close) and `test_app_process_exits_when_worker_stuck_at_close` (subprocess, full exit)
- `README.md` - one new Safety sentence about refused special files

## Decisions Made
See `key-decisions` in frontmatter. No decisions departed from the plan's own Design Notes.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. Both RED phases failed for the expected reason (assertion failure on the friendly message text; genuine subprocess timeout) rather than an unrelated error, and both GREEN phases passed on the first implementation attempt. The full suite (`pytest -q`, 89 tests) passes with no regressions, including `tests/test_walking_skeleton.py::test_close_during_comparison_does_not_crash`, `test_app_module_launches`, and `tests/test_architecture.py`.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
Phase 01 complete, ready for verification.

---
*Phase: 01-foundation-rebuild*
*Completed: 2026-09-26*
