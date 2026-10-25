---
phase: 05-mvr-import-fixture-substitution
reviewed: 2026-10-24T00:00:00Z
depth: standard
files_reviewed: 25
files_reviewed_list:
  - pyproject.toml
  - src/gdtf_comparer/app.py
  - src/gdtf_comparer/core/errors.py
  - src/gdtf_comparer/core/hardening.py
  - src/gdtf_comparer/core/mvr_repository.py
  - src/gdtf_comparer/core/repository.py
  - src/gdtf_comparer/core/requirements_repository.py
  - src/gdtf_comparer/core/substitution.py
  - src/gdtf_comparer/gui/candidate_results.py
  - src/gdtf_comparer/gui/main_window.py
  - src/gdtf_comparer/gui/requirements_editor.py
  - src/gdtf_comparer/gui/substitution_window.py
  - src/gdtf_comparer/gui/worker.py
  - tests/conftest.py
  - tests/core/test_mvr_hardening.py
  - tests/core/test_mvr_repository.py
  - tests/core/test_requirement_defaults.py
  - tests/core/test_requirements_repository.py
  - tests/core/test_substitution.py
  - tests/gui/test_candidate_results.py
  - tests/gui/test_mvr_import.py
  - tests/gui/test_requirements_editor.py
  - tests/gui/test_requirements_file.py
  - tests/gui/test_substitution_round_trip.py
  - tests/test_architecture.py
  - tests/test_fixture_builder.py
findings:
  critical: 1
  warning: 3
  info: 1
  total: 5
status: issues_found
---

# Phase 05: Code Review Report

**Reviewed:** 2026-10-24T00:00:00Z
**Depth:** standard
**Files Reviewed:** 25 (13 source, 13 test/fixture files read for cross-reference)
**Status:** issues_found

## Summary

This phase adds MVR import, a fixture-requirements editor/sidecar format, and
a "Check Inventory" substitute-finder. The hardening work in
`core/hardening.py` and `core/requirements_repository.py` is unusually
careful about the GDTF/MVR/requirements-file trust boundary (size limits,
XXE/entity rejection, compression-ratio bombs, regular-file/FIFO discipline,
atomic writes, strict schema validation with no coercion) and the test suite
exercises almost every edge named in the module docstrings.

Despite that care, one gap in the same threat model slipped through: the
recursive walk over a nested MVR scene graph (`core/mvr_repository.iter_fixtures`)
has no depth limit, unlike every other dimension of the MVR/GDTF pipeline
(byte size, compression ratio, XML entities), making it a plausible
crash/DoS vector for a crafted MVR file. I also found a misleading
user-facing message for an edge case the tests don't actually assert on
(unreferenced-only MVR), two cases where an `OSError` from `os.set_blocking`
would bypass this codebase's own "always wrap in a typed, friendly error"
rule, and a closeEvent timeout composition issue where two independently
"bounded" waits stack into an unbounded-feeling total.

## Critical Issues

### CR-01: Unbounded recursion depth walking a nested MVR scene graph (crash/DoS risk from untrusted file)

**File:** `src/gdtf_comparer/core/mvr_repository.py:103-125` (`iter_fixtures`), reached from `import_mvr` at `src/gdtf_comparer/core/mvr_repository.py:204-213`

**Issue:** `core/hardening.prevalidate_mvr_document` carefully bounds every
other dimension of an untrusted `.mvr` file before it is parsed — total
file size (`MAX_MVR_FILE_BYTES`), the scene XML's own size
(`MAX_GSD_XML_BYTES`), total uncompressed expansion/ratio
(`MAX_MVR_TOTAL_UNCOMPRESSED_BYTES`), and XXE/entity declarations
(`forbid_dtd`/`forbid_entities`/`forbid_external`). None of that bounds
*nesting depth*. `iter_fixtures` recurses once per level of
`<GroupObject>`/`<SceneObject>`/`<Truss>`/`<Support>`/`<VideoScreen>`/
`<Projector>`/nested-`<Fixture>` nesting, with no depth counter and no cap:

```python
def iter_fixtures(child_list: Optional[Any]) -> Iterator[Any]:
    if child_list is None:
        return
    for fixture in child_list.fixtures:
        yield fixture
        yield from iter_fixtures(getattr(fixture, "child_list", None))
    for name in _CHILD_NODE_LISTS:
        for node in getattr(child_list, name, None) or ():
            yield from iter_fixtures(getattr(node, "child_list", None))
```

