"""GUI tests for MVR import in SubstitutionWindow: summary wording, empty
state, friendly dialogs, one-import-at-a-time, and clean shutdown
(PARSE-02, SUB-01).
"""

from typing import List, Tuple

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from gdtf_comparer.core.models import CATEGORY_PHYSICAL, AttributeKey
from gdtf_comparer.core.mvr_repository import NO_FIXTURES_TEMPLATE, import_mvr, import_summary_message
from gdtf_comparer.gui.substitution_window import NO_MVR_PLACEHOLDER, SubstitutionWindow

from tests.conftest import build_gdtf_bytes

XXE_SCENE_XML = b"""<?xml version="1.0"?>
<!DOCTYPE GeneralSceneDescription [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<GeneralSceneDescription verMajor="1" verMinor="6"><Scene>&xxe;</Scene></GeneralSceneDescription>
"""


@pytest.fixture
def capture_dialogs(monkeypatch):
    """Monkeypatch QMessageBox.exec to record (text, textFormat) and return 0."""
    dialogs: List[Tuple[str, "Qt.TextFormat"]] = []

    def _fake_exec(self):
        dialogs.append((self.text(), self.textFormat()))
        return 0

    monkeypatch.setattr(QMessageBox, "exec", _fake_exec)
    return dialogs


def test_skipped_types_named_in_window(qtbot, make_mvr, monkeypatch):
    good_bytes = build_gdtf_bytes(name="Good Fixture")
    path = make_mvr(
        "mixed.mvr",
        fixtures=[("Good", "Good.gdtf"), ("Missing", "Missing.gdtf")],
        gdtf_members={"Good.gdtf": good_bytes},
    )

    window = SubstitutionWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(window, "_ask_open_mvr_path", lambda: str(path))

    qtbot.mouseClick(window.import_mvr_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.import_mvr_button.isEnabled(), timeout=10000)

    assert window.fixture_list.count() == 1
    expected = import_summary_message(import_mvr(str(path)))
    assert window.mvr_summary_label.text() == expected


def test_empty_mvr_shows_message_not_crash(qtbot, make_mvr, monkeypatch):
    path = make_mvr("empty.mvr")

    window = SubstitutionWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(window, "_ask_open_mvr_path", lambda: str(path))

    qtbot.mouseClick(window.import_mvr_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.import_mvr_button.isEnabled(), timeout=10000)

    assert window.fixture_list.count() == 0
    assert window.mvr_summary_label.text() == NO_FIXTURES_TEMPLATE.format(file="empty.mvr")
    assert window.save_requirements_button.isEnabled() is False
    assert window.use_for_inventory_button.isEnabled() is False


def test_single_type_is_a_single_row(qtbot, make_mvr, monkeypatch):
    spot_bytes = build_gdtf_bytes(name="Spot A", weight=10.0)
    path = make_mvr(
        "single.mvr", fixtures=[("F1", "A@Spot.gdtf")], gdtf_members={"A@Spot.gdtf": spot_bytes}
    )

    window = SubstitutionWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(window, "_ask_open_mvr_path", lambda: str(path))

    qtbot.mouseClick(window.import_mvr_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.import_mvr_button.isEnabled(), timeout=10000)

    assert window.fixture_list.count() == 1
    assert window.fixture_list.currentRow() == 0
    leaf = window.requirements_editor.leaf_item(AttributeKey(CATEGORY_PHYSICAL, "", "Weight"))
    assert leaf is not None


def test_summary_label_is_plain_text(qtbot, make_mvr, monkeypatch):
    bogus_spec = "<b>x</b>.gdtf"
    path = make_mvr("markup.mvr", fixtures=[("F1", bogus_spec)])

    window = SubstitutionWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(window, "_ask_open_mvr_path", lambda: str(path))

    qtbot.mouseClick(window.import_mvr_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.import_mvr_button.isEnabled(), timeout=10000)

    assert window.mvr_summary_label.textFormat() == Qt.TextFormat.PlainText
    assert bogus_spec in window.mvr_summary_label.text()


def test_accented_fixture_type_imports_in_window(qtbot, make_mvr, monkeypatch):
    spec = "Lumière@Spot.gdtf"
    spot_bytes = build_gdtf_bytes(name="Lumiere Spot")
    path = make_mvr("accented.mvr", fixtures=[("F1", spec)], gdtf_members={spec: spot_bytes})

    window = SubstitutionWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(window, "_ask_open_mvr_path", lambda: str(path))

    qtbot.mouseClick(window.import_mvr_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(
        lambda: window.import_mvr_button.isEnabled() and window.fixture_list.count() == 1, timeout=10000
    )

    assert window.fixture_list.item(0).toolTip() == spec


def test_hostile_mvr_shows_one_friendly_dialog(qtbot, make_mvr, monkeypatch, capture_dialogs):
    path = make_mvr("xxe.mvr", scene_xml=XXE_SCENE_XML)

    window = SubstitutionWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(window, "_ask_open_mvr_path", lambda: str(path))

    qtbot.mouseClick(window.import_mvr_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.import_mvr_button.isEnabled(), timeout=10000)

    assert len(capture_dialogs) == 1
    text, text_format = capture_dialogs[0]
    assert text.startswith("Could not open 'xxe.mvr':")
    assert text_format == Qt.TextFormat.PlainText
    assert window.fixture_list.count() == 0
    assert window.mvr_summary_label.text() == NO_MVR_PLACEHOLDER
    assert window.import_mvr_button.isEnabled()


def test_failed_import_clears_previous_list(qtbot, make_mvr, tmp_path, monkeypatch, capture_dialogs):
    spot_bytes = build_gdtf_bytes(name="Spot A")
    wash_bytes = build_gdtf_bytes(name="Wash A")
    good_path = make_mvr(
        "good.mvr",
        fixtures=[("F1", "A@Spot.gdtf"), ("F2", "B@Wash.gdtf")],
        gdtf_members={"A@Spot.gdtf": spot_bytes, "B@Wash.gdtf": wash_bytes},
    )

    window = SubstitutionWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(window, "_ask_open_mvr_path", lambda: str(good_path))
    qtbot.mouseClick(window.import_mvr_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(
        lambda: window.import_mvr_button.isEnabled() and window.fixture_list.count() == 2, timeout=10000
    )

    bad_path = tmp_path / "bad.mvr"
    bad_path.write_bytes(b"not a zip")
    monkeypatch.setattr(window, "_ask_open_mvr_path", lambda: str(bad_path))
    qtbot.mouseClick(window.import_mvr_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.import_mvr_button.isEnabled(), timeout=10000)

    assert window.fixture_list.count() == 0
    assert window.requirements_editor.requirement_set() is None
