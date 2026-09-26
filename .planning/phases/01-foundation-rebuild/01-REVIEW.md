---
phase: 01-foundation-rebuild
reviewed: 2026-09-26T00:00:00Z
depth: standard
files_reviewed: 15
files_reviewed_list:
  - README.md
  - src/gdtf_comparer/app.py
  - src/gdtf_comparer/core/extract.py
  - src/gdtf_comparer/core/hardening.py
  - src/gdtf_comparer/core/models.py
  - src/gdtf_comparer/core/repository.py
  - src/gdtf_comparer/gui/main_window.py
  - tests/core/test_comparator.py
  - tests/core/test_extract.py
  - tests/core/test_hardening.py
  - tests/core/test_models.py
  - tests/gui/test_file_selection.py
  - tests/gui/test_shutdown.py
  - tests/gui/test_theme.py
  - tests/gui/test_unspecified_values.py
findings:
  critical: 0
  warning: 1
  info: 1
  total: 2
status: issues_found
---

# Phase 01: Code Review Report (re-review, gap-closure batch 01-06/01-07/01-08)

**Reviewed:** 2026-09-26
**Depth:** standard
**Files Reviewed:** 15
**Status:** issues_found

## Summary

This is a re-review scoped to the diff since `904e0ef` — the three gap-closure
plans (01-06, 01-07, 01-08) that closed prior findings Truth 6/CR-01
(N/A-vs-spec-default), WR-02 (target/comparison self-selection), IN-01/IN-02
(hygiene), and WR-01 (indefinite hang on special files and on window close
during a stuck comparison).

All four fixes were independently re-derived and verified against the
actual installed `pygdtf` 1.4.5 source (`.venv/lib/python3.12/site-packages/
pygdtf/`), not just against the project's own tests:

- **Truth 6 / CR-01 (`core/extract.py`, `core/hardening.py`,
  `core/repository.py`)** — `extract_attributes` now takes the validated
  `<GDTF>` tree alongside the pygdtf `FixtureType` and checks, attribute by
  attribute, whether the manufacturer's file actually declared it, using
  the exact same lookup chains pygdtf itself uses internally
  (`FixtureType._root.find("Geometries"/"Models")`,
  `Properties`'s `PhysicalDescriptions → Properties → Weight` chain with a
  `Value` attribute requirement, `TAG_TO_GEOMETRY_CLASS` as the child-tag
  filter). I traced each of these against pygdtf's real source and confirmed
  the presence checks in `_weight_declared`, `iter_geometry_paths` and
  `extract_attributes` align element-for-element with how pygdtf itself
  walks the tree, including the `GeometryReference`-has-no-`.geometries`
  special case and the fact that `Geometry.__init__` always initializes
  `.geometries` to an (empty) list, never `None`, so the lockstep walk can't
  false-positive a `DescriptionMismatchError` on an ordinary childless
  geometry. This fix is correct and well-tested (`tests/core/test_extract.py`,
  `tests/core/test_comparator.py`).
- **WR-02 (`gui/main_window.py`)** — `_normalized_path` (realpath + normcase)
  is now used consistently in both `set_target_file` (evicts an
  already-listed alias of the new target) and `add_compare_files` (refuses
  an alias of the current target), with status-bar feedback in both
  directions. Traced through the alias/symlink/`./`-segment test cases in
  `tests/gui/test_file_selection.py` and found the logic sound: guards
  against `self.target_file == ""` before computing a key, uses a
  `existing_keys` set to prevent both target-collision and intra-call
  duplicate-add races, and reports the skip/eviction message exactly once
  per call.
- **WR-01, T-01-28 (`core/hardening.py::read_gdtf_bytes`)** — opens the path
  once with `O_NONBLOCK` (where available), does the regular-file check via
  `fstat` on that same descriptor (no separate stat-then-open gap, T-01-30),
  and only then reads. This correctly turns what would otherwise be an
  indefinite `open()` block on a FIFO into an immediate, friendly
  `GDTFValidationError`. Verified this is consistent with POSIX semantics
  (a nonblocking read-side FIFO open never waits for a writer) and with
  `stat.S_ISREG` correctly excluding FIFOs/devices/directories while still
  reading regular files fully into memory in one pass.
