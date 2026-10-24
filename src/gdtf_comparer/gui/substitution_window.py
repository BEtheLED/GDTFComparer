"""Find Substitutes window: MVR import, requirements editing, inventory checking (D-07).

Two tabs in one top-level window, one per role: "1. Set Requirements" (the
LD imports an MVR, marks what matters, saves a sidecar file) and "2. Check
Inventory" (anyone opens that file, points at a folder of GDTF files, and
sees them ranked). Both long-running operations (MVR import, folder scan)
run on a QThread worker, mirroring gui.main_window's existing D-14 wiring.
"""

import logging
import os
from typing import Optional

from PySide6.QtCore import QThread, Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableView,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from gdtf_comparer.core.errors import SubstitutionError
from gdtf_comparer.core.mvr_repository import MVRImport, import_summary_message
from gdtf_comparer.core.requirements_repository import load_requirements, save_requirements, suggested_file_name
from gdtf_comparer.core.substitution import (
    CandidateScan,
    RequirementSet,
    describe_requirements,
    scan_summary_message,
)
from gdtf_comparer.gui.candidate_results import LEGEND_TEXT, CandidateResultsModel
from gdtf_comparer.gui.requirements_editor import RequirementsEditor
from gdtf_comparer.gui.table_model import BackgroundBrushDelegate
from gdtf_comparer.gui.worker import CandidateScanWorker, MVRImportWorker

_LOGGER = logging.getLogger(__name__)

IMPORT_MVR_LABEL = "Import MVR…"
SAVE_REQUIREMENTS_LABEL = "Save Requirements…"
USE_FOR_INVENTORY_LABEL = "Check Inventory With These…"
OPEN_REQUIREMENTS_LABEL = "Open Requirements…"
CHOOSE_FOLDER_LABEL = "Choose Inventory Folder…"
CHECK_INVENTORY_LABEL = "Check Inventory"

MVR_FILE_FILTER = "MVR files (*.mvr);;All files (*)"
REQUIREMENTS_FILE_FILTER = "Fixture requirements (*.json);;All files (*)"

FIXTURE_TYPE_ITEM_TEMPLATE = "{name} — {manufacturer} ({count} in this show)"
FIXTURE_TYPE_ITEM_NO_MANUFACTURER_TEMPLATE = "{name} ({count} in this show)"

NO_MVR_PLACEHOLDER = "No show file imported yet."
NO_REQUIREMENTS_PLACEHOLDER = "No requirements loaded yet."
NO_FOLDER_PLACEHOLDER = "No inventory folder chosen yet."

NEED_REQUIREMENTS_MESSAGE = "Open a requirements file first, or send one over from the Set Requirements tab."
NEED_FOLDER_MESSAGE = "Choose the folder that holds your inventory's GDTF files first."

REQUIREMENTS_SAVED_TEMPLATE = "Saved requirements for '{name}' to '{file}'."

# How long closeEvent waits for a running worker thread before giving up and
# closing anyway, mirroring gui.main_window.CLOSE_WAIT_TIMEOUT_MS. Read at
# call time (not captured as a default argument) so tests can shrink it.
SUBSTITUTION_CLOSE_WAIT_TIMEOUT_MS = 3000


