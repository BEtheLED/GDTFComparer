"""Failure rows, legend, tooltips and one-check-at-a-time for the ranked
Check Inventory results table (D-10, D-11, D-12, SUB-04 concurrency).
"""

import threading

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

import gdtf_comparer.gui.worker as worker_module
from gdtf_comparer.core.errors import CandidateFolderError
from gdtf_comparer.core.models import CATEGORY_PHYSICAL, AttributeKey
from gdtf_comparer.core.requirements_repository import save_requirements
from gdtf_comparer.core.substitution import (
    NO_GDTF_FILES_TEMPLATE,
    DIRECTION_LABELS,
    Direction,
    Requirement,
    RequirementSet,
    scan_candidate_folder,
    scan_summary_message,
)
from gdtf_comparer.gui.candidate_results import (
    COL_FILE,
    COL_FIXTURE,
    COL_SUMMARY,
    FAILURE_FIXTURE_TEXT,
    FAILURE_ROW_ROLE,
    FIRST_REQUIREMENT_COLUMN,
    LEGEND_TEXT,
    MATCH_STATE_ROLE,
    NOT_LISTED_TEXT,
    STATE_DESCRIPTIONS,
)
from gdtf_comparer.gui.substitution_window import SubstitutionWindow
from gdtf_comparer.gui.theme import DARK_THEME, LIGHT_THEME, apply_theme

WEIGHT_KEY = AttributeKey(CATEGORY_PHYSICAL, "", "Weight")
WEIGHT_TOLERANCE = 2.0


@pytest.fixture
def capture_dialogs(monkeypatch):
    """Monkeypatch QMessageBox.exec to record (text, textFormat) and return 0."""
    dialogs = []

    def _fake_exec(self):
        dialogs.append((self.text(), self.textFormat()))
        return 0

    monkeypatch.setattr(QMessageBox, "exec", _fake_exec)
    return dialogs


def _weight_requirements():
    return RequirementSet(
        "Acme Spot",
        "Acme",
        "Acme@Spot.gdtf",
        (Requirement(key=WEIGHT_KEY, target=15.0, direction=Direction.LOWER, tolerance=WEIGHT_TOLERANCE),),
    )


