"""GUI tests for MVR import in SubstitutionWindow: summary wording, empty
state, friendly dialogs, one-import-at-a-time, and clean shutdown
(PARSE-02, SUB-01).
"""

from PySide6.QtCore import Qt

from gdtf_comparer.core.models import CATEGORY_PHYSICAL, AttributeKey
from gdtf_comparer.core.mvr_repository import NO_FIXTURES_TEMPLATE, import_mvr, import_summary_message
from gdtf_comparer.gui.substitution_window import SubstitutionWindow

from tests.conftest import build_gdtf_bytes


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