- **WR-01, T-01-29 (`gui/main_window.py::closeEvent`, `app.py::main`)** — the
  bounded `thread.wait(CLOSE_WAIT_TIMEOUT_MS)` correctly reflects that
  `QThread.quit()` cannot interrupt a slot (`ComparisonWorker.run`) that is
  still synchronously blocked in a kernel read, since the thread's `exec()`
  event loop hasn't even started yet at that point — the timeout is the only
  way out, and `app.main`'s post-`exec()` `os._exit` on a still-running
  worker correctly avoids the Qt `QThread`-destroyed-while-running abort.
  Confirmed via both the unit test (bounded elapsed time) and the
  process-level subprocess test (clean exit code 0).

One robustness gap was found in the new `read_gdtf_bytes` code (see WR-01
below — using this review's own finding numbering, unrelated to the
project's identically-named historical WR-01 gap-closure item). It does not
regress any of the four fixes above and does not reproduce the original
hang, but it does let one class of OS-level failure escape the function's
documented, typed-error contract.

The full test suite (89 tests) passes locally.

## Warnings

### WR-01: `os.set_blocking` failure escapes `read_gdtf_bytes`'s typed-error contract

**File:** `src/gdtf_comparer/core/hardening.py:110-111`
**Issue:** Every other OS-level call in `read_gdtf_bytes` (`os.open`,
`os.fstat`, `os.fdopen`, `handle.read`) is wrapped in a `try/except OSError`
that re-raises as `GDTFValidationError`, per the function's documented
contract ("Raises: GDTFValidationError ... GDTFUnsafeFileError ..."). The one
call added by this fix that isn't wrapped is:

```python
if getattr(os, "O_NONBLOCK", 0):
    os.set_blocking(fd, True)
```

If this raises `OSError` (e.g. an exotic file-descriptor type — a special
device, a socket-like fd, or a platform where toggling `O_NONBLOCK` back off
is refused for a file that nonetheless passed `stat.S_ISREG`), it propagates
as a raw, untyped `OSError` out of `read_gdtf_bytes` instead of the friendly,
typed error every other failure path in this function produces. It doesn't
leak the file descriptor (the outer `finally: if owns_fd: os.close(fd)`
still runs, since `owns_fd` is only set `False` after `os.fdopen` succeeds),
and it doesn't crash the app (`ComparisonWorker.run`'s generic
`except Exception` still converts it to a generic user-facing message), but
it silently downgrades the specific, friendly "the file could not be read
(...)" message the rest of this function guarantees, for a rare edge case
that is easy to close along with the rest.

**Fix:**
```python
if getattr(os, "O_NONBLOCK", 0):
    try:
        os.set_blocking(fd, True)
    except OSError as exc:
        raise GDTFValidationError(
            path, f"the file could not be read ({exc.strerror})."
        ) from exc
```

## Info

### IN-01: `_weight_declared`'s docstring slightly misattributes where the lookup chain lives

**File:** `src/gdtf_comparer/core/extract.py:200-207`
**Issue:** The docstring says `_weight_declared` "Mirrors pygdtf's own lookup
chain exactly (`Properties._read_xml`)". I checked the installed pygdtf
source: the `PhysicalDescriptions → Properties` half of that chain is
actually walked in `pygdtf.FixtureType.__init__`
(`physical_descriptions_node.find("Properties")`), and only the final
`Properties → Weight` step happens inside `Properties._read_xml`
(`xml_node.find("Weight")`, where `xml_node` is already the `<Properties>`
element). The resulting behavior this function reproduces is correct — I
verified it end to end — but a future maintainer following the docstring's
pointer to `Properties._read_xml` to re-verify this against a new pygdtf
version would land in the wrong method and miss half the chain.
**Fix:** Reword to "Mirrors pygdtf's own lookup chain exactly
(`FixtureType.__init__`'s `PhysicalDescriptions → Properties` lookup, then
`Properties._read_xml`'s `Weight` lookup)" so the pointer covers both
methods that actually implement the chain.

---

_Reviewed: 2026-09-26_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