def _open_requirements_and_check(qtbot, monkeypatch, tmp_path, requirement_set, folder):
    window = SubstitutionWindow()
    qtbot.addWidget(window)

    saved_path = tmp_path / "reqs.json"
    save_requirements(str(saved_path), requirement_set)
    monkeypatch.setattr(window, "_ask_open_requirements_path", lambda: str(saved_path))
    qtbot.mouseClick(window.open_requirements_button, Qt.MouseButton.LeftButton)

    monkeypatch.setattr(window, "_ask_inventory_folder", lambda: str(folder))
    qtbot.mouseClick(window.choose_folder_button, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(window.check_inventory_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.check_inventory_button.isEnabled(), timeout=10000)

    return window


def test_unreadable_files_listed_below_candidates(qtbot, make_gdtf, tmp_path, monkeypatch):
    folder = tmp_path / "inventory"
    folder.mkdir()
    make_gdtf("inventory/Beta.gdtf", weight=14.0)
    make_gdtf("inventory/Gamma.gdtf", weight=16.5)
    (folder / "Broken.gdtf").write_bytes(b"not a zip")

    requirement_set = _weight_requirements()
    window = _open_requirements_and_check(qtbot, monkeypatch, tmp_path, requirement_set, folder)

    model = window.results_model
    assert model.rowCount() == 3

    assert model.index(0, 0).data(FAILURE_ROW_ROLE) is False
    assert model.index(1, 0).data(FAILURE_ROW_ROLE) is False
    assert model.index(2, 0).data(FAILURE_ROW_ROLE) is True

    assert model.index(2, COL_FIXTURE).data() == FAILURE_FIXTURE_TEXT
    assert model.index(2, COL_FILE).data() == "Broken.gdtf"
    assert "not a valid GDTF file" in model.index(2, COL_SUMMARY).data()

    requirement_cell = model.index(2, FIRST_REQUIREMENT_COLUMN)
    assert requirement_cell.data(Qt.ItemDataRole.BackgroundRole) is None
    assert requirement_cell.data(MATCH_STATE_ROLE) is None

    scan = scan_candidate_folder(str(folder), requirement_set)
    assert window.statusBar().currentMessage() == scan_summary_message(scan)


def test_empty_folder_message_in_window(qtbot, tmp_path, monkeypatch):
    folder = tmp_path / "empty"
    folder.mkdir()

    requirement_set = _weight_requirements()
    window = _open_requirements_and_check(qtbot, monkeypatch, tmp_path, requirement_set, folder)

    assert window.results_model.rowCount() == 0
    assert window.statusBar().currentMessage() == NO_GDTF_FILES_TEMPLATE.format(folder=str(folder))


# --- Task 3: colors visible in both themes, words everywhere, one check at a time ---


def _three_candidate_folder(tmp_path, make_gdtf):
    """Beta (green), Gamma (yellow), Delta (red) against WEIGHT_KEY's requirement."""
    folder = tmp_path / "inventory"
    folder.mkdir()
    make_gdtf("inventory/Beta.gdtf", name="Beta", weight=14.0)
    make_gdtf("inventory/Gamma.gdtf", name="Gamma", weight=16.5)
    make_gdtf("inventory/Delta.gdtf", name="Delta", weight=20.0)
    return folder


def _sample_pixel_at_right_edge(view, row: int, column: int):
    """Sample a pixel near the right edge of a visible cell's rect."""
    index = view.model().index(row, column)
    rect = view.visualRect(index)
    point = rect.topRight()
    point.setX(point.x() - 3)
    point.setY(rect.center().y())
    image = view.viewport().grab().toImage()
    return image.pixelColor(point)


@pytest.mark.parametrize("theme", [LIGHT_THEME, DARK_THEME])
def test_traffic_lights_paint_in_both_themes(qapp, qtbot, make_gdtf, tmp_path, monkeypatch, theme):
    apply_theme(qapp, theme)
    try:
        folder = _three_candidate_folder(tmp_path, make_gdtf)
        window = _open_requirements_and_check(qtbot, monkeypatch, tmp_path, _weight_requirements(), folder)
        window.tabs.setCurrentWidget(window.check_inventory_tab)
        window.show()
        qtbot.waitExposed(window)

        view = window.results_view
        assert view.model().rowCount() == 3

        for row in range(3):
            requirement_pixel = _sample_pixel_at_right_edge(view, row, FIRST_REQUIREMENT_COLUMN)
            file_pixel = _sample_pixel_at_right_edge(view, row, COL_FILE)
            assert requirement_pixel != file_pixel

        green_pixel = _sample_pixel_at_right_edge(view, 0, FIRST_REQUIREMENT_COLUMN)
        assert green_pixel.green() > green_pixel.red()

        yellow_pixel = _sample_pixel_at_right_edge(view, 1, FIRST_REQUIREMENT_COLUMN)
        assert yellow_pixel.red() > yellow_pixel.blue()
        assert yellow_pixel.green() > yellow_pixel.blue()

        red_pixel = _sample_pixel_at_right_edge(view, 2, FIRST_REQUIREMENT_COLUMN)
        assert red_pixel.red() > red_pixel.green()
    finally:
        apply_theme(qapp, LIGHT_THEME)


def test_cell_tooltips_explain_in_words(qtbot, make_gdtf, tmp_path, monkeypatch):
    folder = _three_candidate_folder(tmp_path, make_gdtf)
    window = _open_requirements_and_check(qtbot, monkeypatch, tmp_path, _weight_requirements(), folder)

    model = window.results_model
    expected_candidate_text = ["14", "16.5", "20"]
    for row, candidate_text in enumerate(expected_candidate_text):
        index = model.index(row, FIRST_REQUIREMENT_COLUMN)
        tooltip = index.data(Qt.ItemDataRole.ToolTipRole)
        assert f"Candidate: {candidate_text}" in tooltip
        assert "Your fixture: 15" in tooltip
        assert DIRECTION_LABELS[Direction.LOWER] in tooltip
        state = index.data(MATCH_STATE_ROLE)
        assert STATE_DESCRIPTIONS[state] in tooltip

    # A missing value's display text is NOT_LISTED_TEXT and its tooltip
    # says so in words too.
    missing_folder = tmp_path / "missing"
    missing_folder.mkdir()
    make_gdtf("missing/NoWeight.gdtf", name="NoWeight", weight=None)
    missing_window = _open_requirements_and_check(
        qtbot, monkeypatch, tmp_path, _weight_requirements(), missing_folder
    )
    missing_index = missing_window.results_model.index(0, FIRST_REQUIREMENT_COLUMN)
    assert missing_index.data() == NOT_LISTED_TEXT
    missing_tooltip = missing_index.data(Qt.ItemDataRole.ToolTipRole)
    assert f"Candidate: {NOT_LISTED_TEXT}" in missing_tooltip
    assert "Your fixture: 15" in missing_tooltip


def test_result_column_counts_in_words(qtbot, make_gdtf, tmp_path, monkeypatch):
    folder = _three_candidate_folder(tmp_path, make_gdtf)
    window = _open_requirements_and_check(qtbot, monkeypatch, tmp_path, _weight_requirements(), folder)

    assert window.results_model.index(0, COL_SUMMARY).data() == "1 green · 0 yellow · 0 red"


def test_legend_shown_above_results(qtbot):
    window = SubstitutionWindow()
    qtbot.addWidget(window)
    window.tabs.setCurrentWidget(window.check_inventory_tab)
    window.show()
    qtbot.waitExposed(window)

    assert window.legend_label.text() == LEGEND_TEXT
    assert window.legend_label.textFormat() == Qt.TextFormat.PlainText
    assert window.legend_label.isVisible()

    legend_top = window.legend_label.mapTo(window, window.legend_label.rect().topLeft()).y()
    results_top = window.results_view.mapTo(window, window.results_view.rect().topLeft()).y()
    assert legend_top < results_top


def test_check_button_disabled_while_checking(qtbot, make_gdtf, tmp_path, monkeypatch):
    """SUB-04 concurrency: only one inventory check runs at a time."""
    folder = _three_candidate_folder(tmp_path, make_gdtf)
    requirement_set = _weight_requirements()
    saved_path = tmp_path / "reqs.json"
    save_requirements(str(saved_path), requirement_set)

    window = SubstitutionWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(window, "_ask_open_requirements_path", lambda: str(saved_path))
    qtbot.mouseClick(window.open_requirements_button, Qt.MouseButton.LeftButton)
    monkeypatch.setattr(window, "_ask_inventory_folder", lambda: str(folder))
    qtbot.mouseClick(window.choose_folder_button, Qt.MouseButton.LeftButton)

    real_scan = worker_module.scan_candidate_folder
    release = threading.Event()
    call_count = []

    def _gated(*args, **kwargs):
        call_count.append(1)
        release.wait(timeout=10)
        return real_scan(*args, **kwargs)

    monkeypatch.setattr(worker_module, "scan_candidate_folder", _gated)

    qtbot.mouseClick(window.check_inventory_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: len(call_count) == 1, timeout=5000)

    assert window.check_inventory_button.isEnabled() is False
    assert window.results_model.rowCount() == 0

    window.check_inventory()
    assert len(call_count) == 1

    release.set()
    qtbot.waitUntil(
        lambda: window.check_inventory_button.isEnabled() and window.results_model.rowCount() == 3,
        timeout=10000,
    )
    assert len(call_count) == 1


def test_new_check_replaces_results(qtbot, make_gdtf, tmp_path, monkeypatch):
    folder_a = tmp_path / "inventory_a"
    folder_a.mkdir()
    make_gdtf("inventory_a/Alpha.gdtf", name="Alpha", weight=14.0)

    folder_b = tmp_path / "inventory_b"
    folder_b.mkdir()
    make_gdtf("inventory_b/Omega.gdtf", name="Omega", weight=14.0)
    make_gdtf("inventory_b/Zenith.gdtf", name="Zenith", weight=14.0)

    requirement_set = _weight_requirements()
    saved_path = tmp_path / "reqs.json"
    save_requirements(str(saved_path), requirement_set)

    window = SubstitutionWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(window, "_ask_open_requirements_path", lambda: str(saved_path))
    qtbot.mouseClick(window.open_requirements_button, Qt.MouseButton.LeftButton)

    monkeypatch.setattr(window, "_ask_inventory_folder", lambda: str(folder_a))
    qtbot.mouseClick(window.choose_folder_button, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(window.check_inventory_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(
        lambda: window.check_inventory_button.isEnabled() and window.results_model.rowCount() == 1,
        timeout=10000,
    )

    monkeypatch.setattr(window, "_ask_inventory_folder", lambda: str(folder_b))
    qtbot.mouseClick(window.choose_folder_button, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(window.check_inventory_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(
        lambda: window.check_inventory_button.isEnabled() and window.results_model.rowCount() == 2,
        timeout=10000,
    )

    names = {window.results_model.index(row, COL_FILE).data() for row in range(2)}
    assert names == {"Omega.gdtf", "Zenith.gdtf"}


def test_failed_check_clears_results(qtbot, make_gdtf, tmp_path, monkeypatch, capture_dialogs):
    folder = _three_candidate_folder(tmp_path, make_gdtf)
    requirement_set = _weight_requirements()
    window = _open_requirements_and_check(qtbot, monkeypatch, tmp_path, requirement_set, folder)
    assert window.results_model.rowCount() == 3

    def _raise(*args, **kwargs):
        raise CandidateFolderError("boom")

    monkeypatch.setattr(worker_module, "scan_candidate_folder", _raise)
    qtbot.mouseClick(window.check_inventory_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.check_inventory_button.isEnabled(), timeout=10000)

    assert window.results_model.rowCount() == 0
    assert len(capture_dialogs) == 1
    text, text_format = capture_dialogs[0]
    assert text == "boom"
    assert text_format == Qt.TextFormat.PlainText