A single `<GroupObject uuid="..."><ChildList>` open tag is roughly 60-80
bytes; `MAX_GSD_XML_BYTES` is 64 MB, so an attacker can fit on the order of
10^5-10^6 nesting levels well inside the existing size budget — far beyond
Python's default recursion limit (1000). pymvr's own XML-to-object
construction for `GeneralSceneDescription(...)` (inside the same
`import_mvr` try block, `mvr_repository.py:199`) is also presumably
recursive per nesting level, adding further C-stack depth before
`iter_fixtures` is even reached.

A plain `RecursionError` would be caught by the surrounding
`except Exception as exc: raise MVRParseError(...)` (mvr_repository.py:216-219)
and reported as a friendly error — that part is fine. The real risk is a
**native C-stack overflow**, which is not guaranteed to raise a catchable
Python exception and can segfault the process outright. This is exactly the
class of input-driven crash the rest of this module (and the Phase 1/5
RESEARCH notes it cites) was built to prevent, and it is reachable purely
through the structure of an otherwise-valid, size-compliant `.mvr` file —
no XXE, no zip bomb, no oversized file required.

**Fix:** Bound the walk's depth explicitly, independent of Python's own
recursion limit, e.g.:

```python
MAX_SCENE_NESTING_DEPTH = 64  # [ASSUMED] generous for any real show file

def iter_fixtures(child_list, _depth: int = 0) -> Iterator[Any]:
    if child_list is None:
        return
    if _depth > MAX_SCENE_NESTING_DEPTH:
        raise MVRUnsafeFileError(..., "it was rejected for safety reasons (too deeply nested).")
    for fixture in child_list.fixtures:
        yield fixture
        yield from iter_fixtures(getattr(fixture, "child_list", None), _depth + 1)
    for name in _CHILD_NODE_LISTS:
        for node in getattr(child_list, name, None) or ():
            yield from iter_fixtures(getattr(node, "child_list", None), _depth + 1)
```

or convert the walk to an explicit stack/queue (iterative, not recursive) so
depth is bounded only by available heap, not by the C call stack. Either
way, this should be exercised by a test that builds a few-thousand-level
deep `<GroupObject>` chain and asserts a friendly `MVRValidationError`/
`MVRUnsafeFileError` rather than a crash.

## Warnings

### WR-01: `import_summary_message` mislabels an "all fixtures unreferenced" MVR as a failed import

**File:** `src/gdtf_comparer/core/mvr_repository.py:269-272` (branch selection), `:34` (`NONE_IMPORTED_TEMPLATE`), `:289-291` (unreferenced clause)

**Issue:** When an MVR's scene walk finds fixtures but *every* one of them
has no `<GDTFSpec>` at all (so `fixture_types == ()`, `skipped == ()`, and
`unreferenced_fixture_count == total_fixture_count > 0`), the branch at
line 271 falls into `NONE_IMPORTED_TEMPLATE`:

```python
if result.total_fixture_count == 0:
    message = NO_FIXTURES_TEMPLATE.format(file=result.file_name)
elif not result.fixture_types:
    message = NONE_IMPORTED_TEMPLATE.format(file=result.file_name)  # <-- reached here too
else:
    ...
```

`NONE_IMPORTED_TEMPLATE` reads "None of the fixture types in '{file}' could
be imported." — which asserts that fixture types *were referenced and
failed to import*. In this edge case no fixture type was ever referenced at
all (`skipped` is also empty), so the sentence is factually wrong. The
final message ends up reading e.g. "None of the fixture types in
'practical.mvr' could be imported. 1 fixture in the show names no GDTF file
and is left out." — confusing for the non-technical lighting professional
this message is written for (it reads as if an import attempt failed, when
nothing was ever attempted).

`tests/core/test_mvr_repository.py::test_fixture_without_gdtf_spec_is_counted`
only asserts a substring match (`"1 fixture in the show names no GDTF
file" in summary`), so it doesn't catch the misleading prefix — this gap
currently has no regression coverage.

**Fix:** Distinguish "nothing was ever referenced" from "referenced types
failed," e.g.:

```python
elif not result.fixture_types and not result.skipped:
    message = f"'{result.file_name}' has no fixtures that reference a GDTF file."
elif not result.fixture_types:
    message = NONE_IMPORTED_TEMPLATE.format(file=result.file_name)
```

and add a test asserting the full message text (not just a substring) for
the unreferenced-only case.

### WR-02: `os.set_blocking` failures bypass the typed-error contract in two hardening paths

