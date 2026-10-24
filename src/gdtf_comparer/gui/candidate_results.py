"""QAbstractTableModel presenting a CandidateScan (SUB-04 -> presentation)."""

import os
from typing import Any, Dict, Optional

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QBrush, QColor

from gdtf_comparer.core.models import format_value
from gdtf_comparer.core.substitution import DIRECTION_LABELS, CandidateFailure, CandidateScan, MatchState

MATCH_STATE_ROLE = Qt.ItemDataRole.UserRole + 1
FAILURE_ROW_ROLE = Qt.ItemDataRole.UserRole + 2

COL_RANK = 0
COL_FIXTURE = 1
COL_FILE = 2
COL_SUMMARY = 3
FIRST_REQUIREMENT_COLUMN = 4

FAILURE_FIXTURE_TEXT = "Couldn't read this file"
_FAILURE_FOREGROUND = QBrush(QColor(128, 128, 128))

# Fixed, theme-independent colors (Phase 5, Claude's discretion, matching
# gui.main_window's own fixed match-indicator color posture): a traffic
# light needs to read the same way regardless of light/dark mode.
STATE_COLORS: Dict[MatchState, QColor] = {
    MatchState.GREEN: QColor(46, 204, 113, 140),
    MatchState.YELLOW: QColor(241, 196, 15, 160),
    MatchState.RED: QColor(231, 76, 60, 140),
}

STATE_DESCRIPTIONS: Dict[MatchState, str] = {
    MatchState.GREEN: "Meets or beats the requirement",
    MatchState.YELLOW: "Close — might work",
    MatchState.RED: "Way outside the range — won't work",
}

NOT_LISTED_TEXT = "Not listed"


class CandidateResultsModel(QAbstractTableModel):
    """Table model over a CandidateScan: rank, fixture, file, summary, then one column per requirement."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._scan: Optional[CandidateScan] = None

    def set_scan(self, scan: Optional[CandidateScan]) -> None:
        """Replace the displayed scan, resetting the model.

        Parameters:
            scan: The new CandidateScan to display, or None to clear.
        """
        self.beginResetModel()
        self._scan = scan
        self.endResetModel()

    def scan(self) -> Optional[CandidateScan]:
        """Return the currently displayed CandidateScan, or None."""
        return self._scan

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return ranked candidates plus failure rows (0 for a valid parent or no scan).

        Failure rows are appended below every ranked candidate row, at
        indexes >= len(ranked) -- every file the shop owns stays visible in
        one table, readable or not.
        """
        if parent.isValid() or self._scan is None:
            return 0
        return len(self._scan.ranked) + len(self._scan.failures)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return FIRST_REQUIREMENT_COLUMN (no scan) plus the requirement count."""
        if parent.isValid():
            return 0
        if self._scan is None:
            return FIRST_REQUIREMENT_COLUMN
        return FIRST_REQUIREMENT_COLUMN + len(self._scan.requirement_set.requirements)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Return display, tooltip, match-state and background data for a cell."""
        if not index.isValid() or self._scan is None:
            return None

        row = index.row()
        column = index.column()
        ranked_count = len(self._scan.ranked)
        is_failure_row = row >= ranked_count

        if role == FAILURE_ROW_ROLE:
            return is_failure_row

        if is_failure_row:
            failure = self._scan.failures[row - ranked_count]
            return self._failure_value(failure, role, column)

        score = self._scan.ranked[row]
        if role == Qt.ItemDataRole.DisplayRole:
            return self._display_value(score, row, column)
        if role == Qt.ItemDataRole.ToolTipRole:
            return self._tooltip(score, column)
        if column >= FIRST_REQUIREMENT_COLUMN:
            requirement_index = column - FIRST_REQUIREMENT_COLUMN
            state = score.states[requirement_index]
            if role == MATCH_STATE_ROLE:
                return state
            if role == Qt.ItemDataRole.BackgroundRole:
                return QBrush(STATE_COLORS[state])
        return None

    def _failure_value(self, failure: CandidateFailure, role: int, column: int) -> Any:
        """Return one failure row's data for role/column.

        A failure row never answers MATCH_STATE_ROLE or BackgroundRole for
        any column (it has no requirement cells to color) -- only
        DisplayRole, ToolTipRole (file column only, the full path) and a
        fixed gray ForegroundRole across every column.
        """
        if role == Qt.ItemDataRole.DisplayRole:
            if column == COL_RANK:
                return "—"
            if column == COL_FIXTURE:
                return FAILURE_FIXTURE_TEXT
            if column == COL_FILE:
                return os.path.basename(failure.path)
            if column == COL_SUMMARY:
                return failure.reason
            return None
        if role == Qt.ItemDataRole.ToolTipRole:
            if column == COL_FILE:
                return failure.path
            return None
        if role == Qt.ItemDataRole.ForegroundRole:
            return _FAILURE_FOREGROUND
        return None

    def _display_value(self, score, row: int, column: int) -> Any:
        """Return the raw display text for one cell of a candidate row."""
        if column == COL_RANK:
            return str(row + 1)
        if column == COL_FIXTURE:
            if score.candidate.manufacturer.strip():
                return f"{score.candidate.name} — {score.candidate.manufacturer}"
            return score.candidate.name
        if column == COL_FILE:
            return score.candidate.file_name
        if column == COL_SUMMARY:
            return f"{score.green_count} green · {score.yellow_count} yellow · {score.red_count} red"

        requirement_index = column - FIRST_REQUIREMENT_COLUMN
        if not (0 <= requirement_index < len(score.values)):
            return None
        value = score.values[requirement_index]
        return format_value(value) if value is not None else NOT_LISTED_TEXT

    def _tooltip(self, score, column: int) -> Any:
        """Return the ToolTipRole text for one cell: requirement cells get a full explanation."""
        if column == COL_FILE:
            return score.candidate.source_path
        if column < FIRST_REQUIREMENT_COLUMN:
            return None

        requirement_index = column - FIRST_REQUIREMENT_COLUMN
        if not (0 <= requirement_index < len(score.values)):
            return None
        requirement = self._scan.requirement_set.requirements[requirement_index]
        state = score.states[requirement_index]
        return (
            f"Candidate: {format_value(score.values[requirement_index])} · "
            f"Your fixture: {format_value(requirement.target)} · "
            f"{DIRECTION_LABELS[requirement.direction]} → {STATE_DESCRIPTIONS[state]}"
        )

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """Return column headers: #, Fixture, File, Result, then each requirement's label."""
        if orientation != Qt.Orientation.Horizontal or role != Qt.ItemDataRole.DisplayRole:
            return None
        if section == COL_RANK:
            return "#"
        if section == COL_FIXTURE:
            return "Fixture"
        if section == COL_FILE:
            return "File"
        if section == COL_SUMMARY:
            return "Result"

        requirement_index = section - FIRST_REQUIREMENT_COLUMN
        if self._scan is None or not (0 <= requirement_index < len(self._scan.requirement_set.requirements)):
            return None
        key = self._scan.requirement_set.requirements[requirement_index].key
        if key.element_path:
            return f"{key.attribute} ({key.element_label})"
        return key.attribute

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """Return enabled + selectable flags for valid indexes."""
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
