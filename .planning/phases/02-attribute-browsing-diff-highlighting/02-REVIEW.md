---
phase: 02-attribute-browsing-diff-highlighting
reviewed: 2026-10-11T00:00:00Z
depth: standard
files_reviewed: 14
files_reviewed_list:
  - src/gdtf_comparer/core/comparator.py
  - src/gdtf_comparer/core/extract.py
  - src/gdtf_comparer/core/models.py
  - src/gdtf_comparer/gui/attribute_picker.py
  - src/gdtf_comparer/gui/main_window.py
  - src/gdtf_comparer/gui/table_model.py
  - src/gdtf_comparer/gui/theme.py
  - tests/conftest.py
  - tests/core/test_comparator.py
  - tests/core/test_extract.py
  - tests/gui/test_attribute_picker.py
  - tests/gui/test_attribute_selection.py
  - tests/gui/test_diff_highlighting.py
  - tests/gui/test_differences_only_toggle.py
  - tests/gui/test_dmx_attributes.py
findings:
  critical: 1
  warning: 2
  info: 1
  total: 4
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-10-11T00:00:00Z
**Depth:** standard
**Files Reviewed:** 14
**Status:** issues_found

## Summary

Reviewed the comparator/extraction core, the attribute picker + main window +
table model GUI layer, and the Phase 02 test suite at standard depth. The
existing test suite (100 tests across the core/GUI files in scope) passes in
full, and the namespaced-attribute extraction, cross-file beam positioning,
presence-vs-default handling, attribute selection filtering, and diff
highlighting are all carefully built and well covered by tests for the paths
they exercise.

The adversarial pass found one BLOCKER that the existing test suite does not
exercise: nothing stops the user from changing the target/comparison file
selection while a comparison is still running, and `on_comparison_ready`
applies whatever result the worker returns without checking it still matches
the current file selection -- so the results table and status bar can
silently show a stale comparison. I built and ran a reproduction (removed
afterward, not part of this submission) that confirms this lands observable,
incorrect state in `MainWindow`. Two further WARNING-level correctness/display
gaps were found and confirmed the same way, plus one low-priority Info item.

## Critical Issues

### CR-01: A comparison result can be applied after the user has already changed the file selection, silently showing a stale comparison

**File:** `src/gdtf_comparer/gui/main_window.py:547-599`

**Issue:** `run_comparison()` only disables `self.run_button` while a worker
is in flight (`main_window.py:560`, re-enabled only in `_on_thread_finished`,
`main_window.py:580-589`). `self.target_button`, `self.add_button` and
`self.remove_button` are never disabled or otherwise guarded during a run
(confirmed by grep: the only `setEnabled` calls in the file are for
`run_button` and the profile combo/menu, `main_window.py:560,589,930,939,
967-969`). A user is therefore free to call `select_target_file()` /
`select_compare_files()` / `remove_selected_files()` while the worker thread
from an earlier `run_comparison()` call is still running.

When that in-flight worker later emits `comparison_ready`,
`on_comparison_ready()` (`main_window.py:591-599`) unconditionally does:

```python
def on_comparison_ready(self, result: ComparisonResult) -> None:
    self.table_model.set_result(result)
    self.attribute_picker.set_catalog(attribute_catalog(result))
    self._apply_attribute_selection()
```

There is no check anywhere in this path that `result.target`/
`result.comparisons` still correspond to `self.target_file`/
`self.compare_files` (or to what `self.compare_list` currently displays).
`_update_match_indicators()` happens to defend itself against this
(`main_window.py:687-731`, it resets every dot to "unknown" when
`compare_list` and `result.comparisons` disagree by count or path), but
nothing else does: the results table's rows, its per-file column headers
(`table_model.py::_header_label`/`_header_tooltip`), and the status bar
message built from `result.target.file_name` / `len(result.comparisons)`
(`main_window.py:822-824`) all go ahead and render the *old* comparison,
while the Files panel (target field, "Compare with" list) already shows the
*new* selection. A lighting/AV professional reading the table has no way to
tell the numbers on screen no longer correspond to the files listed above
them -- for a tool whose entire value proposition is "see which attributes
actually differ," this is a direct risk of an incorrect decision made from
stale data.

I verified this is reachable (not just theoretical) with the following
reproduction, run against the current code and then removed (it is not part
of this submission):

```python
def test_stale_result_lands_on_table_after_user_changes_files(qtbot, make_gdtf):
    old_target = make_gdtf("old_target.gdtf", name="Old Target")
    old_compare = make_gdtf("old_compare.gdtf", name="Old Compare")
    new_target = make_gdtf("new_target.gdtf", name="New Target")
    new_compare = make_gdtf("new_compare.gdtf", name="New Compare")

    window = MainWindow()
    qtbot.addWidget(window)

    # Simulate a worker "in flight" for the old selection.
    stale_result = compare_files(str(old_target), [str(old_compare)])

    # User changes their mind before that worker finishes -- nothing stops them.
    window.set_target_file(str(new_target))
    window.add_compare_files([str(new_compare)])

    # The stale worker now delivers its result, exactly as
    # ComparisonWorker.comparison_ready -> on_comparison_ready would.
    window.on_comparison_ready(stale_result)

    assert window.target_edit.text() == str(new_target)              # Files panel: new
    assert window.table_model.result() is stale_result                # Table: OLD result
    assert "old_target" in window.statusBar().currentMessage()        # status bar: OLD target
```

This passed, confirming the table and status bar end up describing
`old_target.gdtf`/`old_compare.gdtf` while the Files panel already shows
`new_target.gdtf`/`new_compare.gdtf`.

