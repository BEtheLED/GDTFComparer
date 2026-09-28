# Debug Session: G-01-2 — Long filename column headers hard to read

## Symptom
Per-file column headers show the full GDTF filename (manufacturer@model@revision.gdtf). Headers appear clipped at the start ("TARG…", "…Bea…") in the screenshot; a horizontal scrollbar is present.

## Root Cause
Not an alignment/anchor bug (no `setDefaultAlignment` or anchor override anywhere; qt-material's `QHeaderView::section` CSS only sets color/background/padding/`text-transform: uppercase`). It's genuine horizontal-scroll clipping of an oversized column:

- `src/gdtf_comparer/gui/table_model.py:97-112` (`_header_label`) builds `f"Target: {self._result.target.file_name}"` for the target column and the raw `file_name` verbatim for each compare column, with no truncation/elision.
- `src/gdtf_comparer/core/models.py:75-78` — `FixtureModel.file_name` is `os.path.basename(source_path)`, i.e. the full `Manufacturer@Model@Revision.gdtf` string.
- `src/gdtf_comparer/gui/main_window.py:279` — `resizeColumnsToContents()` sizes each column to fully fit that long text with no max-section-size cap; line 128 only sets `setStretchLastSection(True)`.

Oversized columns push the total table width past the viewport, forcing the horizontal scrollbar seen in the screenshot. Since the header scrolls in lockstep with the body, any non-zero scroll position shows the tail of the long header string with its start pushed off the left edge — that's why it *looks* like start-clipping rather than normal end-eliding.

## Fix Direction
`FixtureModel` already carries a short, human-readable `name`/`manufacturer` (`models.py:70-71`, parsed from `description.xml`). Use those for header labels instead of the raw filename; keep the full filename/path in the existing `_header_tooltip` (`table_model.py:114-125`, unchanged). Cap column width (`QHeaderView.setMaximumSectionSize` or clamp post-`resizeColumnsToContents()`) so any still-long label elides natively at the end instead of growing the column and forcing horizontal scroll.
