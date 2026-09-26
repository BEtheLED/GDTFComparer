---
phase: 01-foundation-rebuild
reviewed: 2026-09-26T13:46:29Z
depth: standard
files_reviewed: 27
files_reviewed_list:
  - .gitignore
  - pyproject.toml
  - README.md
  - src/gdtf_comparer/__init__.py
  - src/gdtf_comparer/app.py
  - src/gdtf_comparer/core/__init__.py
  - src/gdtf_comparer/core/comparator.py
  - src/gdtf_comparer/core/errors.py
  - src/gdtf_comparer/core/extract.py
  - src/gdtf_comparer/core/hardening.py
  - src/gdtf_comparer/core/models.py
  - src/gdtf_comparer/core/repository.py
  - src/gdtf_comparer/gui/__init__.py
  - src/gdtf_comparer/gui/main_window.py
  - src/gdtf_comparer/gui/table_model.py
  - src/gdtf_comparer/gui/theme.py
  - src/gdtf_comparer/gui/worker.py
  - tests/conftest.py
  - tests/core/test_comparator.py
  - tests/core/test_extract.py
  - tests/core/test_hardening.py
  - tests/core/test_repository.py
  - tests/gui/test_error_handling.py
  - tests/gui/test_namespaced_rows.py
  - tests/gui/test_theme.py
  - tests/test_architecture.py
  - tests/test_fixture_builder.py
  - tests/test_walking_skeleton.py
findings:
  critical: 1
  warning: 2
  info: 3
  total: 6
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-09-26T13:46:29Z
**Depth:** standard
**Files Reviewed:** 27
**Status:** issues_found

## Summary

This phase rebuilds GDTF Comparer as a PySide6 app with a Qt-free `core`
layer (parsing, hardening, comparison) and a thin `gui` layer. The
architecture is clean and well enforced (AST-based import-boundary tests
correctly forbid `gui` from touching `pygdtf`/`zipfile`/`defusedxml`, and
forbid `core` from touching Qt or writing to disk). The RELI-02 hardening
pipeline (size caps, compression-ratio/zip-bomb checks, `defusedxml`
XXE/entity rejection, capped reads) is well designed and I could not find a
bypass: the exact bytes validated by `prevalidate_gdtf()` are the exact
bytes handed to `pygdtf`, so there is no TOCTOU/confused-deputy gap between
the two independent zip/XML parses.

The one significant defect is in `core/extract.py`: the code's `None`
checks for individual optional GDTF attributes (BeamAngle, FieldAngle,
PowerConsumption, LuminousFlux, ColorTemperature, BeamType, Weight) are
dead code in practice, because the installed `pygdtf==1.4.5` never returns
`None` for these fields — it silently backfills its own library defaults
(e.g. `BeamAngle` → `25.0`, `Weight` → `0.0`, `BeamType` → `"Wash"`) when
the XML attribute/element is omitted. I reproduced this directly against
the pinned dependency (see CR-01). This is a correctness bug that strikes
at the app's stated core value ("see which attributes actually differ"):
a fixture that never declares `BeamAngle` is displayed and compared as if
it declared `25.0`, and two fixtures that both omit `Weight` compare as
"identical, 0.0 kg" instead of both showing `N/A`. No test in the suite
exercises this exact scenario (all existing "N/A" tests cover the case
where an entire geometry/model node is absent, not the case where the node
is present but an individual attribute is omitted from it), which is why
it went undetected.

Two further robustness gaps and three minor/info items are listed below.

## Critical Issues

### CR-01: Omitted GDTF attribute values silently become pygdtf's spec defaults instead of "N/A"

**File:** `src/gdtf_comparer/core/extract.py:124-155`
**Issue:**

`extract_attributes()` defends against a value being genuinely absent with
`getattr(..., None)` followed by an `is None` check, e.g.:

```python
raw_weight = getattr(properties, "weight", None)
if raw_weight is not None:
    weight = float(raw_weight)
```

and, for every `BEAM_ATTRIBUTES` field:

```python
raw_value = getattr(node, field_name, None)
if gdtf_name == "BeamType":
    value: AttributeValue = raw_value.value if raw_value is not None else None
elif raw_value is None:
    value = None
else:
    value = float(raw_value)
```

This assumes pygdtf leaves a field unset (`None`) when the corresponding
XML attribute/element is omitted. It does not. Verified directly against
the pinned `pygdtf==1.4.5`:

- `pygdtf.properties.Properties.weight` defaults to `0` in `__init__` and
  is only reassigned if a `<Weight>` element is found — never set to
  `None`.
- `pygdtf.geometries.GeometryBeam` defaults `beam_angle=25.0`,
  `field_angle=25.0`, `power_consumption=1000`, `luminous_flux=10000`,
  `color_temperature=6000`, and `beam_type=BeamType(None)` (whose `.value`
  itself defaults to `"Wash"`) — none of these become `None` either.

Reproduction (a `<Beam Name="Beam"/>` with no other attributes declared):

```
AttributeKey(category='Beam', element_path='Head/Beam', attribute='BeamAngle') 25.0
AttributeKey(category='Beam', element_path='Head/Beam', attribute='FieldAngle') 25.0
AttributeKey(category='Beam', element_path='Head/Beam', attribute='PowerConsumption') 1000.0
AttributeKey(category='Beam', element_path='Head/Beam', attribute='LuminousFlux') 10000.0
AttributeKey(category='Beam', element_path='Head/Beam', attribute='ColorTemperature') 6000.0
AttributeKey(category='Beam', element_path='Head/Beam', attribute='BeamType') Wash
```

and a `<Properties><Weight/></Properties>` block with the `<Weight>`
element omitted entirely yields `Weight = 0.0`, not `None`.

