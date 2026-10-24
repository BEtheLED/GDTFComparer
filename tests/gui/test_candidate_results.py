"""Failure rows, legend, tooltips and one-check-at-a-time for the ranked
Check Inventory results table (D-10, D-11, D-12, SUB-04 concurrency).
"""

from PySide6.QtCore import Qt

from gdtf_comparer.core.models import CATEGORY_PHYSICAL, AttributeKey
from gdtf_comparer.core.requirements_repository import save_requirements
from gdtf_comparer.core.substitution import (
    NO_GDTF_FILES_TEMPLATE,
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
    MATCH_STATE_ROLE,
)
from gdtf_comparer.gui.substitution_window import SubstitutionWindow

WEIGHT_KEY = AttributeKey(CATEGORY_PHYSICAL, "", "Weight")
WEIGHT_TOLERANCE = 2.0


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
