"""Main window: file pickers, Run Comparison, results table (UI-02).

Only ever calls into gdtf_comparer.core.comparator / core.models -- never
pygdtf or zipfile directly (D-16). Comparison work runs on a QThread-backed
ComparisonWorker so the GUI thread never blocks (D-14).
"""

import logging
import os
from typing import List, Optional, Sequence

from PySide6.QtCore import QThread, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from gdtf_comparer.core.models import ComparisonResult
from gdtf_comparer.gui.table_model import ComparisonTableModel, UppercaseHeaderProxyModel
from gdtf_comparer.gui.worker import ComparisonWorker

GDTF_FILE_FILTER = "GDTF files (*.gdtf);;All files (*)"

_LOGGER = logging.getLogger(__name__)

# How long closeEvent waits for a running worker thread before giving up and
# closing anyway (WR-01, T-01-29). Read at call time (not captured as a
# default argument) so tests can shrink it. Well above the 0.3 s worker used
# by test_close_during_comparison_does_not_crash, so a normal in-flight
# comparison is still waited for and finishes cleanly.
CLOSE_WAIT_TIMEOUT_MS = 3000


def _normalized_path(path: str) -> str:
    """Return a canonical key for path so alias forms compare equal.

    Parameters:
        path: A file path, possibly containing "./"/".." segments or a
            symlink, or differing only in case.

    Returns:
        os.path.normcase(os.path.realpath(path)) -- realpath resolves
        symlinks and "." / ".." segments, and normcase folds case on
        Windows (a no-op elsewhere) (WR-02, T-01-27).
    """
    return os.path.normcase(os.path.realpath(path))


