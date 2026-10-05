"""Main window: file pickers, Run Comparison, results table (UI-02).

Only ever calls into gdtf_comparer.core.comparator / core.models -- never
pygdtf or zipfile directly (D-16). Comparison work runs on a QThread-backed
ComparisonWorker so the GUI thread never blocks (D-14).
"""

import logging
import os
from typing import List, Optional, Sequence

from PySide6.QtCore import QThread, Qt, Slot
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableView,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from gdtf_comparer.core.comparator import attribute_catalog
from gdtf_comparer.core.errors import ProfileError, ProfileStorageError
from gdtf_comparer.core.models import ComparisonResult
from gdtf_comparer.core.profile_repository import (
    Profile,
    ProfileRepository,
    missing_attributes,
    normalize_profile_name,
    profile_name_key,
)
from gdtf_comparer.gui.attribute_picker import AttributePicker
from gdtf_comparer.gui.table_model import (
    AttributeSelectionProxyModel,
    BackgroundBrushDelegate,
    ComparisonTableModel,
    DifferencesOnlyProxyModel,
    UppercaseHeaderProxyModel,
)
from gdtf_comparer.gui.theme import current_theme_name, diff_highlight_color, theme_for_scheme
from gdtf_comparer.gui.worker import ComparisonWorker

GDTF_FILE_FILTER = "GDTF files (*.gdtf);;All files (*)"

# Status bar message shown when a comparison has rows but none of them are
# currently checked in the Attributes panel (D-03; _show_result_status).
NO_ATTRIBUTES_SELECTED_MESSAGE = (
    "No attributes selected. Check attributes in the Attributes panel to show them."
)

# Label for the "differences only" checkbox above the results table
# (Phase 2 D-06).
DIFFERENCES_ONLY_LABEL = "Show differences only"

# Status bar message shown when "Show differences only" is ticked and no
# selected row differs from the target (Phase 2 D-06; _show_result_status).
NO_DIFFERENCES_MESSAGE = (
    'No differences in the selected attributes. Untick "Show differences only" '
    "to see every row."
)

# Profile toolbar row (Phase 3 D-02, D-07): sits directly above the
# attribute picker at the top of the Attributes side panel.
PROFILE_PLACEHOLDER = "Load a profile…"
NO_PROFILES_PLACEHOLDER = "No saved profiles yet"
PROFILES_UNAVAILABLE_PLACEHOLDER = "Saved profiles unavailable"
SAVE_PROFILE_LABEL = "Save…"
SAVE_PROFILE_TITLE = "Save Compare Profile"
SAVE_PROFILE_PROMPT = "Name for the attributes checked now:"
PROFILE_COMBO_TOOLTIP = "Pick a saved compare profile to check exactly its attributes"
SAVE_PROFILE_TOOLTIP = "Save the attributes checked below as a named compare profile"
PROFILE_SAVED_TEMPLATE = "Saved profile '{name}' ({count} attributes)."
OVERWRITE_PROFILE_TEMPLATE = (
    "A profile named '{name}' already exists. Replace it with the attributes checked now?"
)

# Manage button + menu (Phase 3 D-05, D-07): sits in the same profile row as
# the dropdown and Save…, offering Rename… (and, from Plan 03-03 Task 2,
# Delete…) for whichever profile is currently shown in the dropdown. Disabled
# until a profile is shown there (RESEARCH Pitfall 3 carried over: the menu
# acts on the dropdown's current selection, never triggers a load itself).
MANAGE_PROFILES_LABEL = "Manage"
MANAGE_PROFILES_TOOLTIP = "Rename or delete the profile shown in the list"
RENAME_PROFILE_LABEL = "Rename…"
DELETE_PROFILE_LABEL = "Delete…"
RENAME_PROFILE_TITLE = "Rename Compare Profile"
RENAME_PROFILE_PROMPT = "New name for '{name}':"
PROFILE_RENAMED_TEMPLATE = "Renamed profile '{old}' to '{new}'."
DELETE_PROFILE_TEMPLATE = "Delete the profile '{name}'? This can't be undone."
PROFILE_DELETED_TEMPLATE = "Deleted profile '{name}'."