**File:** `src/gdtf_comparer/core/hardening.py:157-158` (`_read_file_bytes`), `src/gdtf_comparer/core/requirements_repository.py:239-240` (`_read_requirements_bytes`)

**Issue:** Both functions carefully wrap every other OS-level failure
(`os.open`, `os.fstat`, `os.fdopen`, the read itself) in a `try/except
OSError` that raises the module's typed, friendly error. The one call that
is *not* wrapped is the one in between:

```python
if getattr(os, "O_NONBLOCK", 0):
    os.set_blocking(fd, True)   # <-- can raise OSError, uncaught here

try:
    handle = os.fdopen(fd, "rb")
except OSError as exc:
    raise kind.validation_error(...) from exc
```

If `os.set_blocking` raises (e.g. `EBADF` from some platform/fd edge case),
the exception propagates as a raw, untyped `OSError` instead of
`GDTFValidationError`/`RequirementsFileError`. The surrounding `finally:
if owns_fd: os.close(fd)` still runs (no fd leak), but every caller up the
stack (including `gui/worker.py`'s `except GDTFError`/`except
SubstitutionError` branches) is written assuming only typed errors escape
this layer — a raw `OSError` here falls through to each worker's generic
`except Exception` fallback instead of the intended friendly message, and
would raise completely unguarded if ever called synchronously outside a
worker. Given how deliberately every other branch here is wrapped, this
looks like an oversight rather than a decision.

**Fix:** Wrap the same call the same way:

```python
if getattr(os, "O_NONBLOCK", 0):
    try:
        os.set_blocking(fd, True)
    except OSError as exc:
        raise kind.validation_error(path, f"the file could not be read ({exc.strerror}).") from exc
```

(mirror in `requirements_repository._read_requirements_bytes` using
`_unreadable(exc)`).

### WR-03: Sequential closeEvent waits can block the GUI far longer than any single timeout constant suggests

**File:** `src/gdtf_comparer/gui/substitution_window.py:417-428` (`closeEvent`), `src/gdtf_comparer/gui/main_window.py:920-944` (`closeEvent`)

**Issue:** `SubstitutionWindow.closeEvent` waits for its import thread and
scan thread **sequentially**, each up to `SUBSTITUTION_CLOSE_WAIT_TIMEOUT_MS`
(3000 ms):

```python
def closeEvent(self, event) -> None:
    for thread in (self._import_thread, self._scan_thread):
        if thread is not None:
            thread.quit()
            finished = thread.wait(SUBSTITUTION_CLOSE_WAIT_TIMEOUT_MS)
            ...
```

Nothing in the GUI prevents an import and a scan from being in flight at
the same time (they are independent tabs/threads with no mutual-exclusion
between them, only within each kind) — a stuck network-mounted MVR import
on tab 1 and a stuck inventory-folder scan on tab 2 at the same time is a
realistic scenario this phase's own `test_close_during_import_returns_promptly`-style
tests don't cover. In that case this window alone blocks the GUI thread for
up to 2 × 3000 ms = 6000 ms. `MainWindow.closeEvent` then closes the
substitution window first and *afterwards* performs its own bounded wait on
its own comparison thread (`CLOSE_WAIT_TIMEOUT_MS`, another 3000 ms),
pushing the worst-case total to ~9000 ms — far beyond what every one of the
"never blocks the GUI thread for more than CLOSE_WAIT_TIMEOUT_MS" comments
elsewhere in this codebase (e.g. `app.py:52-65`, `main_window.py:923-927`)
leads a reader to expect from a single named constant.

**Fix:** Either wait on both substitution threads concurrently (e.g. quit
both first, then wait on each with a *shared* deadline computed once up
front, not a fresh timeout per thread), or document explicitly that the
real worst case is the sum of all independently-waited threads across both
windows, and size the constants with that total in mind.

## Info

### IN-01: Inconsistent error-to-message extraction between workers

**File:** `src/gdtf_comparer/gui/worker.py:47,80,115`

**Issue:** `ComparisonWorker` and `MVRImportWorker` emit
`exc.user_message` explicitly; `CandidateScanWorker` emits `str(exc)`
instead (line 115). These happen to be equivalent today because every
`GDTFError`/`SubstitutionError.__str__` returns `self.user_message`, so
this is not a functional bug, but it's an easy invariant to break silently
if a future subclass overrides `__str__` for debugging without updating
this one call site.

**Fix:** Use `exc.user_message` consistently in `CandidateScanWorker.run`
for the same reason the other two workers do.

---

_Reviewed: 2026-10-24T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
