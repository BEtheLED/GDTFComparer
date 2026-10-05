"""Manage menu end-to-end tests: Rename… updates the dropdown, refuses
conflicts, and never touches the current comparison; Delete… asks first and
removes a profile everywhere (Phase 3 D-05, D-07)."""

import os

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox, QToolButton

from gdtf_comparer.core.models import CATEGORY_BEAM, CATEGORY_PHYSICAL
from gdtf_comparer.core.profile_repository import ProfileRepository
from gdtf_comparer.gui import main_window as main_window_module
from gdtf_comparer.gui.main_window import MainWindow

# Shared GUI test data (03-01-PLAN.md context), copied from
# tests/gui/test_profile_portability.py.
_GEOMETRIES_XML = (
    '<Geometry Name="Head"><Beam Name="Beam" BeamAngle="10" FieldAngle="15"/></Geometry>'
)
_PAN_XML = (
    '<Attribute Name="Pan" Pretty="P" ActivationGroup="PanTilt" '
    'Feature="Position.PanTilt" PhysicalUnit="Angle"/>'
)
_TILT_XML = (
    '<Attribute Name="Tilt" Pretty="T" ActivationGroup="PanTilt" '
    'Feature="Position.PanTilt" PhysicalUnit="Angle"/>'
)
_DIMMER_XML = (
    '<Attribute Name="Dimmer" Pretty="Dim" Feature="Dimmer.Dimmer" PhysicalUnit="Percent"/>'
)

CATEGORY_DMX_POSITION = "DMX: Position"
CATEGORY_DMX_DIMMER = "DMX: Dimmer"

# The spec sheet used by most tests: 5 pairs, 2 of which (Pan, Tilt) are
# absent from "lacking" files.
PROFILE_PAIRS = frozenset(
    {
        (CATEGORY_BEAM, "BeamAngle"),
        (CATEGORY_PHYSICAL, "Weight"),
        (CATEGORY_DMX_DIMMER, "Dimmer"),
        (CATEGORY_DMX_POSITION, "Pan"),
        (CATEGORY_DMX_POSITION, "Tilt"),
    }
)
BASIC_PAIRS = frozenset({(CATEGORY_BEAM, "BeamAngle")})


def _lacking_files(make_gdtf, suffix=""):
    """Target and comparison both lack Pan/Tilt entirely (no DMX: Position)."""
    target = make_gdtf(
        f"target_lacking{suffix}.gdtf",
        name="Target Fixture",
        geometries_xml=_GEOMETRIES_XML,
        attributes_xml=_DIMMER_XML,
    )
    comparison = make_gdtf(
        f"comparison_lacking{suffix}.gdtf",
        name="Comparison Fixture",
        geometries_xml=_GEOMETRIES_XML,
        attributes_xml=_DIMMER_XML,
    )
    return target, comparison


def _build_window(qtbot, base_dir, profiles):
    """Save each (name, pairs) in profiles, then build a MainWindow over them."""
    repo = ProfileRepository(base_dir=str(base_dir / "profiles"))
    for name, pairs in profiles:
        repo.save(name, pairs)
    window = MainWindow(profile_repository=repo)
    qtbot.addWidget(window)
    return window


def _index_of(window, name):
    for index in range(window.profile_combo.count()):
        if window.profile_combo.itemText(index) == name:
            return index
    raise AssertionError(f"'{name}' not found in profile_combo")


def _select(window, name):
    window.profile_combo.setCurrentIndex(_index_of(window, name))


def _load_profile_named(qtbot, window, name):
    index = _index_of(window, name)
    window.profile_combo.setCurrentIndex(index)
    with qtbot.waitSignal(window.attribute_picker.selection_changed, timeout=1000):
        window.profile_combo.activated.emit(index)


def _run(qtbot, window, target, comparison):
    """Set target/comparison files on window, click Run, and wait."""
    window.set_target_file(str(target))
    window.add_compare_files([str(comparison)])
    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.run_button.isEnabled(), timeout=10000)


@pytest.fixture
def capture_dialogs(monkeypatch):
    """Monkeypatch QMessageBox.exec to record (text, textFormat) and return 0."""
    dialogs = []

    def _fake_exec(self):
        dialogs.append((self.text(), self.textFormat()))
        return 0

    monkeypatch.setattr(QMessageBox, "exec", _fake_exec)
    return dialogs