# Status bar message shown when a loaded profile has checked spec items that
# no file in the current comparison has a row for -- i.e. no file is loaded
# at all, or the loaded files simply lack the item (Phase 3 D-06). This is
# the highest-precedence branch inside _show_result_status, ahead of
# NO_ATTRIBUTES_SELECTED_MESSAGE: the spec items in question ARE checked,
# just absent from these particular files, so reporting "no attributes
# selected" would be misleading.
PROFILE_ITEMS_NOT_FOUND_TEMPLATE = (
    "{missing} of {total} spec items in '{name}' weren't found in these files: {names}."
)

# Status bar message shown when a profile is loaded before any comparison
# has finished (RESEARCH Pitfall 2): there is no current result to check the
# profile's spec items against yet, so D-06's not-found report cannot run.
# Written directly by _load_selected_profile, not by _show_result_status,
# since that method returns early while table_model.result() is None.
PROFILE_LOADED_NO_RESULT_TEMPLATE = (
    "Loaded profile '{name}' ({count} spec items). Run a comparison to check "
    "them against your files."
)

_LOGGER = logging.getLogger(__name__)

# How long closeEvent waits for a running worker thread before giving up and
# closing anyway (WR-01, T-01-29). Read at call time (not captured as a
# default argument) so tests can shrink it. Well above the 0.3 s worker used
# by test_close_during_comparison_does_not_crash, so a normal in-flight
# comparison is still waited for and finishes cleanly.
CLOSE_WAIT_TIMEOUT_MS = 3000

# Maximum width, in pixels, a value column is normally allowed to grow to
# after resizeColumnsToContents() (01-UAT.md G-01-2). Sized to fit
# "TARGET: " plus a typical fixture name at qt-material's 13 px Roboto
# header font (same in both themes). When there isn't room for every value
# column at this width -- i.e. more than a target plus one comparison at
# the default 1280 px window, with the 260 px Attributes side panel beside
# the table (D-02) -- _fit_columns_to_contents shrinks the cap further so
# any number of comparison files still fits without a horizontal scrollbar
# (WR-01), rather than only the single-comparison case. Read at call time by
# _fit_columns_to_contents, not captured as a default argument.
MAX_COLUMN_WIDTH_PX = 280

# Floor, in pixels, for the adaptive value-column cap in
# _fit_columns_to_contents (WR-01). Keeps a value column from being
# squeezed to an unreadable sliver when many comparison files are open at
# once -- past this point a horizontal scrollbar is the lesser evil.
MIN_VALUE_COLUMN_WIDTH_PX = 120