class SubstitutionWindow(QMainWindow):
    """Find Substitutes: import an MVR, mark requirements, check inventory (D-07)."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Find Substitutes — GDTF Comparer")
        self.resize(1280, 760)

        self._mvr_import: Optional[MVRImport] = None
        self._loaded_requirements: Optional[RequirementSet] = None
        self._import_thread: Optional[QThread] = None
        self._import_worker: Optional[MVRImportWorker] = None
        self._scan_thread: Optional[QThread] = None
        self._scan_worker: Optional[CandidateScanWorker] = None

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Build the two tabs and their widgets."""
        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)

        self.set_requirements_tab = self._create_set_requirements_tab()
        self.tabs.addTab(self.set_requirements_tab, "1. Set Requirements")

        self.check_inventory_tab = self._create_check_inventory_tab()
        self.tabs.addTab(self.check_inventory_tab, "2. Check Inventory")

        self.statusBar().showMessage("Ready")

    def _create_set_requirements_tab(self) -> QWidget:
        """Build the "1. Set Requirements" tab: import, pick a type, mark requirements."""
        tab = QWidget(self)
        layout = QVBoxLayout(tab)

        import_row = QHBoxLayout()
        self.import_mvr_button = QPushButton(IMPORT_MVR_LABEL, tab)
        self.import_mvr_button.clicked.connect(self.import_mvr)
        import_row.addWidget(self.import_mvr_button)
        self.mvr_summary_label = QLabel(NO_MVR_PLACEHOLDER, tab)
        self.mvr_summary_label.setWordWrap(True)
        # A skipped fixture type's name or a bogus GDTFSpec is shown
        # verbatim -- it is file-supplied text and must never be
        # interpreted as rich text (T-01-17 carried to Phase 5).
        self.mvr_summary_label.setTextFormat(Qt.TextFormat.PlainText)
        import_row.addWidget(self.mvr_summary_label, 1)
        layout.addLayout(import_row)

        splitter = QSplitter(Qt.Orientation.Horizontal, tab)
        self.fixture_list = QListWidget(splitter)
        self.fixture_list.currentRowChanged.connect(self._show_selected_fixture)
        splitter.addWidget(self.fixture_list)

        right_pane = QWidget(splitter)
        right_layout = QVBoxLayout(right_pane)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self.requirements_editor = RequirementsEditor(right_pane)
        right_layout.addWidget(self.requirements_editor)

        actions_row = QHBoxLayout()
        self.save_requirements_button = QPushButton(SAVE_REQUIREMENTS_LABEL, right_pane)
        self.save_requirements_button.setEnabled(False)
        self.save_requirements_button.clicked.connect(self.save_requirements)
        actions_row.addWidget(self.save_requirements_button)
        self.use_for_inventory_button = QPushButton(USE_FOR_INVENTORY_LABEL, right_pane)
        self.use_for_inventory_button.setEnabled(False)
        self.use_for_inventory_button.clicked.connect(self.use_requirements_for_inventory)
        actions_row.addWidget(self.use_for_inventory_button)
        right_layout.addLayout(actions_row)

        splitter.addWidget(right_pane)
        layout.addWidget(splitter)
        return tab

    def _create_check_inventory_tab(self) -> QWidget:
        """Build the "2. Check Inventory" tab: open requirements, scan a folder, see ranked results."""
        tab = QWidget(self)
        layout = QVBoxLayout(tab)

        open_row = QHBoxLayout()
        self.open_requirements_button = QPushButton(OPEN_REQUIREMENTS_LABEL, tab)
        self.open_requirements_button.clicked.connect(self.open_requirements)
        open_row.addWidget(self.open_requirements_button)
        self.requirements_summary_label = QLabel(NO_REQUIREMENTS_PLACEHOLDER, tab)
        self.requirements_summary_label.setWordWrap(True)
        open_row.addWidget(self.requirements_summary_label, 1)
        layout.addLayout(open_row)

        folder_row = QHBoxLayout()
        self.choose_folder_button = QPushButton(CHOOSE_FOLDER_LABEL, tab)
        self.choose_folder_button.clicked.connect(self.choose_inventory_folder)
        folder_row.addWidget(self.choose_folder_button)
        self.folder_label = QLabel(NO_FOLDER_PLACEHOLDER, tab)
        self.folder_label.setWordWrap(True)
        folder_row.addWidget(self.folder_label, 1)
        layout.addLayout(folder_row)

        self.check_inventory_button = QPushButton(CHECK_INVENTORY_LABEL, tab)
        self.check_inventory_button.clicked.connect(self.check_inventory)
        layout.addWidget(self.check_inventory_button)

        # D-10 on screen: a legend in the user's own words, directly above
        # the results table, so color is never the only signal.
        self.legend_label = QLabel(LEGEND_TEXT, tab)
        self.legend_label.setWordWrap(True)
        self.legend_label.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.legend_label)

        self.results_model = CandidateResultsModel(tab)
        self.results_view = QTableView(tab)
        self.results_view.setModel(self.results_model)
        self.results_view.setItemDelegate(BackgroundBrushDelegate(self.results_view))
        self.results_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.results_view.verticalHeader().setVisible(False)
        self.results_view.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.results_view)

        self._folder_path: Optional[str] = None
        return tab

    def _ask_open_mvr_path(self) -> Optional[str]:
        """Prompt for an MVR file to import. Returns None if cancelled."""
        path, _ = QFileDialog.getOpenFileName(self, "Import MVR", "", MVR_FILE_FILTER)
        return path or None

    def _ask_save_requirements_path(self, suggested: str) -> Optional[str]:
        """Prompt for where to save a requirements file. Returns None if cancelled."""
        path, _ = QFileDialog.getSaveFileName(self, "Save Requirements", suggested, REQUIREMENTS_FILE_FILTER)
        return path or None

    def _ask_open_requirements_path(self) -> Optional[str]:
        """Prompt for a requirements file to open. Returns None if cancelled."""
        path, _ = QFileDialog.getOpenFileName(self, "Open Requirements", "", REQUIREMENTS_FILE_FILTER)
        return path or None

    def _ask_inventory_folder(self) -> Optional[str]:
        """Prompt for an inventory folder to scan. Returns None if cancelled."""
        path = QFileDialog.getExistingDirectory(self, "Choose Inventory Folder")
        return path or None

    def _show_error(self, message: str) -> None:
        """Show a friendly modal, plain-text error dialog (mirrors MainWindow._show_error)."""
        box = QMessageBox(
            QMessageBox.Icon.Warning,
            "GDTF Comparer",
            message,
            QMessageBox.StandardButton.Ok,
            self,
        )
        box.setTextFormat(Qt.TextFormat.PlainText)
        box.exec()

    def is_busy(self) -> bool:
        """Return True while an import or scan worker thread is still running."""
        return (self._import_thread is not None and self._import_thread.isRunning()) or (
            self._scan_thread is not None and self._scan_thread.isRunning()
        )

    def import_mvr(self) -> None:
        """Prompt for an MVR file and import it on a background worker (PARSE-02)."""
        if self._import_thread is not None:
            return
        path = self._ask_open_mvr_path()
        if path is None:
            return

        self.fixture_list.clear()
        self.requirements_editor.clear()
        self.mvr_summary_label.setText(f"Importing '{os.path.basename(path)}'…")
        self.import_mvr_button.setEnabled(False)

        thread = QThread(self)
        worker = MVRImportWorker(path)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.import_ready.connect(self._on_import_ready)
        worker.import_failed.connect(self._on_import_failed)
        worker.import_ready.connect(thread.quit)
        worker.import_failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_import_thread_finished)

        self._import_thread = thread
        self._import_worker = worker
        thread.start()

    def _on_import_thread_finished(self) -> None:
        """Clear import thread/worker references and re-enable Import MVR…."""
        self._import_thread = None
        self._import_worker = None
        self.import_mvr_button.setEnabled(True)

    def _on_import_ready(self, result: MVRImport) -> None:
        """Populate the fixture list from a successful MVR import."""
        self._mvr_import = result
        for entry in result.fixture_types:
            if entry.fixture.manufacturer.strip():
                text = FIXTURE_TYPE_ITEM_TEMPLATE.format(
                    name=entry.fixture.name, manufacturer=entry.fixture.manufacturer, count=entry.instance_count
                )
            else:
                text = FIXTURE_TYPE_ITEM_NO_MANUFACTURER_TEMPLATE.format(
                    name=entry.fixture.name, count=entry.instance_count
                )
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, entry.gdtf_spec)
            item.setToolTip(entry.gdtf_spec)
            self.fixture_list.addItem(item)

        self.mvr_summary_label.setText(import_summary_message(result))
        if self.fixture_list.count() > 0:
            self.fixture_list.setCurrentRow(0)
        else:
            # An MVR with no importable fixture type (SUB-01 empty edge):
            # currentRowChanged never fires on an empty list, so the
            # editor/buttons must be cleared explicitly here instead.
            self._show_selected_fixture(-1)

    def _on_import_failed(self, message: str) -> None:
        """Clear the fixture list and show a friendly error for a failed import."""
        self.fixture_list.clear()
        self.requirements_editor.clear()
        self.mvr_summary_label.setText(NO_MVR_PLACEHOLDER)
        self._show_error(message)

    def _show_selected_fixture(self, row: int) -> None:
        """Show the currently selected fixture type's requirements editor, or clear it."""
        if row < 0 or self._mvr_import is None:
            self.requirements_editor.clear()
            self.save_requirements_button.setEnabled(False)
            self.use_for_inventory_button.setEnabled(False)
            return

        entry = self._mvr_import.fixture_types[row]
        self.requirements_editor.show_fixture(entry.gdtf_spec, entry.fixture)
        self.save_requirements_button.setEnabled(True)
        self.use_for_inventory_button.setEnabled(True)

    def save_requirements(self) -> None:
        """Save the editor's currently checked requirements to a chosen file (D-08, D-09)."""
        requirement_set = self.requirements_editor.requirement_set()
        if requirement_set is None:
            return
        path = self._ask_save_requirements_path(suggested_file_name(requirement_set))
        if path is None:
            return

        try:
            save_requirements(path, requirement_set)
        except SubstitutionError as exc:
            self._show_error(str(exc))
            return

        self.statusBar().showMessage(
            REQUIREMENTS_SAVED_TEMPLATE.format(name=requirement_set.fixture_name, file=path)
        )

    def use_requirements_for_inventory(self) -> None:
        """Send the editor's current requirements to the Check Inventory tab (D-03)."""
        requirement_set = self.requirements_editor.requirement_set()
        if requirement_set is None:
            return
        self._loaded_requirements = requirement_set
        self.requirements_summary_label.setText(describe_requirements(requirement_set))
        self.results_model.set_scan(None)
        self.tabs.setCurrentWidget(self.check_inventory_tab)

    def open_requirements(self) -> None:
        """Prompt for a requirements file and load it (SUB-03)."""
        path = self._ask_open_requirements_path()
        if path is None:
            return

        try:
            requirement_set = load_requirements(path)
        except SubstitutionError as exc:
            self._show_error(str(exc))
            return

        self._loaded_requirements = requirement_set
        self.requirements_summary_label.setText(describe_requirements(requirement_set))
        self.results_model.set_scan(None)

    def choose_inventory_folder(self) -> None:
        """Prompt for an inventory folder to scan against (SUB-04)."""
        path = self._ask_inventory_folder()
        if path is None:
            return
        self._folder_path = path
        self.folder_label.setText(path)

    def check_inventory(self) -> None:
        """Scan the chosen folder against the loaded requirements on a background worker (SUB-04)."""
        if self._scan_thread is not None:
            return
        if self._loaded_requirements is None:
            self._show_error(NEED_REQUIREMENTS_MESSAGE)
            return
        if not self._folder_path:
            self._show_error(NEED_FOLDER_MESSAGE)
            return

        self.results_model.set_scan(None)
        self.check_inventory_button.setEnabled(False)
        self.statusBar().showMessage(f"Checking '{self._folder_path}'…")

        thread = QThread(self)
        worker = CandidateScanWorker(self._folder_path, self._loaded_requirements)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.scan_ready.connect(self._on_scan_ready)
        worker.scan_failed.connect(self._on_scan_failed)
        worker.scan_ready.connect(thread.quit)
        worker.scan_failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_scan_thread_finished)

        self._scan_thread = thread
        self._scan_worker = worker
        thread.start()

    def _on_scan_thread_finished(self) -> None:
        """Clear scan thread/worker references and re-enable Check Inventory."""
        self._scan_thread = None
        self._scan_worker = None
        self.check_inventory_button.setEnabled(True)

    def _on_scan_ready(self, scan: CandidateScan) -> None:
        """Render a successful inventory scan result."""
        self.results_model.set_scan(scan)
        self.results_view.resizeColumnsToContents()
        self.statusBar().showMessage(scan_summary_message(scan))

    def _on_scan_failed(self, message: str) -> None:
        """Clear the results and show a friendly error for a failed scan."""
        self.results_model.set_scan(None)
        self._show_error(message)

    def closeEvent(self, event) -> None:
        """Quit and wait (bounded) for any running worker thread, then close."""
        for thread in (self._import_thread, self._scan_thread):
            if thread is not None:
                thread.quit()
                finished = thread.wait(SUBSTITUTION_CLOSE_WAIT_TIMEOUT_MS)
                if not finished:
                    _LOGGER.warning(
                        "Substitution worker still running after %d ms; closing anyway.",
                        SUBSTITUTION_CLOSE_WAIT_TIMEOUT_MS,
                    )
        super().closeEvent(event)