# ---------------------------------------------------------------------------
# Task 1: Rename…
# ---------------------------------------------------------------------------


def test_manage_button_sits_in_profile_row(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert (
        window.profile_actions_row.indexOf(window.manage_profile_button)
        > window.profile_actions_row.indexOf(window.save_profile_button)
        >= 0
    )
    assert window.manage_profile_button.text() == main_window_module.MANAGE_PROFILES_LABEL
    assert window.manage_profile_button.menu() is window.manage_profile_menu
    assert (
        window.manage_profile_button.popupMode() == QToolButton.ToolButtonPopupMode.InstantPopup
    )
    assert window.rename_profile_action in window.manage_profile_menu.actions()
    assert window.rename_profile_action.text() == main_window_module.RENAME_PROFILE_LABEL


def test_manage_disabled_until_a_profile_is_shown(qtbot, tmp_path):
    empty_window = _build_window(qtbot, tmp_path / "empty", [])
    assert empty_window.manage_profile_button.isEnabled() is False

    window = _build_window(qtbot, tmp_path / "seeded", [("Basic", BASIC_PAIRS)])
    assert window.profile_combo.currentIndex() == -1
    assert window.manage_profile_button.isEnabled() is False
    before = window.attribute_picker.checked_attributes()

    window.profile_combo.setCurrentIndex(0)
    assert window.manage_profile_button.isEnabled() is True
    assert window.rename_profile_action.isEnabled() is True
    assert window.attribute_picker.checked_attributes() == before

    window.profile_combo.setCurrentIndex(-1)
    assert window.manage_profile_button.isEnabled() is False
    assert window.rename_profile_action.isEnabled() is False


def test_rename_updates_dropdown_and_survives_restart(qtbot, tmp_path, monkeypatch):
    window = _build_window(
        qtbot, tmp_path, [("Moving Head Spec", PROFILE_PAIRS), ("Basic", BASIC_PAIRS)]
    )
    _select(window, "Moving Head Spec")

    recorded = []

    def _recording_ask(title, label, default_text=""):
        recorded.append((title, label, default_text))
        return "Wash Spec"

    monkeypatch.setattr(window, "_ask_profile_name", _recording_ask)
    window.rename_profile_action.trigger()

    assert recorded == [
        (
            main_window_module.RENAME_PROFILE_TITLE,
            main_window_module.RENAME_PROFILE_PROMPT.format(name="Moving Head Spec"),
            "Moving Head Spec",
        )
    ]
    assert [
        window.profile_combo.itemText(i) for i in range(window.profile_combo.count())
    ] == ["Basic", "Wash Spec"]
    assert window.profile_combo.currentText() == "Wash Spec"
    assert (
        window.statusBar().currentMessage()
        == main_window_module.PROFILE_RENAMED_TEMPLATE.format(old="Moving Head Spec", new="Wash Spec")
    )

    base_dir = os.path.dirname(window.profile_repository.path)
    fresh_repo = ProfileRepository(base_dir=base_dir)
    fresh_window = MainWindow(profile_repository=fresh_repo)
    qtbot.addWidget(fresh_window)
    assert [
        fresh_window.profile_combo.itemText(i) for i in range(fresh_window.profile_combo.count())
    ] == ["Basic", "Wash Spec"]
    assert fresh_repo.get("Wash Spec").attributes == PROFILE_PAIRS


def test_rename_cancel_changes_nothing(qtbot, tmp_path, monkeypatch):
    window = _build_window(
        qtbot, tmp_path, [("Moving Head Spec", PROFILE_PAIRS), ("Basic", BASIC_PAIRS)]
    )
    _select(window, "Moving Head Spec")
    original_bytes = open(window.profile_repository.path, "rb").read()
    original_items = [
        window.profile_combo.itemText(i) for i in range(window.profile_combo.count())
    ]

    monkeypatch.setattr(window, "_ask_profile_name", lambda *a, **k: None)
    window.rename_profile_action.trigger()

    assert open(window.profile_repository.path, "rb").read() == original_bytes
    assert [
        window.profile_combo.itemText(i) for i in range(window.profile_combo.count())
    ] == original_items


def test_rename_conflict_shows_error_and_changes_nothing(
    qtbot, tmp_path, monkeypatch, capture_dialogs
):
    window = _build_window(
        qtbot, tmp_path, [("Moving Head Spec", PROFILE_PAIRS), ("Basic", BASIC_PAIRS)]
    )
    _select(window, "Moving Head Spec")
    original_bytes = open(window.profile_repository.path, "rb").read()
    original_items = [
        window.profile_combo.itemText(i) for i in range(window.profile_combo.count())
    ]

    monkeypatch.setattr(window, "_ask_profile_name", lambda *a, **k: " basic ")
    window.rename_profile_action.trigger()

    assert len(capture_dialogs) == 1
    text, text_format = capture_dialogs[0]
    assert "already exists" in text
    assert text_format == Qt.TextFormat.PlainText
    assert open(window.profile_repository.path, "rb").read() == original_bytes
    assert [
        window.profile_combo.itemText(i) for i in range(window.profile_combo.count())
    ] == original_items


def test_rename_never_changes_checked_attributes_or_result(
    qtbot, make_gdtf, tmp_path, monkeypatch
):
    target, comparison = _lacking_files(make_gdtf)
    window = _build_window(qtbot, tmp_path, [("Moving Head Spec", PROFILE_PAIRS)])
    _run(qtbot, window, target, comparison)
    _load_profile_named(qtbot, window, "Moving Head Spec")

    checked_before = window.attribute_picker.checked_attributes()
    result_before = window.table_model.result()

    monkeypatch.setattr(window, "_ask_profile_name", lambda *a, **k: "Wash Spec")
    window.rename_profile_action.trigger()

    assert window.attribute_picker.checked_attributes() == checked_before
    assert window.table_model.result() is result_before
    assert window.is_comparison_running() is False
    assert window.run_button.isEnabled() is True


def test_renaming_loaded_profile_keeps_not_found_report_under_new_name(
    qtbot, make_gdtf, tmp_path, monkeypatch
):
    target, comparison = _lacking_files(make_gdtf)
    window = _build_window(qtbot, tmp_path, [("Moving Head Spec", PROFILE_PAIRS)])
    _run(qtbot, window, target, comparison)
    _load_profile_named(qtbot, window, "Moving Head Spec")

    assert (
        window.statusBar().currentMessage()
        == main_window_module.PROFILE_ITEMS_NOT_FOUND_TEMPLATE.format(
            missing=2, total=5, name="Moving Head Spec", names="Pan, Tilt"
        )
    )

    monkeypatch.setattr(window, "_ask_profile_name", lambda *a, **k: "Wash Spec")
    window.rename_profile_action.trigger()

    assert window._active_profile.name == "Wash Spec"
    window._show_result_status()
    assert (
        window.statusBar().currentMessage()
        == main_window_module.PROFILE_ITEMS_NOT_FOUND_TEMPLATE.format(
            missing=2, total=5, name="Wash Spec", names="Pan, Tilt"
        )
    )


# ---------------------------------------------------------------------------
# Task 2: Delete…
# ---------------------------------------------------------------------------


def test_manage_menu_lists_rename_then_delete(qtbot, tmp_path):
    window = _build_window(qtbot, tmp_path, [("Basic", BASIC_PAIRS)])

    assert [action.text() for action in window.manage_profile_menu.actions()] == [
        main_window_module.RENAME_PROFILE_LABEL,
        main_window_module.DELETE_PROFILE_LABEL,
    ]

    window.profile_combo.setCurrentIndex(0)
    assert window.delete_profile_action.isEnabled() is True
    assert window.rename_profile_action.isEnabled() is True

    window.profile_combo.setCurrentIndex(-1)
    assert window.delete_profile_action.isEnabled() is False
    assert window.rename_profile_action.isEnabled() is False


def test_delete_asks_first_and_no_keeps_profile(qtbot, tmp_path, monkeypatch):
    window = _build_window(qtbot, tmp_path, [("Basic", BASIC_PAIRS)])
    _select(window, "Basic")
    original_bytes = open(window.profile_repository.path, "rb").read()
    original_items = [
        window.profile_combo.itemText(i) for i in range(window.profile_combo.count())
    ]

    confirm_calls = []

    def _confirm_no(message):
        confirm_calls.append(message)
        return False

    monkeypatch.setattr(window, "_confirm", _confirm_no)
    window.delete_profile_action.trigger()

    assert confirm_calls == [main_window_module.DELETE_PROFILE_TEMPLATE.format(name="Basic")]
    assert open(window.profile_repository.path, "rb").read() == original_bytes
    assert [
        window.profile_combo.itemText(i) for i in range(window.profile_combo.count())
    ] == original_items


def test_delete_yes_removes_from_dropdown_and_disk_and_keeps_selection(
    qtbot, make_gdtf, tmp_path, monkeypatch
):
    target, comparison = _lacking_files(make_gdtf)
    window = _build_window(
        qtbot, tmp_path, [("Moving Head Spec", PROFILE_PAIRS), ("Basic", BASIC_PAIRS)]
    )
    _run(qtbot, window, target, comparison)
    _load_profile_named(qtbot, window, "Moving Head Spec")
    checked_before = window.attribute_picker.checked_attributes()

    _select(window, "Basic")
    monkeypatch.setattr(window, "_confirm", lambda message: True)
    window.delete_profile_action.trigger()

    assert [
        window.profile_combo.itemText(i) for i in range(window.profile_combo.count())
    ] == ["Moving Head Spec"]
    assert window.profile_combo.currentIndex() == -1
    assert window.manage_profile_button.isEnabled() is False
    assert (
        window.statusBar().currentMessage()
        == main_window_module.PROFILE_DELETED_TEMPLATE.format(name="Basic")
    )
    assert window.attribute_picker.checked_attributes() == checked_before

    base_dir = os.path.dirname(window.profile_repository.path)
    fresh_repo = ProfileRepository(base_dir=base_dir)
    fresh_window = MainWindow(profile_repository=fresh_repo)
    qtbot.addWidget(fresh_window)
    assert [
        fresh_window.profile_combo.itemText(i) for i in range(fresh_window.profile_combo.count())
    ] == ["Moving Head Spec"]


def test_deleting_loaded_profile_stops_not_found_report(qtbot, make_gdtf, tmp_path, monkeypatch):
    target, comparison = _lacking_files(make_gdtf)
    window = _build_window(qtbot, tmp_path, [("Moving Head Spec", PROFILE_PAIRS)])
    _run(qtbot, window, target, comparison)
    _load_profile_named(qtbot, window, "Moving Head Spec")

    assert (
        window.statusBar().currentMessage()
        == main_window_module.PROFILE_ITEMS_NOT_FOUND_TEMPLATE.format(
            missing=2, total=5, name="Moving Head Spec", names="Pan, Tilt"
        )
    )

    checked_before = window.attribute_picker.checked_attributes()
    monkeypatch.setattr(window, "_confirm", lambda message: True)
    window.delete_profile_action.trigger()

    assert window._active_profile is None
    assert window.attribute_picker.checked_attributes() == checked_before
    window._show_result_status()
    assert (
        window.statusBar().currentMessage()
        == f"Compared 1 file(s) against {os.path.basename(str(target))}"
    )


def test_deleting_last_profile_disables_dropdown(qtbot, tmp_path, monkeypatch):
    window = _build_window(qtbot, tmp_path, [("Basic", BASIC_PAIRS)])
    _select(window, "Basic")
    monkeypatch.setattr(window, "_confirm", lambda message: True)

    window.delete_profile_action.trigger()

    assert window.profile_combo.isEnabled() is False
    assert window.profile_combo.placeholderText() == main_window_module.NO_PROFILES_PLACEHOLDER
    assert window.manage_profile_button.isEnabled() is False


def test_delete_with_damaged_file_shows_error_and_keeps_file(
    qtbot, tmp_path, monkeypatch, capture_dialogs
):
    window = _build_window(qtbot, tmp_path, [("Basic", BASIC_PAIRS)])
    _select(window, "Basic")

    with open(window.profile_repository.path, "w", encoding="utf-8") as fh:
        fh.write("{not json")

    monkeypatch.setattr(window, "_confirm", lambda message: True)
    window.delete_profile_action.trigger()

    assert len(capture_dialogs) == 1
    text, text_format = capture_dialogs[0]
    assert "damaged" in text
    assert text_format == Qt.TextFormat.PlainText
    with open(window.profile_repository.path, "r", encoding="utf-8") as fh:
        assert fh.read() == "{not json"