class MainWindow(QMainWindow):
    """Pick a target + comparison GDTF files, run a comparison, view the table."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.target_file: str = ""
        self.compare_files: List[str] = []
        self._thread: Optional[QThread] = None
        self._worker: Optional[ComparisonWorker] = None

        self.setWindowTitle("GDTF Comparer")
        self.resize(1000, 650)
        self.create_widgets()

    def create_widgets(self) -> None:
        """Build the Files group box, Run button, and results table."""
        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        files_group = QGroupBox("Files", central)
        grid = QGridLayout(files_group)

        target_label = QLabel("Target GDTF", files_group)
        self.target_edit = QLineEdit(files_group)
        self.target_edit.setReadOnly(True)
        self.target_edit.setPlaceholderText("No target selected")
        self.target_button = QPushButton("Browse…", files_group)
        self.target_button.clicked.connect(self.select_target_file)

        grid.addWidget(target_label, 0, 0)
        grid.addWidget(self.target_edit, 0, 1)
        grid.addWidget(self.target_button, 0, 2)

        compare_label = QLabel("Compare with", files_group)
        self.compare_list = QListWidget(files_group)
        self.compare_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        button_column = QVBoxLayout()
        self.add_button = QPushButton("Add Files…", files_group)
        self.add_button.clicked.connect(self.select_compare_files)
        self.remove_button = QPushButton("Remove Selected", files_group)
        self.remove_button.clicked.connect(self.remove_selected_files)
        button_column.addWidget(self.add_button)
        button_column.addWidget(self.remove_button)
        button_column.addStretch(1)

        grid.addWidget(compare_label, 1, 0, Qt.AlignmentFlag.AlignTop)
        grid.addWidget(self.compare_list, 1, 1)
        grid.addLayout(button_column, 1, 2)

        layout.addWidget(files_group)

        run_row = QHBoxLayout()
        run_row.addStretch(1)
        self.run_button = QPushButton("Run Comparison", central)
        self.run_button.clicked.connect(self.run_comparison)
        run_row.addWidget(self.run_button)
        layout.addLayout(run_row)

        self.table_model = ComparisonTableModel(central)
        self.header_proxy = UppercaseHeaderProxyModel(central)
        self.header_proxy.setSourceModel(self.table_model)
        self.table_view = QTableView(central)
        self.table_view.setModel(self.header_proxy)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table_view)

        self.statusBar().showMessage("Ready")

    def select_target_file(self) -> None:
        """Open a file dialog to pick the target GDTF file."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Target GDTF File", "", GDTF_FILE_FILTER
        )
        if path:
            self.set_target_file(path)

    def select_compare_files(self) -> None:
        """Open a file dialog to add one or more comparison GDTF files."""
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Comparison GDTF Files", "", GDTF_FILE_FILTER
        )
        if paths:
            self.add_compare_files(paths)

    def set_target_file(self, path: str) -> None:
        """Set the target file path and evict it from the comparison list.

        A file can never be both the target and a comparison file (WR-02):
        if the newly chosen target is already present in compare_files
        (including via a "./" segment or symlink alias, T-01-27), it is
        removed from the comparison list and the status bar says so.

        Parameters:
            path: Path to the target .gdtf file.
        """
        self.target_file = path
        self.target_edit.setText(path)

        if not path:
            return

        target_key = _normalized_path(path)
        removed_basename: Optional[str] = None
        for row in range(self.compare_list.count() - 1, -1, -1):
            item = self.compare_list.item(row)
            item_path = item.data(Qt.ItemDataRole.UserRole)
            if _normalized_path(item_path) == target_key:
                removed_basename = os.path.basename(item_path)
                if item_path in self.compare_files:
                    self.compare_files.remove(item_path)
                self.compare_list.takeItem(row)

        if removed_basename is not None:
            self.statusBar().showMessage(
                f"Removed '{removed_basename}' from the comparison list: "
                "it is now the target file."
            )

    def add_compare_files(self, paths: Sequence[str]) -> None:
        """Add comparison files, refusing the target and duplicate paths.

        A file can never be both the target and a comparison file (WR-02):
        any candidate that resolves to the same file as the current target
        (including via a "./" segment or symlink alias, T-01-27) is skipped
        and reported in the status bar instead of being added.

        Parameters:
            paths: Candidate .gdtf file paths to add, in order.
        """
        target_key = _normalized_path(self.target_file) if self.target_file else None
        existing_keys = {_normalized_path(path) for path in self.compare_files}
        target_was_offered = False

        for path in paths:
            if not path:
                continue
            key = _normalized_path(path)
            if target_key is not None and key == target_key:
                target_was_offered = True
                continue
            if key in existing_keys:
                continue
            self.compare_files.append(path)
            existing_keys.add(key)
            item = QListWidgetItem(os.path.basename(path))
            item.setToolTip(path)
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.compare_list.addItem(item)

        if target_was_offered:
            self.statusBar().showMessage(
                f"Skipped '{os.path.basename(self.target_file)}': it is "
                "already selected as the target file."
            )

    def remove_selected_files(self) -> None:
        """Remove the selected rows from both compare_files and the list widget."""
        for item in self.compare_list.selectedItems():
            row = self.compare_list.row(item)
            path = item.data(Qt.ItemDataRole.UserRole)
            if path in self.compare_files:
                self.compare_files.remove(path)
            self.compare_list.takeItem(row)

    def run_comparison(self) -> None:
        """Validate inputs, then run a comparison on a QThread worker (D-14)."""
        if self.is_comparison_running():
            return
        if not self.target_file:
            self._show_error("Select a target GDTF file before running a comparison.")
            return
        if not self.compare_files:
            self._show_error("Add at least one GDTF file to compare against the target.")
            return

        self.table_model.set_result(None)
        self.run_button.setEnabled(False)
        self.statusBar().showMessage(f"Comparing {len(self.compare_files)} file(s)…")

        thread = QThread(self)
        worker = ComparisonWorker(self.target_file, list(self.compare_files))
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.comparison_ready.connect(self.on_comparison_ready)
        worker.comparison_failed.connect(self.on_comparison_failed)
        worker.comparison_ready.connect(thread.quit)
        worker.comparison_failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_thread_finished)

        self._thread = thread
        self._worker = worker
        thread.start()

    def _on_thread_finished(self) -> None:
        """Clear thread/worker references and re-enable Run Comparison.

        This is the ONLY place run_button is re-enabled, so a second
        comparison can never start while the previous worker thread is
        still alive (D-14).
        """
        self._thread = None
        self._worker = None
        self.run_button.setEnabled(True)

    def on_comparison_ready(self, result: ComparisonResult) -> None:
        """Render a successful comparison result.

        Parameters:
            result: The ComparisonResult produced by the worker.
        """
        self.table_model.set_result(result)
        self.table_view.resizeColumnsToContents()
        self.statusBar().showMessage(
            f"Compared {len(result.comparisons)} file(s) against {result.target.file_name}"
        )

    def on_comparison_failed(self, message: str) -> None:
        """Clear the table and show a friendly error for a failed comparison.

        Parameters:
            message: The user-facing error message from the worker.
        """
        self.table_model.set_result(None)
        self.statusBar().showMessage("Comparison failed")
        self._show_error(message)

    def is_comparison_running(self) -> bool:
        """Return True while a worker thread exists and is still running."""
        return self._thread is not None and self._thread.isRunning()

    def closeEvent(self, event) -> None:
        """Quit and wait (bounded) for any running worker thread, then close.

        Never blocks the GUI thread for more than CLOSE_WAIT_TIMEOUT_MS (D-14,
        WR-01, T-01-29): a worker stuck in an uninterruptible OS read (e.g. a
        stalled network mount) cannot be interrupted from Python, so if the
        wait times out the window closes anyway and gdtf_comparer.app.main
        ends the process once the Qt event loop returns.
        """
        if self._thread is not None:
            self._thread.quit()
            finished = self._thread.wait(CLOSE_WAIT_TIMEOUT_MS)
            if not finished:
                _LOGGER.warning(
                    "Comparison worker still running after %d ms; closing anyway.",
                    CLOSE_WAIT_TIMEOUT_MS,
                )
        super().closeEvent(event)

    def _show_error(self, message: str) -> None:
        """Show a friendly modal, plain-text error dialog.

        Parameters:
            message: The message to display to the user. Always rendered as
                plain text (Qt.TextFormat.PlainText) so a file name is never
                interpreted as rich text (T-01-17).
        """
        box = QMessageBox(
            QMessageBox.Icon.Warning,
            "GDTF Comparer",
            message,
            QMessageBox.StandardButton.Ok,
            self,
        )
        box.setTextFormat(Qt.TextFormat.PlainText)
        box.exec()
