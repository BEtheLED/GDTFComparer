"""GUI tests for the requirements file: fresh-window open, and a refused
open/save leaving previous state untouched (SUB-03, D-07).
"""

from typing import List, Tuple

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from gdtf_comparer.core.errors import RequirementsFileError
from gdtf_comparer.core.models import CATEGORY_PHYSICAL, AttributeKey
from gdtf_comparer.core.requirements_repository import load_requirements, save_requirements
from gdtf_comparer.core.substitution import Direction, Requirement, RequirementSet, describe_requirements
from gdtf_comparer.gui.substitution_window import SubstitutionWindow

from tests.conftest import build_gdtf_bytes, fixture_xml

WEIGHT_KEY = AttributeKey(CATEGORY_PHYSICAL, "", "Weight")


@pytest.fixture
def capture_dialogs(monkeypatch):
    """Monkeypatch QMessageBox.exec to record (text, textFormat) and return 0."""
    dialogs: List[Tuple[str, "Qt.TextFormat"]] = []

    def _fake_exec(self):
        dialogs.append((self.text(), self.textFormat()))
        return 0

    monkeypatch.setattr(QMessageBox, "exec", _fake_exec)
    return dialogs


def _good_requirement_set():
    return RequirementSet(
        fixture_name="Acme Spot",
        manufacturer="Acme",
        gdtf_file="Acme@Spot.gdtf",
        requirements=(Requirement(WEIGHT_KEY, 15.0, Direction.LOWER, 2.0),),
    )


def _ld_mvr(make_mvr):
    """Write a minimal MVR with one "Acme Spot" fixture instance."""
    ld_bytes = build_gdtf_bytes(name="Acme Spot", manufacturer="Acme", weight=15.0)
    direct_fixture = fixture_xml("Spot 1", "Acme@Spot.gdtf")
    layers_xml = f'<Layer name="Layer 1"><ChildList>{direct_fixture}</ChildList></Layer>'
    return make_mvr("ld.mvr", layers_xml=layers_xml, gdtf_members={"Acme@Spot.gdtf": ld_bytes})


def test_saved_file_opens_in_a_fresh_window(qtbot, tmp_path, make_mvr, monkeypatch):
    mvr_path = _ld_mvr(make_mvr)

    ld = SubstitutionWindow()
    qtbot.addWidget(ld)
    monkeypatch.setattr(ld, "_ask_open_mvr_path", lambda: str(mvr_path))
    qtbot.mouseClick(ld.import_mvr_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(
        lambda: ld.import_mvr_button.isEnabled() and ld.fixture_list.count() == 1, timeout=10000
    )

    leaf = ld.requirements_editor.leaf_item(WEIGHT_KEY)
    assert leaf is not None
    leaf.setCheckState(0, Qt.CheckState.Checked)

    saved_path = tmp_path / "saved.json"
    recorded = []

    def _record_save(suggested):
        recorded.append(suggested)
        return str(saved_path)

    monkeypatch.setattr(ld, "_ask_save_requirements_path", _record_save)
    qtbot.mouseClick(ld.save_requirements_button, Qt.MouseButton.LeftButton)

    assert recorded == ["Acme Spot requirements.json"]
    assert saved_path.exists()

    fresh = SubstitutionWindow()
    qtbot.addWidget(fresh)
    monkeypatch.setattr(fresh, "_ask_open_requirements_path", lambda: str(saved_path))
    qtbot.mouseClick(fresh.open_requirements_button, Qt.MouseButton.LeftButton)

    assert fresh.requirements_summary_label.text() == describe_requirements(
        load_requirements(str(saved_path))
    )


def test_failed_open_keeps_previous_requirements(
    qtbot, tmp_path, make_gdtf, monkeypatch, capture_dialogs
):
    good_path = tmp_path / "good.json"
    save_requirements(str(good_path), _good_requirement_set())

    window = SubstitutionWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(window, "_ask_open_requirements_path", lambda: str(good_path))
    qtbot.mouseClick(window.open_requirements_button, Qt.MouseButton.LeftButton)

    good_summary = window.requirements_summary_label.text()
    assert good_summary == describe_requirements(load_requirements(str(good_path)))

    damaged_path = tmp_path / "damaged.json"
    damaged_path.write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(window, "_ask_open_requirements_path", lambda: str(damaged_path))
    qtbot.mouseClick(window.open_requirements_button, Qt.MouseButton.LeftButton)

    assert len(capture_dialogs) == 1
    text, text_format = capture_dialogs[0]
    assert text_format == Qt.TextFormat.PlainText
    try:
        load_requirements(str(damaged_path))
        raise AssertionError("expected load_requirements to raise")
    except RequirementsFileError as exc:
        assert text == str(exc)

    assert window.requirements_summary_label.text() == good_summary

    inventory_folder = tmp_path / "inventory"
    inventory_folder.mkdir()
    make_gdtf(
        "inventory/Beta Spot.gdtf", name="Beta Spot", manufacturer="Beta", weight=14.0
    )
    monkeypatch.setattr(window, "_ask_inventory_folder", lambda: str(inventory_folder))
    qtbot.mouseClick(window.choose_folder_button, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(window.check_inventory_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(
        lambda: window.check_inventory_button.isEnabled() and window.results_model.rowCount() == 1,
        timeout=10000,
    )


def test_failed_save_shows_dialog(qtbot, tmp_path, make_mvr, monkeypatch, capture_dialogs):
    mvr_path = _ld_mvr(make_mvr)

    window = SubstitutionWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(window, "_ask_open_mvr_path", lambda: str(mvr_path))
    qtbot.mouseClick(window.import_mvr_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(
        lambda: window.import_mvr_button.isEnabled() and window.fixture_list.count() == 1,
        timeout=10000,
    )

    leaf = window.requirements_editor.leaf_item(WEIGHT_KEY)
    assert leaf is not None
    leaf.setCheckState(0, Qt.CheckState.Checked)

    missing_folder_path = tmp_path / "does-not-exist" / "req.json"
    monkeypatch.setattr(
        window, "_ask_save_requirements_path", lambda suggested: str(missing_folder_path)
    )
    qtbot.mouseClick(window.save_requirements_button, Qt.MouseButton.LeftButton)

    assert len(capture_dialogs) == 1
    text, _ = capture_dialogs[0]
    assert text.startswith("Could not save the requirements to")
    assert not missing_folder_path.exists()
