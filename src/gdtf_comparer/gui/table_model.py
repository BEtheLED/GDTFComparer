"""QAbstractTableModel presenting a ComparisonResult (D-13 -> presentation)."""

from collections import Counter
from typing import AbstractSet, Any, FrozenSet, Optional, Tuple

from PySide6.QtCore import (
    QAbstractTableModel,
    QIdentityProxyModel,
    QModelIndex,
    QSortFilterProxyModel,
    Qt,
)
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import QStyledItemDelegate

from gdtf_comparer.core.models import ComparisonResult, format_value

# Custom data role a source model publishes so a view-only proxy can filter
# rows without ever calling sourceModel().result() -- works at any position
# in a proxy chain (D-03; Design notes, 02-01-PLAN.md).
SELECTION_KEY_ROLE = Qt.ItemDataRole.UserRole + 1

# Custom data role publishing ComparisonRow.any_differs, read by
# DifferencesOnlyProxyModel's filterAcceptsRow (Phase 2 D-06) the same way
# SELECTION_KEY_ROLE is read by AttributeSelectionProxyModel -- a proxy never
# calls sourceModel().result() directly.
ANY_DIFFERS_ROLE = Qt.ItemDataRole.UserRole + 2


def _value_column_labels(result: Optional[ComparisonResult]) -> Tuple[str, ...]:
    """Derive per-file header labels for a ComparisonResult's value columns.

    Parameters:
        result: The ComparisonResult to derive labels for, or None.

    Returns:
        An empty tuple for None. Otherwise one label per model (target first,
        then each comparison, in order): the model's stripped ``name`` when
        that name, compared case-and-whitespace-insensitively
        (``str.strip().casefold()``) against every other model's stripped
        name, is unique and non-empty; the model's ``file_name`` otherwise.

        Headers render uppercase (UppercaseHeaderProxyModel), so a
        case-only difference between two names would look identical to the
        user -- that is why the collision key folds case as well as
        whitespace. Falling back to the file name keeps two revisions of one
        fixture (e.g. "...@V2.gdtf" / "...@V3.gdtf") distinguishable, since
        GDTF file names conventionally start with Manufacturer@Model and end
        with the revision.
    """
    if result is None:
        return ()
    models = (result.target,) + tuple(result.comparisons)
    name_counts = Counter(model.name.strip().casefold() for model in models)
    labels = []
    for model in models:
        key = model.name.strip().casefold()
        if key and name_counts[key] == 1:
            labels.append(model.name.strip())
        else:
            labels.append(model.file_name)
    return tuple(labels)