Consequences for the shipped feature:
- Two real fixtures that both simply never bothered to declare
  `BeamAngle`/`Weight`/etc. will be reported as **identical** on that row,
  even though neither manufacturer specified a value.
- A fixture missing weight data is displayed to the lighting/AV
  professional as **"0"** (implying "this fixture weighs nothing"),
  not "N/A" (implying "no data").
- The `is None` branches are unreachable dead code as written, giving a
  false sense that the "N/A" contract (proven only for the
  whole-node-absent case in `test_missing_key_is_none_and_differs`) also
  covers the whole-attribute-absent case. It does not, and no test catches
  it.

**Fix:** Either (a) accept and document that GDTF-spec default values are
the "effective" value and stop implying `None`-on-omission is supported
for these fields (drop the dead `is None` branches, update the module
docstring), or (b) actually detect omission by inspecting the underlying
XML node's `.attrib` before it is coerced by pygdtf (or track presence
separately, e.g. via a lightweight pre-pass over the same validated bytes
already available in `prevalidate_gdtf()`/`read_gdtf_bytes()`) so a
genuinely-omitted `BeamAngle`/`Weight`/etc. can still be shown as `N/A`
independent of pygdtf's own default-substitution. Whichever is chosen, add
a regression test that builds a `<Beam>`/`<Properties>` with the attribute
omitted (not just the whole node omitted) and asserts the resulting
`AttributeKey` value/`format_value()` output.

## Warnings

### WR-01: `closeEvent` can hang the whole app indefinitely with no timeout

**File:** `src/gdtf_comparer/gui/main_window.py:226-231`
**Issue:**

```python
def closeEvent(self, event) -> None:
    """Quit and wait for any running worker thread before closing (D-14)."""
    if self._thread is not None:
        self._thread.quit()
        self._thread.wait()
    super().closeEvent(event)
```

`QThread.wait()` is called with no timeout, on the GUI thread, while the
window is closing. `ComparisonWorker.run()` (via `compare_files()` →
`FixtureRepository.load()` → `hardening.read_gdtf_bytes()`) does a plain
blocking `open(path, "rb")` / `handle.read(limit + 1)` with no timeout of
its own (`src/gdtf_comparer/core/hardening.py:46-90`). If a selected path
is a special file (a named pipe/FIFO with no writer, a stalled network
mount, a device file, etc.) that never completes its read, the worker
thread never finishes, `thread.wait()` blocks forever, and the entire
application becomes unresponsive/unkillable from the UI (no window close,
no way to cancel). This is a narrow but real input-driven denial-of-service
against the app itself, since the file path comes directly from a file
picker the user (or a malicious/crafted directory) controls.

**Fix:** Call `self._thread.wait(some_timeout_ms)` and fall back to
`terminate()`/force-hide the window (or simply proceed with `event.accept()`
regardless) if the timeout elapses, so closing the window is never allowed
to hang forever. Alternatively/also, add a timeout guard around the file
read in `hardening.read_gdtf_bytes()` for non-regular files.

### WR-02: No cross-check between the target file and the comparison list

**File:** `src/gdtf_comparer/gui/main_window.py:133-146`
**Issue:** `add_compare_files()` only dedupes a new path against
`self.compare_files`; it never checks whether the path is also the current
`self.target_file`. A user can select the same file as both target and a
comparison, silently producing a comparison result where every row's
comparison value trivially equals the target (no diffs at all), with no
indication to the user that they just compared a file against itself.
**Fix:** Skip (or warn on) adding a path to `compare_files` that equals
`self.target_file`, and/or re-validate when `set_target_file()` is called
after files were already added.

## Info

### IN-01: Dead/unused public members

**File:** `src/gdtf_comparer/core/models.py:93-96` (`ComparisonRow.any_differs`),
`src/gdtf_comparer/gui/theme.py:86-89` (`OsThemeFollower.current_theme`)
**Issue:** Neither property has any caller or test anywhere in `src/` or
`tests/` (confirmed via full-repo search). They may be intentional
scaffolding for a later diff-highlighting phase, but as committed they are
unreferenced code.
**Fix:** Either wire them into the current UI/tests or remove until the
phase that needs them lands, to keep dead surface area from accumulating.

### IN-02: README setup instructions are stricter than the actual requirement

**File:** `README.md:17,24`
**Issue:** Setup instructions say `python3.12 -m venv .venv`, while
`pyproject.toml:10` declares `requires-python = ">=3.11"` and
`tests/test_fixture_builder.py:18` only asserts `sys.version_info >= (3, 11)`.
A contributor with only Python 3.11 installed could be misled into thinking
the project requires 3.12.
**Fix:** Either state the actual floor (`python3.11+`) or bump
`requires-python` to match `3.12` if 3.12 is really required.

### IN-03: `extract.py`'s BeamType `None` branch is unreachable

**File:** `src/gdtf_comparer/core/extract.py:139-140`
**Issue:** `getattr(node, "beam_type", None)` never returns `None` in
practice — `GeometryBeam.beam_type` is always a `BeamType` enum-wrapper
instance (defaulting to `BeamType(None)`, whose own `.value` defaults to
`"Wash"`, per pygdtf 1.4.5), so `raw_value is not None` is always `True`
and the `else None` branch on line 140 can never execute. Related to CR-01;
listed separately here as a pure dead-code/readability note in case CR-01
is fixed by a narrower patch that leaves this line untouched.
**Fix:** Remove or simplify once CR-01 is addressed; if CR-01 is fixed via
XML-presence detection, this branch becomes meaningful again and should be
kept but its precondition documented (`raw_value` itself is never `None`
from pygdtf — only the *replacement* presence-check will ever produce
`None` here).

---

_Reviewed: 2026-09-26T13:46:29Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