# The Attributes panel's drag floor (D-02: the panel cannot be fully
# collapsed, but the user can still narrow it). Raised from 220 to 240 as
# part of the G-03-1 fix (03-UAT.md) because 230 px of group width is the
# measured breakeven where the stacked Save…/Manage row (profile_actions_row,
# below) stops being squeezed below its own sizeHint (03-04-PLAN.md Design
# notes); the unchanged 260 px default already clears this with room to
# spare.
ATTRIBUTES_PANEL_MIN_WIDTH_PX = 240


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

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        profile_repository: Optional[ProfileRepository] = None,
    ) -> None:
        super().__init__(parent)
        self.target_file: str = ""
        self.compare_files: List[str] = []
        self._thread: Optional[QThread] = None
        self._worker: Optional[ComparisonWorker] = None
        self.profile_repository = (
            profile_repository if profile_repository is not None else ProfileRepository()
        )
        self._active_profile: Optional[Profile] = None

        self.setWindowTitle("GDTF Comparer")
        # 1280x720 (up from 1000x650) keeps the table area beside the 260 px
        # Attributes side panel (D-02) about 980 px wide -- the width Phase
        # 1's no-horizontal-scrollbar tests were tuned for.
        self.resize(1280, 720)
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
        self.selection_proxy = AttributeSelectionProxyModel(central)
        self.selection_proxy.setSourceModel(self.table_model)
        # "Show differences only" (Phase 2 D-06) sits after attribute
        # selection and before the header proxy: table_model -> selection_proxy
        # -> differences_proxy -> header_proxy -> table_view.
        self.differences_proxy = DifferencesOnlyProxyModel(central)
        self.differences_proxy.setSourceModel(self.selection_proxy)
        self.header_proxy = UppercaseHeaderProxyModel(central)
        self.header_proxy.setSourceModel(self.differences_proxy)
        self.table_view = QTableView(central)
        self.table_view.setModel(self.header_proxy)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        # Diff-highlight tint (DIFF-01, Phase 2 D-05): the delegate paints
        # each cell's BackgroundRole brush, which qt-material's own
        # QTableView::item rule otherwise suppresses (Design notes,
        # 02-03-PLAN.md).
        self.table_delegate = BackgroundBrushDelegate(self.table_view)
        self.table_view.setItemDelegate(self.table_delegate)
        self._apply_highlight_theme(current_theme_name(QApplication.instance()))
        # QHeaderView does not elide by default (ElideNone). GDTF file names
        # end with the revision (e.g. "...@V2.gdtf" / "...@V3.gdtf"), so
        # middle elision keeps that distinguishing ending visible when a
        # label is longer than its capped column width (G-01-2).
        self.table_view.horizontalHeader().setTextElideMode(Qt.TextElideMode.ElideMiddle)

        # Attributes side panel (D-01, D-02): always visible, never
        # collapsed away. Plan 02-03 adds a "differences only" toggle row
        # above the table inside results_panel.
        self.attributes_group = QGroupBox("Attributes", central)
        attributes_layout = QVBoxLayout(self.attributes_group)

        # Profile toolbar row (Phase 3 D-02, D-07; split into two stacked
        # rows for G-03-1, 03-UAT.md): sits directly above the attribute
        # picker as one consolidated block -- row 1 is the load dropdown
        # alone, row 2 is Save…+Manage -- rather than squeezing all three
        # widgets into a single row, which qt-material's uppercase +
        # padding chrome was clipping (03-04-PLAN.md Design notes).
        self.profile_row = QVBoxLayout()

        self.profile_combo_row = QHBoxLayout()
        self.profile_combo = QComboBox(self.attributes_group)
        self.profile_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.profile_combo.setMinimumContentsLength(8)
        self.profile_combo.setMaxVisibleItems(15)
        self.profile_combo.setToolTip(PROFILE_COMBO_TOOLTIP)
        self.profile_combo.activated.connect(self._load_selected_profile)
        self.profile_combo_row.addWidget(self.profile_combo, 1)
        self.profile_row.addLayout(self.profile_combo_row)

        self.profile_actions_row = QHBoxLayout()
        self.save_profile_button = QPushButton(SAVE_PROFILE_LABEL, self.attributes_group)
        self.save_profile_button.setToolTip(SAVE_PROFILE_TOOLTIP)
        self.save_profile_button.clicked.connect(self._save_profile)
        self.profile_actions_row.addWidget(self.save_profile_button, 1)

        self.manage_profile_button = QToolButton(self.attributes_group)
        self.manage_profile_button.setText(MANAGE_PROFILES_LABEL)
        self.manage_profile_button.setToolTip(MANAGE_PROFILES_TOOLTIP)
        self.manage_profile_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.manage_profile_menu = QMenu(self.manage_profile_button)
        self.rename_profile_action = self.manage_profile_menu.addAction(RENAME_PROFILE_LABEL)
        self.rename_profile_action.triggered.connect(self._rename_selected_profile)
        self.delete_profile_action = self.manage_profile_menu.addAction(DELETE_PROFILE_LABEL)
        self.delete_profile_action.triggered.connect(self._delete_selected_profile)
        self.manage_profile_button.setMenu(self.manage_profile_menu)
        self.profile_actions_row.addWidget(self.manage_profile_button, 1)
        self.profile_row.addLayout(self.profile_actions_row)

        # Only toggles enabled state (never loads a profile): the dropdown's
        # own activated connection (above) is the sole load trigger, so
        # repopulating the combo after a save/rename/delete never fires a
        # load through this connection either (RESEARCH Pitfall 3).
        self.profile_combo.currentIndexChanged.connect(self._update_profile_actions)

        attributes_layout.addLayout(self.profile_row)

        self.attribute_picker = AttributePicker(self.attributes_group)
        attributes_layout.addWidget(self.attribute_picker)
        self.attributes_group.setMinimumWidth(ATTRIBUTES_PANEL_MIN_WIDTH_PX)
        self.attribute_picker.selection_changed.connect(self._apply_attribute_selection)

        self.results_panel = QWidget(central)
        results_layout = QVBoxLayout(self.results_panel)
        results_layout.setContentsMargins(0, 0, 0, 0)

        # "Show differences only" toggle row (Phase 2 D-06): above the
        # table, on top of the cell highlighting, never a replacement for it.
        toggle_row = QHBoxLayout()
        self.differences_only_checkbox = QCheckBox(DIFFERENCES_ONLY_LABEL, self.results_panel)
        self.differences_only_checkbox.setChecked(False)
        self.differences_only_checkbox.toggled.connect(self._apply_differences_only)
        toggle_row.addWidget(self.differences_only_checkbox)
        toggle_row.addStretch(1)
        results_layout.addLayout(toggle_row)

        results_layout.addWidget(self.table_view)

        self.content_splitter = QSplitter(Qt.Orientation.Horizontal, central)
        self.content_splitter.addWidget(self.attributes_group)
        self.content_splitter.addWidget(self.results_panel)
        # D-02: the Attributes panel cannot be collapsed away by dragging.
        self.content_splitter.setChildrenCollapsible(False)
        self.content_splitter.setStretchFactor(0, 0)
        self.content_splitter.setStretchFactor(1, 1)
        self.content_splitter.setSizes([260, 1020])
        layout.addWidget(self.content_splitter)

        # Live OS light/dark switch re-tints the table without a re-run
        # (DIFF-01, Phase 2 D-05, Task 3).
        style_hints = QApplication.instance().styleHints()
        style_hints.colorSchemeChanged.connect(self._on_color_scheme_changed)

        self.statusBar().showMessage("Ready")
        self._refresh_profile_combo()

    @Slot(Qt.ColorScheme)
    def _on_color_scheme_changed(self, scheme) -> None:
        """Re-tint the table's diff highlight when the OS color scheme changes.

        Parameters:
            scheme: The new Qt.ColorScheme reported by
                QApplication.styleHints().colorSchemeChanged.

        Derives the theme name from scheme itself via theme_for_scheme -- the
        same mapping gui.theme.OsThemeFollower applies -- rather than reading
        THEME_PROPERTY, so the tint is right whichever slot Qt runs first.
        Decorated with @Slot so Qt drops the connection when this window is
        destroyed (same pattern as OsThemeFollower.on_color_scheme_changed).
        Never re-runs the comparison or touches the ComparisonResult
        (prohibition 1, 02-03-PLAN.md).
        """
        self._apply_highlight_theme(theme_for_scheme(scheme))

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
        self.attribute_picker.set_catalog(attribute_catalog(result))
        self._apply_attribute_selection()

    def _apply_highlight_theme(self, theme_name: str) -> None:
        """Set the table's diff-highlight tint from a qt-material theme name.

        Parameters:
            theme_name: A qt-material theme file name (e.g. "dark_blue.xml").

        The only place the table's highlight color is set (DIFF-01, Phase 2
        D-05): runs once per theme (at construction and on a live OS
        light/dark switch, Task 3), never per painted cell.
        """
        self.table_model.set_highlight_color(diff_highlight_color(theme_name))

    def _apply_attribute_selection(self) -> None:
        """Push the picker's checked set into the selection proxy and refit.

        Connected to AttributePicker.selection_changed, and also called
        directly after on_comparison_ready seeds a fresh catalog (D-03: the
        checked set is the only thing that decides which rows show).
        """
        self.selection_proxy.set_selected_attributes(self.attribute_picker.checked_attributes())
        if self.table_model.result() is not None:
            self._fit_columns_to_contents()
        self._show_result_status()

    def _apply_differences_only(self, checked: bool) -> None:
        """Push the "Show differences only" checkbox state into its proxy.

        Parameters:
            checked: The checkbox's new state.

        Connected to differences_only_checkbox.toggled (Phase 2 D-06): the
        toggle is kept on top of the cell highlighting, never a replacement
        for it, and applies to whichever result is current (including one
        that arrives later, since run_comparison never touches the checkbox).
        """
        self.differences_proxy.set_differences_only(checked)
        if self.table_model.result() is not None:
            self._fit_columns_to_contents()
        self._show_result_status()

    def _profile_items_not_found_message(self, result: ComparisonResult) -> Optional[str]:
        """Return the D-06 "not found" message for the active profile, or None.

        Parameters:
            result: The CURRENT comparison result. available is computed
                fresh from this result's attribute_catalog on every call --
                never from gui.attribute_picker.AttributePicker._known, which
                is a sticky superset across comparison runs and would
                undercount items genuinely absent from these files (RESEARCH
                Pitfall 1). This method only reads state; it never changes
                the checked set, the rendered rows or result itself, and it
                is recomputed every time _show_result_status runs -- i.e.
                after every selection change and every re-run.

        Returns:
            None when no profile is loaded (self._active_profile is None),
            when the profile's checked spec items are empty, or when every
            one of them has a row in result's catalog. Otherwise
            PROFILE_ITEMS_NOT_FOUND_TEMPLATE filled in with how many of how
            many spec items are missing, the profile's name, and the missing
            attribute names (category omitted) sorted by (category,
            attribute) and joined with ", ".
        """
        if self._active_profile is None:
            return None

        spec = self._active_profile.attributes & self.attribute_picker.checked_attributes()
        if not spec:
            return None

        available = frozenset(
            (category, attribute)
            for category, attributes in attribute_catalog(result)
            for attribute in attributes
        )
        missing = missing_attributes(spec, available)
        if not missing:
            return None

        return PROFILE_ITEMS_NOT_FOUND_TEMPLATE.format(
            missing=len(missing),
            total=len(spec),
            name=self._active_profile.name,
            names=", ".join(attribute for _, attribute in sorted(missing)),
        )

    def _show_result_status(self) -> None:
        """Show the status bar message matching the current result/selection.

        The single place that writes the result status: does nothing while
        no result is loaded. The highest-precedence case is Phase 3 D-06's
        "spec items not found" report (_profile_items_not_found_message):
        when it applies, it is shown alone, or combined with
        NO_DIFFERENCES_MESSAGE when "Show differences only" also empties the
        table -- this replaces NO_ATTRIBUTES_SELECTED_MESSAGE in that case,
        since the profile's spec items ARE checked, just absent from these
        files, so "no attributes selected" would be misleading. Below that,
        NO_ATTRIBUTES_SELECTED_MESSAGE when the result has rows but none are
        currently selected, then NO_DIFFERENCES_MESSAGE when "Show
        differences only" is ticked and every selected row agrees with the
        target, otherwise the normal "Compared N file(s)..." summary (Phase
        2 D-06).
        """
        result = self.table_model.result()
        if result is None:
            return

        not_found = self._profile_items_not_found_message(result)
        if not_found is not None:
            if (
                self.differences_proxy.differences_only()
                and self.selection_proxy.rowCount() > 0
                and self.differences_proxy.rowCount() == 0
            ):
                self.statusBar().showMessage(f"{not_found} {NO_DIFFERENCES_MESSAGE}")
            else:
                self.statusBar().showMessage(not_found)
            return

        if self.table_model.rowCount() > 0 and self.selection_proxy.rowCount() == 0:
            self.statusBar().showMessage(NO_ATTRIBUTES_SELECTED_MESSAGE)
            return
        if (
            self.differences_proxy.differences_only()
            and self.selection_proxy.rowCount() > 0
            and self.differences_proxy.rowCount() == 0
        ):
            self.statusBar().showMessage(NO_DIFFERENCES_MESSAGE)
            return
        self.statusBar().showMessage(
            f"Compared {len(result.comparisons)} file(s) against {result.target.file_name}"
        )

    def _fit_columns_to_contents(self) -> None:
        """Size columns to their contents, then cap each value column's width.

        Only value columns (COL_TARGET onward, i.e. one per compared
        fixture) are capped: Category/Element/Attribute are left at their
        natural content width (CR-01). Element in particular shows an
        unbounded geometry path (table_model.py), and the table view's
        *cell* elide mode is not middle-elided the way the header is -- so
        capping it can right-elide two different element paths down to
        identical visible text.

        The cap itself adapts to how many value columns there are: it is
        the smaller of MAX_COLUMN_WIDTH_PX and an even share of the space
        left in the viewport after the fixed columns, floored at
        MIN_VALUE_COLUMN_WIDTH_PX (WR-01). MAX_COLUMN_WIDTH_PX alone was
        only ever sized for a target plus one comparison; sharing the
        remaining viewport width keeps *any* number of comparison files --
        the product's actual "compare against any number of files" use
        case -- inside the viewport without a horizontal scrollbar.

        The clamp is applied per section after resizeColumnsToContents(),
        rather than via a header-wide maximum section size, so the stretched
        last section still fills the window (setStretchLastSection) and the
        user can still drag any column wider than the cap to read a full
        name in the header or a cell (G-01-2).
        """
        self.table_view.resizeColumnsToContents()
        header = self.table_view.horizontalHeader()

        num_value_columns = header.count() - ComparisonTableModel.COL_TARGET
        value_cap = MAX_COLUMN_WIDTH_PX
        if num_value_columns > 0:
            fixed_width = sum(
                header.sectionSize(section)
                for section in range(ComparisonTableModel.COL_TARGET)
            )
            available_width = max(0, self.table_view.viewport().width() - fixed_width)
            value_cap = max(
                MIN_VALUE_COLUMN_WIDTH_PX,
                min(MAX_COLUMN_WIDTH_PX, available_width // num_value_columns),
            )

        for section in range(ComparisonTableModel.COL_TARGET, header.count()):
            if header.sectionSize(section) > value_cap:
                header.resizeSection(section, value_cap)

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

    def _refresh_profile_combo(self, select_name: Optional[str] = None) -> None:
        """Repopulate the profile dropdown from disk.

        Parameters:
            select_name: When given, the combo's current index is set to
                the item whose text equals select_name exactly, if present.

        Repopulating never loads a profile by itself (RESEARCH Pitfall 3):
        self.profile_combo.activated is only ever emitted by a user's own
        click/selection, never by clear()/addItem()/setCurrentIndex() below,
        so this is always safe to call after a save.

        A damaged, oversized or newer-version profiles.json (T-03-01) never
        crashes the app: the combo is disabled with
        PROFILES_UNAVAILABLE_PLACEHOLDER and the status bar explains why,
        with no modal dialog (this also runs during __init__, before any
        window is shown). The Save… button stays enabled, so attempting a
        save surfaces the same reason through _save_profile's own
        ProfileError handling.
        """
        try:
            profiles = self.profile_repository.load_all()
        except ProfileStorageError as exc:
            self.profile_combo.clear()
            self.profile_combo.setEnabled(False)
            self.profile_combo.setPlaceholderText(PROFILES_UNAVAILABLE_PLACEHOLDER)
            self.statusBar().showMessage(str(exc))
            self._update_profile_actions()
            return

        self.profile_combo.clear()
        for profile in profiles:
            self.profile_combo.addItem(profile.name)
        self.profile_combo.setEnabled(bool(profiles))
        self.profile_combo.setPlaceholderText(
            PROFILE_PLACEHOLDER if profiles else NO_PROFILES_PLACEHOLDER
        )

        index = -1
        if select_name is not None:
            for candidate_index in range(self.profile_combo.count()):
                if self.profile_combo.itemText(candidate_index) == select_name:
                    index = candidate_index
                    break
        self.profile_combo.setCurrentIndex(index)
        self._update_profile_actions()

    def _update_profile_actions(self) -> None:
        """Enable Manage/Rename only while a profile is shown in the dropdown.

        Connected to profile_combo.currentIndexChanged (never activated):
        this only toggles enabled state and never loads a profile, so a
        profile shown in the dropdown without the user choosing it (e.g. a
        programmatic _refresh_profile_combo(select_name=...) after a save
        or rename) never fires a load through this connection either
        (RESEARCH Pitfall 3 carried to the Manage button). Also called
        directly from _refresh_profile_combo, since the index can stay at
        -1 across a repopulation, in which case currentIndexChanged never
        fires.
        """
        has_selection = self.profile_combo.isEnabled() and self.profile_combo.currentIndex() >= 0
        self.manage_profile_button.setEnabled(has_selection)
        self.rename_profile_action.setEnabled(has_selection)
        self.delete_profile_action.setEnabled(has_selection)

    def _rename_selected_profile(self) -> None:
        """Rename the profile currently shown in the dropdown (D-05).

        Prompts for a new name pre-filled with the current one; cancelling
        leaves everything unchanged. A name already used by a different
        saved profile (ignoring case, surrounding whitespace and Unicode
        form) is refused with a friendly message and nothing is written --
        renaming is never a silent overwrite (T-03-15). Never touches the
        checked attributes or the current comparison: when the renamed
        profile is the one currently loaded, only its tracked name is
        updated, so the D-06 not-found report keeps naming it correctly
        under the new name instead of stopping or going stale (D-06).
        """
        index = self.profile_combo.currentIndex()
        if index < 0:
            return
        old_name = self.profile_combo.itemText(index)

        raw = self._ask_profile_name(
            RENAME_PROFILE_TITLE, RENAME_PROFILE_PROMPT.format(name=old_name), old_name
        )
        if raw is None:
            return

        try:
            profile = self.profile_repository.rename(old_name, raw)
        except ProfileError as exc:
            self._show_error(str(exc))
            return

        if self._active_profile is not None and profile_name_key(
            self._active_profile.name
        ) == profile_name_key(old_name):
            self._active_profile = profile

        self._refresh_profile_combo(select_name=profile.name)
        self.statusBar().showMessage(
            PROFILE_RENAMED_TEMPLATE.format(old=old_name, new=profile.name)
        )

    def _delete_selected_profile(self) -> None:
        """Delete the profile currently shown in the dropdown, after asking (D-05).

        Asks "Delete the profile '<name>'? This can't be undone." first,
        defaulting to No (T-03-14): answering No or closing the dialog
        leaves the profile untouched. Yes removes it from the dropdown and
        from profiles.json for good. Never touches the checked attributes
        or the current comparison table -- only the dropdown and, when the
        deleted profile is the one currently loaded, self._active_profile
        (cleared, so the D-06 not-found report stops naming a profile that
        no longer exists, D-06).
        """
        index = self.profile_combo.currentIndex()
        if index < 0:
            return
        name = self.profile_combo.itemText(index)

        if not self._confirm(DELETE_PROFILE_TEMPLATE.format(name=name)):
            return

        try:
            self.profile_repository.delete(name)
        except ProfileError as exc:
            self._show_error(str(exc))
            return

        if self._active_profile is not None and profile_name_key(
            self._active_profile.name
        ) == profile_name_key(name):
            self._active_profile = None

        self._refresh_profile_combo()
        self.statusBar().showMessage(PROFILE_DELETED_TEMPLATE.format(name=name))

    def _ask_profile_name(self, title: str, label: str, default_text: str = "") -> Optional[str]:
        """Prompt for a profile name.

        Parameters:
            title: The dialog's window title.
            label: The prompt text shown above the input field.
            default_text: Text pre-filled into the input field.

        Returns:
            The entered text, or None if the user cancelled. This is the
            single place the name prompt opens, so tests can monkeypatch it
            directly instead of driving a real modal dialog.
        """
        text, ok = QInputDialog.getText(self, title, label, QLineEdit.EchoMode.Normal, default_text)
        return text if ok else None

    def _save_profile(self) -> None:
        """Save the currently checked attributes as a named compare profile.

        Saving under a name that already exists (ignoring case, surrounding
        whitespace and Unicode form, D-04) asks "Replace it?" first, with No
        as the safe default; answering No leaves the existing profile
        untouched and writes nothing.
        """
        raw_name = self._ask_profile_name(
            SAVE_PROFILE_TITLE,
            SAVE_PROFILE_PROMPT,
            self._active_profile.name if self._active_profile else "",
        )
        if raw_name is None:
            return

        try:
            name = normalize_profile_name(raw_name)
            existing = self.profile_repository.find(name)
            if existing is not None and not self._confirm(
                OVERWRITE_PROFILE_TEMPLATE.format(name=existing.name)
            ):
                return
            profile = self.profile_repository.save(name, self.attribute_picker.checked_attributes())
        except ProfileError as exc:
            self._show_error(str(exc))
            return

        self._active_profile = profile
        self._refresh_profile_combo(select_name=profile.name)
        self.statusBar().showMessage(
            PROFILE_SAVED_TEMPLATE.format(name=profile.name, count=len(profile.attributes))
        )

    def _load_selected_profile(self, index: int) -> None:
        """Load the profile at index into the attribute picker (D-02, D-03).

        Parameters:
            index: The combo index the user just picked. Connected to
                profile_combo.activated only (RESEARCH Pitfall 3), so this
                never runs from a programmatic repopulation.

        Replaces the picker's checked set entirely via
        AttributePicker.set_checked(), which fires selection_changed exactly
        once; the existing selection_changed -> _apply_attribute_selection
        chain then re-filters the table, refits columns and refreshes the
        status message -- this method never duplicates that work, EXCEPT
        before a comparison has ever finished (table_model.result() is
        None, RESEARCH Pitfall 2): in that state _show_result_status returns
        immediately without writing anything, since there is no current
        result to check the profile's spec items against, so this method
        writes PROFILE_LOADED_NO_RESULT_TEMPLATE itself to tell the user to
        run a comparison instead of guessing. D-06's not-found report never
        appears without a current result.
        """
        if index < 0:
            return
        name = self.profile_combo.itemText(index)
        try:
            profile = self.profile_repository.get(name)
        except ProfileError as exc:
            self._show_error(str(exc))
            self._refresh_profile_combo()
            return

        self._active_profile = profile
        self.attribute_picker.set_checked(profile.attributes)
        if self.table_model.result() is None:
            # No comparison has finished yet (or one is running): there is
            # no current result to check the profile's spec items against,
            # so tell the user to run one instead of guessing (RESEARCH
            # Pitfall 2). Once a result exists, the coalesced
            # selection_changed set_checked() just emitted reaches
            # _apply_attribute_selection -> _show_result_status, which owns
            # the status bar from then on and must not be second-guessed
            # here.
            self.statusBar().showMessage(
                PROFILE_LOADED_NO_RESULT_TEMPLATE.format(
                    name=profile.name, count=len(profile.attributes)
                )
            )

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

    def _confirm(self, message: str) -> bool:
        """Ask a plain-text Yes/No question, defaulting to No.

        Parameters:
            message: The question to show. Always rendered as plain text
                (Qt.TextFormat.PlainText) so a profile name is never
                interpreted as rich text (T-01-17 carried).

        Returns:
            True only if the user clicks Yes. Used for the D-04 save-over-
            an-existing-name confirmation here, and for the D-05 delete
            confirmation in Plan 03-03. Defaults to No (both as the
            QMessageBox default button and the escape/close action) so a
            stray Enter or Escape never destroys a saved profile.
        """
        box = QMessageBox(
            QMessageBox.Icon.Question,
            "GDTF Comparer",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            self,
        )
        box.setTextFormat(Qt.TextFormat.PlainText)
        box.setDefaultButton(QMessageBox.StandardButton.No)
        box.setEscapeButton(QMessageBox.StandardButton.No)
        box.exec()
        return box.clickedButton() == box.button(QMessageBox.StandardButton.Yes)