class ComparisonTableModel(QAbstractTableModel):
    """Table model over a ComparisonResult: category, element, attribute, values.

    Per-file value-column headers show each fixture's name (fixture Name
    falling back to file_name when a name is blank or collides with another
    compared fixture's name; see _value_column_labels) -- kept in natural
    case here even though the view paints headers uppercase, so any other
    consumer of this model (e.g. a future CSV export) sees the real name.
    """

    COL_CATEGORY = 0
    COL_ELEMENT = 1
    COL_ATTRIBUTE = 2
    COL_TARGET = 3

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._result: Optional[ComparisonResult] = None
        self._value_labels: Tuple[str, ...] = ()
        self._highlight_brush: Optional[QBrush] = None

    def set_result(self, result: Optional[ComparisonResult]) -> None:
        """Replace the displayed result, resetting the model.

        Parameters:
            result: The new ComparisonResult to display, or None to clear.
        """
        self.beginResetModel()
        self._result = result
        self._value_labels = _value_column_labels(result)
        self.endResetModel()

    def result(self) -> Optional[ComparisonResult]:
        """Return the currently displayed ComparisonResult, or None."""
        return self._result

    def set_highlight_color(self, color: Optional[QColor]) -> None:
        """Set (or clear) the diff-highlight tint color (Phase 2 D-05).

        Parameters:
            color: The QColor to tint a differing comparison cell's
                BackgroundRole with, or None to clear highlighting entirely.

        Emits dataChanged for BackgroundRole over the value-column cells only
        (never the fixed Category/Element/Attribute/Target columns), so the
        view repaints just the cells that can ever be tinted.
        """
        self._highlight_brush = QBrush(QColor(color)) if color is not None else None
        if self.rowCount() > 0 and self.columnCount() > self.COL_TARGET + 1:
            self.dataChanged.emit(
                self.index(0, self.COL_TARGET + 1),
                self.index(self.rowCount() - 1, self.columnCount() - 1),
                [Qt.ItemDataRole.BackgroundRole],
            )

    def highlight_color(self) -> Optional[QColor]:
        """Return a copy of the current diff-highlight tint color, or None."""
        if self._highlight_brush is None:
            return None
        return QColor(self._highlight_brush.color())

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of comparison rows (0 for a valid parent or no result)."""
        if parent.isValid() or self._result is None:
            return 0
        return len(self._result.rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return 4 (no result) or 4 plus the number of comparison files."""
        if parent.isValid():
            return 0
        if self._result is None:
            return 4
        return 4 + len(self._result.comparisons)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Return display, tooltip and diff-highlight data for a cell."""
        if not index.isValid() or self._result is None:
            return None

        row = self._result.rows[index.row()]
        column = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            return self._display_value(row, column)
        if role == Qt.ItemDataRole.ToolTipRole:
            if column == self.COL_ELEMENT:
                return row.key.element_path
            return self._display_value(row, column)
        if role == SELECTION_KEY_ROLE:
            return (row.key.category, row.key.attribute)
        if role == ANY_DIFFERS_ROLE:
            return row.any_differs
        if role == Qt.ItemDataRole.BackgroundRole:
            return self._background(row, column)
        return None

    def _background(self, row, column: int) -> Optional[QBrush]:
        """Return the diff-highlight brush for one cell, or None.

        Reads only ComparisonRow.differs (never display text, prohibition 1
        of 02-03-PLAN.md): a comparison-value column (column > COL_TARGET)
        whose corresponding differs flag is True gets the current highlight
        brush; the Target column, the fixed Category/Element/Attribute
        columns, and any equal or out-of-range comparison column get None.
        """
        if self._highlight_brush is None or column <= self.COL_TARGET:
            return None
        comparison_index = column - self.COL_TARGET - 1
        if 0 <= comparison_index < len(row.differs) and row.differs[comparison_index]:
            return self._highlight_brush
        return None

    def _display_value(self, row, column: int) -> Any:
        """Return the raw display text for one cell of a comparison row."""
        if column == self.COL_CATEGORY:
            return row.key.category
        if column == self.COL_ELEMENT:
            return row.key.element_label
        if column == self.COL_ATTRIBUTE:
            return row.key.attribute
        if column == self.COL_TARGET:
            return format_value(row.target_value)
        comparison_index = column - self.COL_TARGET - 1
        if 0 <= comparison_index < len(row.comparison_values):
            return format_value(row.comparison_values[comparison_index])
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """Return column headers: labels, or tooltips for value columns."""
        if orientation != Qt.Orientation.Horizontal:
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            return self._header_label(section)
        if role == Qt.ItemDataRole.ToolTipRole and section >= self.COL_TARGET:
            return self._header_tooltip(section)
        return None

    def _header_label(self, section: int) -> Any:
        """Return the DisplayRole header text for one column.

        Value columns (COL_TARGET onward) use each fixture's name, falling
        back to its file name on a blank or colliding name
        (_value_column_labels).
        """
        if section == self.COL_CATEGORY:
            return "Category"
        if section == self.COL_ELEMENT:
            return "Element"
        if section == self.COL_ATTRIBUTE:
            return "Attribute"
        if section == self.COL_TARGET:
            if self._result is None:
                return "Target"
            return f"Target: {self._value_labels[0]}"
        comparison_index = section - self.COL_TARGET - 1
        if self._result is not None and 0 <= comparison_index < len(self._result.comparisons):
            return self._value_labels[1 + comparison_index]
        return None

    def _header_tooltip(self, section: int) -> Any:
        """Return the ToolTipRole header text.

        "<manufacturer> <name> — <source_path>" when the model declares a
        non-blank manufacturer, else "<name> — <source_path>". The full
        path (including the real file name) is always shown here, even when
        the header label itself fell back to the file name.
        """
        if self._result is None:
            return None
        if section == self.COL_TARGET:
            model = self._result.target
        else:
            comparison_index = section - self.COL_TARGET - 1
            if not (0 <= comparison_index < len(self._result.comparisons)):
                return None
            model = self._result.comparisons[comparison_index]
        if model.manufacturer.strip():
            return f"{model.manufacturer} {model.name} — {model.source_path}"
        return f"{model.name} — {model.source_path}"

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """Return enabled + selectable flags for valid indexes."""
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def find_row(self, category: str, element_path: str, attribute: str) -> int:
        """Find the row index matching a given AttributeKey's fields.

        Parameters:
            category: The AttributeKey category to match.
            element_path: The AttributeKey element_path to match.
            attribute: The AttributeKey attribute to match.

        Returns:
            The matching row index, or -1 if no row matches or no result is set.
        """
        if self._result is None:
            return -1
        for index, row in enumerate(self._result.rows):
            key = row.key
            if (
                key.category == category
                and key.element_path == element_path
                and key.attribute == attribute
            ):
                return index
        return -1


class AttributeSelectionProxyModel(QSortFilterProxyModel):
    """View-only proxy that shows only checked (category, attribute) rows.

    D-03: the checked set (from gui.attribute_picker.AttributePicker) is the
    single source of truth for which rows appear; this proxy never modifies
    the source model or the ComparisonResult it presents. It reads the row's
    identity through SELECTION_KEY_ROLE rather than calling
    sourceModel().result(), so it works at any position in a proxy chain
    (Design notes, 02-01-PLAN.md). An empty selection hides every row.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._selected: FrozenSet[Tuple[str, str]] = frozenset()

    def set_selected_attributes(self, pairs: AbstractSet[Tuple[str, str]]) -> None:
        """Replace the checked (category, attribute) set and refilter.

        Parameters:
            pairs: The (category, attribute) pairs whose rows should show.

        Uses beginFilterChange()/endFilterChange() rather than the single-
        call invalidate*() methods, which raise DeprecationWarning under
        PySide6 6.11.2 (Design notes, 02-01-PLAN.md).
        """
        self.beginFilterChange()
        self._selected = frozenset(tuple(pair) for pair in pairs)
        self.endFilterChange(QSortFilterProxyModel.Direction.Rows)

    def selected_attributes(self) -> FrozenSet[Tuple[str, str]]:
        """Return the currently checked (category, attribute) set."""
        return self._selected

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        """Accept a source row only when its selection key is checked."""
        key = self.sourceModel().index(source_row, 0, source_parent).data(SELECTION_KEY_ROLE)
        return key is not None and tuple(key) in self._selected


