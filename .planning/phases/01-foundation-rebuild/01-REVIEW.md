---
phase: 01-foundation-rebuild
reviewed: 2026-09-28T03:30:45Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - src/gdtf_comparer/gui/main_window.py
  - src/gdtf_comparer/gui/table_model.py
  - tests/gui/test_table_headers.py
  - tests/test_walking_skeleton.py
findings:
  critical: 1
  warning: 1
  info: 1
  total: 3
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-09-28T03:30:45Z
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Reviewed the gap-closure diff (plan 01-09) that fixed two UAT bugs: header text
clipping under qt-material's CSS uppercase transform (G-01-1, fixed via
`UppercaseHeaderProxyModel`) and long-filename headers forcing horizontal
scroll (G-01-2, fixed via `_value_column_labels` name-preference plus
`MAX_COLUMN_WIDTH_PX` capping/eliding in `_fit_columns_to_contents`).

`UppercaseHeaderProxyModel` itself is correct and well-targeted: it measures
exactly what qt-material paints, and I confirmed by instrumenting the real
`QHeaderView`/`QTableView` that its interaction with `setStretchLastSection`
behaves exactly as the docstring claims (the last section is always
re-stretched to fill remaining space regardless of the cap, so the loop is a
harmless no-op there).

However, the width-cap loop in `_fit_columns_to_contents` is not scoped to
"value columns" the way its own docstring and `MAX_COLUMN_WIDTH_PX` comment
claim — it caps every column, including `Category`/`Element`/`Attribute`.
Because the table view's own cell text-elide mode was never changed (only the
*header's* elide mode was set to `ElideMiddle`), this reintroduces a
readability defect in the `Element` column that has nothing to do with either
G-01-1 or G-01-2 and can make two genuinely different rows display identical
text. I reproduced this empirically (see CR-01). I also reproduced that the
G-01-2 "no horizontal scrollbar" fix only holds for the single-comparison
case the tests exercise; it does not generalize to the product's core
"compare against any number of files" use case (see WR-01).

## Critical Issues

### CR-01: Column-width cap is applied to fixed columns too, and can make two different Element paths render as identical text

**File:** `src/gdtf_comparer/gui/main_window.py:299-312`
**Issue:**

`_fit_columns_to_contents` loops over *every* header section:

```python
self.table_view.resizeColumnsToContents()
header = self.table_view.horizontalHeader()
for section in range(header.count()):
    if header.sectionSize(section) > MAX_COLUMN_WIDTH_PX:
        header.resizeSection(section, MAX_COLUMN_WIDTH_PX)
```

but the surrounding comment and the `MAX_COLUMN_WIDTH_PX` docstring both
describe this as capping "a value column" (i.e. `COL_TARGET` and later),
sized specifically for `"TARGET: " + a fixture name`. `COL_ELEMENT`
(`table_model.py`) displays `AttributeKey.element_label`, which per
`core/models.py:29` is "the full path to the owning element (e.g. a geometry
path...)" — an unbounded, hierarchical string (e.g.
`"Base -> Yoke -> Head -> LampHousing -> LensAssembly -> DiffuserFilterWheel"`)
that has nothing to do with either G-01-1 or G-01-2.

I reproduced this with a real `MainWindow` and a single long element path:
before this diff, `resizeColumnsToContents()` alone sized that column to its
natural content width (476 px in my repro); after this diff,
`_fit_columns_to_contents` clamps it to `MAX_COLUMN_WIDTH_PX` (280 px),
identically to how a value column is clamped.

This alone would just be a readability regression, but it compounds with a
second gap: only the **header's** elide mode was changed
(`self.table_view.horizontalHeader().setTextElideMode(Qt.TextElideMode.ElideMiddle)`,
line 143). `QTableView`'s own (cell) `textElideMode` is untouched and
defaults to `Qt.TextElideMode.ElideRight` (confirmed: a fresh `QTableView()`
reports `TextElideMode.ElideRight`). So once the `Element` column is capped
below its natural width, cell text is elided from the **right**, not the
middle.

Concretely: two comparison rows whose element paths share a long common
prefix and differ only near the end (a very ordinary shape for nested GDTF
geometry, e.g. `"...Head -> Lamp1"` vs `"...Head -> Lamp2"`) will render with
**identical visible text** in the `Element` column once that shared prefix
alone exceeds ~280 px, because both get right-elided at the same point. That
directly contradicts the application's stated core value ("see which
attributes actually differ" — and, via this column, *where*): the UI can now
show two different geometry elements as indistinguishable. The full path is
still recoverable via the cell tooltip (`ComparisonTableModel.data`,
`ToolTipRole` for `COL_ELEMENT`), but nothing prompts a user to hover when
the two truncated strings look identical and non-suspicious.