**Fix:** Either disable `target_button`/`add_button`/`remove_button` (and
ideally the whole `files_group`) for the duration of a run (matching the
existing `run_button` discipline, `main_window.py:560,589`), or track a
monotonically increasing "request generation" set when `run_comparison()`
starts and compare it in `on_comparison_ready`/`on_comparison_failed`,
discarding (and logging) any result whose generation doesn't match the
current one:

```python
def run_comparison(self) -> None:
    ...
    self._comparison_generation += 1
    generation = self._comparison_generation
    worker = ComparisonWorker(self.target_file, list(self.compare_files))
    worker.comparison_ready.connect(
        lambda result: self.on_comparison_ready(result, generation)
    )
    ...

def on_comparison_ready(self, result: ComparisonResult, generation: int) -> None:
    if generation != self._comparison_generation:
        return  # stale: file selection has moved on since this run started
    ...
```

## Warnings

### WR-01: Identical NaN values on both sides are reported as a difference

**File:** `src/gdtf_comparer/core/models.py:177-195`

**Issue:** `values_equal()` special-cases `None`/`None` as equal (vacuous
truth: "neither file declares this") but does not special-case NaN. Python's
`math.isclose(nan, nan, ...)` is `False` by definition (NaN is never close to
anything, including itself), so when two files declare the exact same
not-a-number value for a numeric attribute, `compare()` reports
`differs=True` and the cell gets highlighted as a difference, even though
both files say the identical thing. GDTF numeric attributes are manufacturer
XML text (`BeamAngle="NaN"` parses successfully via pygdtf/Python's
`float()`), and the test suite already exercises other malformed-value paths
(`test_declared_malformed_values_follow_pygdtf`,
`test_declared_physical_unit_none_is_not_na`) as a class of input this code
is expected to tolerate gracefully -- NaN floats are the same class of input
and currently produce a false-positive diff. Verified with:

```python
def test_nan_beam_angle_shows_as_differing_even_when_both_sides_are_nan(make_gdtf):
    geometries_xml = '<Geometry Name="Head"><Beam Name="Beam" BeamAngle="NaN"/></Geometry>'
    target = make_gdtf("target.gdtf", geometries_xml=geometries_xml)
    comparison = make_gdtf("comparison.gdtf", geometries_xml=geometries_xml)
    result = compare_files(str(target), [str(comparison)])
    row = next(r for r in result.rows if r.key.attribute == "BeamAngle")
    assert row.differs == (True,)  # both sides are NaN, yet this is True
```

**Fix:** Add an explicit NaN-equality branch before the `math.isclose` call:

```python
if isinstance(a, (int, float)) and isinstance(b, (int, float)):
    a_float, b_float = float(a), float(b)
    if math.isnan(a_float) and math.isnan(b_float):
        return True
    return math.isclose(a_float, b_float, rel_tol=1e-9, abs_tol=1e-12)
```

### WR-02: Two comparison files can render with identical, indistinguishable column headers

**File:** `src/gdtf_comparer/gui/table_model.py:30-62`

**Issue:** `_value_column_labels()` falls back to `model.file_name` (the
basename) whenever a fixture's `name` is blank or collides (case/whitespace
folded) with another compared fixture's name. The fallback key is only the
*basename*, not the full path, so two comparison files that both have a
blank/colliding `name` **and** share a basename (e.g. two different
manufacturers' revisions both exported as `fixture.gdtf` into different
folders, a plausible real workflow for this app's "compare downloaded
revisions" use case) end up with two value columns headered with the exact
same text -- and since `UppercaseHeaderProxyModel` uppercases both
identically, there is nothing in the header row (only the per-column tooltip,
which requires hovering) to tell the two apart. Verified with:

```python
def test_duplicate_basenames_from_different_dirs_get_identical_headers(tmp_path, make_gdtf):
    # comp1 = tmp_path/a/fixture.gdtf, comp2 = tmp_path/b/fixture.gdtf, both name=""
    result = compare_files(str(target), [str(comp1), str(comp2)])
    model = ComparisonTableModel()
    model.set_result(result)
    header1 = model.headerData(ComparisonTableModel.COL_TARGET + 1, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
    header2 = model.headerData(ComparisonTableModel.COL_TARGET + 2, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
    assert header1 == header2 == "fixture.gdtf"  # indistinguishable in the header row
```

**Fix:** When even the basename collides, disambiguate further -- e.g.
append the parent directory name, or an ordinal suffix ("fixture.gdtf (1)" /
"fixture.gdtf (2)") -- rather than letting the final fallback collide too.

## Info

### IN-01: `format_value` can fall back to scientific notation for large magnitudes

**File:** `src/gdtf_comparer/core/models.py:157-174`

**Issue:** `format(value, ".10g")` switches to scientific notation once a
float needs more than 10 significant digits to render in fixed form (e.g.
`format_value(12345678901.0) == "1.23456789e+10"`), which the docstring
("a compact decimal string for float") doesn't anticipate. In practice GDTF
numeric attributes (beam angle, power consumption, weight, luminous flux)
stay well under this threshold, so this is unlikely to be hit with real
fixture data, but it is a latent display inconsistency worth a one-line
docstring caveat or an explicit format override if it is ever reached.

**Fix:** Either document the scientific-notation fallback explicitly in the
docstring, or guard against it (e.g. `format(value, "f").rstrip("0").rstrip(".")`
for a fixed-point-only guarantee) if large magnitudes are ever expected.

---

_Reviewed: 2026-10-11T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