class DifferencesOnlyProxyModel(QSortFilterProxyModel):
    """View-only proxy that hides rows where nothing differs (Phase 2 D-06).

    On top of the cell highlighting, not a replacement for it: this proxy
    never modifies the source model or the ComparisonResult it presents, and
    it never sorts, so the rows it shows keep the source's order. It reads
    the row's any_differs flag through ANY_DIFFERS_ROLE rather than calling
    sourceModel().result(), so it works at any position in a proxy chain
    (same pattern as AttributeSelectionProxyModel / SELECTION_KEY_ROLE).
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._enabled = False

    def set_differences_only(self, enabled: bool) -> None:
        """Enable or disable the differences-only filter and refilter.

        Parameters:
            enabled: True to show only rows where any_differs is True.

        A no-op when enabled already matches the current state. Uses
        beginFilterChange()/endFilterChange() rather than the single-call
        invalidate*() methods, which raise DeprecationWarning under PySide6
        6.11.2 (same pattern as AttributeSelectionProxyModel).
        """
        enabled = bool(enabled)
        if enabled == self._enabled:
            return
        self.beginFilterChange()
        self._enabled = enabled
        self.endFilterChange(QSortFilterProxyModel.Direction.Rows)

    def differences_only(self) -> bool:
        """Return True when the differences-only filter is enabled."""
        return self._enabled

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        """Accept every row when disabled; only any_differs rows when enabled."""
        if not self._enabled:
            return True
        return bool(
            self.sourceModel().index(source_row, 0, source_parent).data(ANY_DIFFERS_ROLE)
        )


class BackgroundBrushDelegate(QStyledItemDelegate):
    """Paints a cell's BackgroundRole brush before Qt's own item painting.

    Measured at planning time (02-03-PLAN.md Design notes): once qt-material's
    stylesheet is applied, its ``QTableView::item`` rule (padding, min-height,
    a transparent border-color) makes Qt's stylesheet style draw the item
    itself and ignore the item's own BackgroundRole brush -- a cell whose
    data() answers BackgroundRole with a colored QBrush paints identically to
    an unhighlighted neighbor under qt-material with no delegate. This
    delegate only adds that fill; sizing, text and selection painting remain
    entirely Qt's own via the super().paint() call.
    """

    def paint(self, painter, option, index) -> None:
        """Fill option.rect with the index's BackgroundRole brush, then paint normally."""
        brush = index.data(Qt.ItemDataRole.BackgroundRole)
        if brush is not None:
            painter.fillRect(option.rect, brush)
        super().paint(painter, option, index)


class UppercaseHeaderProxyModel(QIdentityProxyModel):
    """View-only proxy that uppercases horizontal header DisplayRole text.

    qt-material paints ``QHeaderView::section`` text uppercase via CSS
    ``text-transform``, but Qt's own column-sizing and elision logic measures
    the text the model returns -- it does not know about that CSS effect. A
    column sized to fit "Category" is too narrow for the painted "CATEGORY",
    clipping the label at both ends (01-UAT.md G-01-1). Handing the view text
    that is already uppercased makes Qt measure and elide exactly what
    qt-material paints, in both themes and across a live light/dark switch --
    no custom stylesheet and no edits to the vendored qt-material template
    (D-05, D-08). Every other role/orientation, and vertical headers, pass
    through unchanged. The source ComparisonTableModel keeps natural-case
    labels for any other consumer (e.g. a future CSV export).
    """

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """Return the source header value, uppercased for horizontal DisplayRole text."""
        value = super().headerData(section, orientation, role)
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
            and isinstance(value, str)
        ):
            return value.upper()
        return value