**Fix:** Scope the cap to value columns only, matching what the docstring
already claims:

```python
def _fit_columns_to_contents(self) -> None:
    self.table_view.resizeColumnsToContents()
    header = self.table_view.horizontalHeader()
    for section in range(ComparisonTableModel.COL_TARGET, header.count()):
        if header.sectionSize(section) > MAX_COLUMN_WIDTH_PX:
            header.resizeSection(section, MAX_COLUMN_WIDTH_PX)
```

If capping `Element` is still desired for extreme geometry-path lengths, also
set `self.table_view.setTextElideMode(Qt.TextElideMode.ElideMiddle)` so cell
elision matches the header's, and add a regression test with two rows whose
element paths differ only after the cap width to prove they remain visually
distinguishable.

## Warnings

### WR-01: G-01-2's "no horizontal scrollbar" fix only holds for the single-comparison case the tests cover

**File:** `src/gdtf_comparer/gui/main_window.py:46-52, 299-312`
**Issue:** `MAX_COLUMN_WIDTH_PX`'s own comment says it is "sized ... to keep a
target plus **one** comparison inside the default 1000 px window with no
horizontal scrollbar," and `test_long_headers_are_capped_and_elided` /
`test_fixed_headers_fit_uppercased_labels` only ever construct a
`ComparisonResult` with exactly one comparison file. That is a narrower case
than the bug this gap-closure plan was meant to fix (01-UAT.md G-01-2: "long
GDTF filenames ... forcing horizontal scroll") and narrower than the
product's stated core value ("pick a target GDTF file and **any number of**
comparison files").

I reproduced the original scrollbar bug still occurring post-fix with a
realistic (if generous) multi-file comparison: target + 3 comparison files
with ~70-character fixture names at the default 1000×650 window produces
`horizontalScrollBar().maximum() == 4` (i.e. scrolling is required again),
because only the single *last* column is stretch-exempt from the cap — every
other value column still consumes up to 280 px each, and 3+ of those plus the
fixed columns exceed the default viewport width. (With 3 more realistically
short names, e.g. `"Martin MAC Aura XB"`, no scrollbar is needed — so the
regression is real but name-length/column-count dependent, not universal.)

Because the only test added for this fix (`test_long_headers_are_capped_and_elided`)
exercises just one comparison file, it does not actually verify the
UAT-reported scenario generalizes, and gives false confidence that G-01-2 is
fully closed.

**Fix:** Either (a) explicitly document this as a known, accepted limit (e.g.
rename/re-scope the UAT item to "target + 1 comparison" and note that N>2
comparisons with long names may still require horizontal scrolling), or (b)
make the cap adaptive to the number of value columns and available viewport
width (e.g. `min(MAX_COLUMN_WIDTH_PX, available_width / num_value_columns)`),
and add a test with 3+ comparison files with realistic (~30-50 char) fixture
names asserting no scrollbar is required.

## Info

### IN-01: Header tooltip doesn't strip whitespace-only/padded names the way the header label does

**File:** `src/gdtf_comparer/gui/table_model.py:181-183`
**Issue:** `_value_column_labels` strips `model.name` before using it as the
header label (`model.name.strip()`), but `_header_tooltip` uses the raw,
unstripped `model.name`:

```python
if model.manufacturer.strip():
    return f"{model.manufacturer} {model.name} — {model.source_path}"
return f"{model.name} — {model.source_path}"
```

For a fixture whose name is only whitespace (covered by
`test_colliding_or_blank_names_fall_back_to_file_names`'s `blank` fixture,
`name="   "`, `manufacturer=""`), the header label correctly falls back to
the file name, but the tooltip renders as `"    — /fixtures/blank.gdtf"`
(literal leading spaces before the em dash) instead of a clean
`"blank.gdtf — /fixtures/blank.gdtf"`-style message. Purely cosmetic, no
functional impact.

**Fix:** Use `model.name.strip()` in `_header_tooltip` as well, and consider
falling back to `model.file_name` there too when the stripped name is empty,
for consistency with the header label.

---

_Reviewed: 2026-09-28T03:30:45Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
