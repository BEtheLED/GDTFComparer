"""QAbstractTableModel presenting a ComparisonResult (D-13 -> presentation)."""

from typing import Any, Optional

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from gdtf_comparer.core.models import ComparisonResult, format_value


class ComparisonTableModel(QAbstractTableModel):
    """Table model over a ComparisonResult: category, element, attribute, values."""

    COL_CATEGORY = 0
    COL_ELEMENT = 1
    COL_ATTRIBUTE = 2
    COL_TARGET = 3

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._result: Optional[ComparisonResult] = None

    def set_result(self, result: Optional[ComparisonResult]) -> None:
        """Replace the displayed result, resetting the model.

        Parameters:
            result: The new ComparisonResult to display, or None to clear.
        """
        self.beginResetModel()
        self._result = result
        self.endResetModel()

    def result(self) -> Optional[ComparisonResult]:
        """Return the currently displayed ComparisonResult, or None."""
        return self._result

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
        """Return display/tooltip data for a cell."""
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
        """Return the DisplayRole header text for one column."""
        if section == self.COL_CATEGORY:
            return "Category"
        if section == self.COL_ELEMENT:
            return "Element"
        if section == self.COL_ATTRIBUTE:
            return "Attribute"
        if section == self.COL_TARGET:
            if self._result is None:
                return "Target"
            return f"Target: {self._result.target.file_name}"
        comparison_index = section - self.COL_TARGET - 1
        if self._result is not None and 0 <= comparison_index < len(self._result.comparisons):
            return self._result.comparisons[comparison_index].file_name
        return None

    def _header_tooltip(self, section: int) -> Any:
        """Return the ToolTipRole header text ("<name> — <source_path>")."""
        if self._result is None:
            return None
        if section == self.COL_TARGET:
            model = self._result.target
        else:
            comparison_index = section - self.COL_TARGET - 1
            if not (0 <= comparison_index < len(self._result.comparisons)):
                return None
            model = self._result.comparisons[comparison_index]
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
