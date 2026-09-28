# Debug Session: G-01-1 — Column header text clipped (CATEGORY/ELEMENT/ATTRIBUTE)

## Symptom
Fixed table header labels render truncated in-app — "CATEGORY" shows as "ATEGOR", "ELEMENT" and "ATTRIBUTE" similarly clipped.

## Root Cause
App is PySide6/Qt themed via qt-material (not Tkinter — `CLAUDE.md`'s stack description is stale).

- `qt_material/material.qss.template:1326-1336` sets `QHeaderView::section { text-transform: uppercase; padding: 0 24px; }`, applied via `apply_stylesheet()` at `src/gdtf_comparer/gui/theme.py:64`. Uppercasing is a paint-time CSS effect only.
- Column widths are computed by `self.table_view.resizeColumnsToContents()` at `src/gdtf_comparer/gui/main_window.py:279`, which sizes from the original mixed-case strings returned by `_header_label()` in `src/gdtf_comparer/gui/table_model.py:97-108` (e.g. "Category").
- Qt's size-hint calculation ignores CSS `text-transform`, so the computed width fits "Category" but not the wider rendered "CATEGORY". Headers use Qt's default center alignment (no `Qt.TextAlignmentRole` override), so overflow clips symmetrically from both ends, matching "CATEGORY" → "ATEGOR".

## Fix Direction
After `resizeColumnsToContents()` (`main_window.py:279`), widen these header columns using width computed from the *uppercased* label (`QFontMetrics.horizontalAdvance(label.upper())`) plus the stylesheet's 24px × 2 padding, instead of relying on Qt's built-in size hint (which ignores `text-transform`). Do not modify the vendored qt-material template (third-party dependency).
