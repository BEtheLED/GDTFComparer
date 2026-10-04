"""Profile toolbar end-to-end tests: save, reopen, pick from dropdown, load
replaces the checked set exactly (ATTR-03, D-01..D-04, D-07)."""

import os

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QMessageBox

from gdtf_comparer.core.errors import ProfileNameError
from gdtf_comparer.core.models import CATEGORY_BEAM, CATEGORY_PHYSICAL
from gdtf_comparer.core.profile_repository import ProfileRepository, normalize_profile_name
from gdtf_comparer.gui import main_window as main_window_module
from gdtf_comparer.gui.attribute_picker import AttributePicker
from gdtf_comparer.gui.main_window import MainWindow
from gdtf_comparer.gui.table_model import ComparisonTableModel

# One Beam geometry (6 Beam pairs) plus the fixture-level Weight pair, plus
# two DMX attribute definitions under their own "DMX: " categories (shared
# GUI test data, 03-01-PLAN.md).
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

# The 7 default-checked pairs after a run with _GEOMETRIES_XML (D-04).
_DEFAULT_CHECKED = frozenset(
    {
        (CATEGORY_BEAM, "BeamAngle"),
        (CATEGORY_BEAM, "FieldAngle"),
        (CATEGORY_BEAM, "PowerConsumption"),
        (CATEGORY_BEAM, "LuminousFlux"),
        (CATEGORY_BEAM, "ColorTemperature"),
        (CATEGORY_BEAM, "BeamType"),
        (CATEGORY_PHYSICAL, "Weight"),
    }
)


def _run(qtbot, window, target, comparison) -> None:
    """Set target/comparison files on window, click Run, and wait."""
    window.set_target_file(str(target))
    window.add_compare_files([str(comparison)])
    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.run_button.isEnabled(), timeout=10000)


def _make_target_and_comparison(make_gdtf):
    target = make_gdtf(
        "target.gdtf",
        name="Target Fixture",
        geometries_xml=_GEOMETRIES_XML,
        attributes_xml=_PAN_XML + _DIMMER_XML,
    )
    comparison = make_gdtf(
        "comparison.gdtf",
        name="Comparison Fixture",
        geometries_xml=_GEOMETRIES_XML,
        attributes_xml=_PAN_XML + _DIMMER_XML,
    )
    return target, comparison


def test_profile_toolbar_sits_above_picker_in_attributes_panel(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.attributes_group.isAncestorOf(window.profile_combo) is True
    assert window.attributes_group.isAncestorOf(window.save_profile_button) is True
    assert window.profile_row.indexOf(window.profile_combo) >= 0
    assert window.profile_row.indexOf(window.save_profile_button) >= 0
    assert window.save_profile_button.text() == main_window_module.SAVE_PROFILE_LABEL
    assert window.profile_combo.isEnabled() is False
    assert window.profile_combo.count() == 0
    assert window.profile_combo.placeholderText() == main_window_module.NO_PROFILES_PLACEHOLDER

    window.show()
    qtbot.waitExposed(window)

    combo_top = window.profile_combo.mapTo(window, QPoint(0, 0)).y()
    search_top = window.attribute_picker.search_edit.mapTo(window, QPoint(0, 0)).y()
    assert combo_top < search_top


def test_load_profile_replaces_checked_set(qtbot, make_gdtf, monkeypatch):
    target, comparison = _make_target_and_comparison(make_gdtf)

    window_a = MainWindow()
    qtbot.addWidget(window_a)
    _run(qtbot, window_a, target, comparison)
    picker_a = window_a.attribute_picker

    with qtbot.waitSignal(picker_a.selection_changed, timeout=1000):
        picker_a.leaf_item(CATEGORY_BEAM, "FieldAngle").setCheckState(0, Qt.CheckState.Unchecked)
    with qtbot.waitSignal(picker_a.selection_changed, timeout=1000):
        picker_a.leaf_item(CATEGORY_DMX_POSITION, "Pan").setCheckState(0, Qt.CheckState.Checked)

    expected = picker_a.checked_attributes()
    assert (CATEGORY_BEAM, "FieldAngle") not in expected
    assert (CATEGORY_DMX_POSITION, "Pan") in expected

    monkeypatch.setattr(window_a, "_ask_profile_name", lambda *a, **k: "Moving Head Spec")
    qtbot.mouseClick(window_a.save_profile_button, Qt.MouseButton.LeftButton)
    assert os.path.exists(window_a.profile_repository.path)

    window_b = MainWindow()
    qtbot.addWidget(window_b)
    assert [
        window_b.profile_combo.itemText(i) for i in range(window_b.profile_combo.count())
    ] == ["Moving Head Spec"]
    assert window_b.profile_combo.currentIndex() == -1

    _run(qtbot, window_b, target, comparison)
    picker_b = window_b.attribute_picker
    assert picker_b.checked_attributes() == _DEFAULT_CHECKED

    window_b.profile_combo.setCurrentIndex(0)
    with qtbot.waitSignal(picker_b.selection_changed, timeout=1000):
        window_b.profile_combo.activated.emit(0)

    assert picker_b.checked_attributes() == expected
    assert picker_b.leaf_item(CATEGORY_BEAM, "FieldAngle").checkState(0) == Qt.CheckState.Unchecked
    assert (
        picker_b.leaf_item(CATEGORY_DMX_POSITION, "Pan").checkState(0) == Qt.CheckState.Checked
    )

    attrs_in_expected = {attribute for _, attribute in expected}
    view_model = window_b.table_view.model()
    pan_seen = False
    field_angle_seen = False
    for row in range(view_model.rowCount()):
        attribute_text = view_model.data(view_model.index(row, ComparisonTableModel.COL_ATTRIBUTE))
        assert attribute_text in attrs_in_expected
        if attribute_text == "Pan":
            pan_seen = True
        if attribute_text == "FieldAngle":
            field_angle_seen = True
    assert pan_seen is True
    assert field_angle_seen is False


def test_profile_loaded_before_comparison_is_not_widened_by_defaults(qtbot, make_gdtf, tmp_path):
    target, comparison = _make_target_and_comparison(make_gdtf)

    repo = ProfileRepository(base_dir=str(tmp_path / "profiles"))
    repo.save("Spec", {(CATEGORY_DMX_POSITION, "Pan"), (CATEGORY_PHYSICAL, "Weight")})

    window = MainWindow(profile_repository=repo)
    qtbot.addWidget(window)
    picker = window.attribute_picker

    window.profile_combo.setCurrentIndex(0)
    with qtbot.waitSignal(picker.selection_changed, timeout=1000):
        window.profile_combo.activated.emit(0)

    _run(qtbot, window, target, comparison)

    assert picker.checked_attributes() == frozenset(
        {(CATEGORY_DMX_POSITION, "Pan"), (CATEGORY_PHYSICAL, "Weight")}
    )

    beam_section = picker.section_item(CATEGORY_BEAM)
    for index in range(beam_section.childCount()):
        assert beam_section.child(index).checkState(0) == Qt.CheckState.Unchecked

    view_model = window.table_view.model()
    allowed = {("DMX: Position", "Pan"), (CATEGORY_PHYSICAL, "Weight")}
    for row in range(view_model.rowCount()):
        category_text = view_model.data(view_model.index(row, ComparisonTableModel.COL_CATEGORY))
        attribute_text = view_model.data(
            view_model.index(row, ComparisonTableModel.COL_ATTRIBUTE)
        )
        assert (category_text, attribute_text) in allowed


def test_repopulating_dropdown_never_loads_a_profile(qtbot, make_gdtf, tmp_path, monkeypatch):
    target, comparison = _make_target_and_comparison(make_gdtf)

    repo = ProfileRepository(base_dir=str(tmp_path / "profiles"))
    repo.save("A", {(CATEGORY_PHYSICAL, "Weight")})

    window = MainWindow(profile_repository=repo)
    qtbot.addWidget(window)
    _run(qtbot, window, target, comparison)
    picker = window.attribute_picker
    expected = picker.checked_attributes()
    assert expected == _DEFAULT_CHECKED

    monkeypatch.setattr(window, "_ask_profile_name", lambda *a, **k: "B")
    qtbot.mouseClick(window.save_profile_button, Qt.MouseButton.LeftButton)

    assert [
        window.profile_combo.itemText(i) for i in range(window.profile_combo.count())
    ] == ["A", "B"]
    assert window.profile_combo.currentText() == "B"
    assert picker.checked_attributes() == expected

    window.profile_combo.setCurrentIndex(0)
    qtbot.wait(50)
    assert picker.checked_attributes() == expected


def test_cancelled_save_writes_nothing(qtbot, monkeypatch):
    window = MainWindow()
    qtbot.addWidget(window)

    monkeypatch.setattr(window, "_ask_profile_name", lambda *a, **k: None)
    qtbot.mouseClick(window.save_profile_button, Qt.MouseButton.LeftButton)

    assert os.path.exists(window.profile_repository.path) is False
    assert window.profile_combo.count() == 0


def test_set_checked_replaces_and_emits_once(qtbot):
    picker = AttributePicker()
    qtbot.addWidget(picker)

    catalog = (
        ("Beam", ("BeamAngle", "FieldAngle", "BeamType")),
        ("Physical Properties", ("Weight", "Width")),
        ("Extra Category", ("Zoom", "Focus")),
    )
    picker.set_catalog(catalog)

    emissions = []
    picker.selection_changed.connect(lambda: emissions.append(True))

    with qtbot.waitSignal(picker.selection_changed, timeout=1000):
        picker.set_checked({("Extra Category", "Zoom"), ("Gone", "Missing")})
    qtbot.wait(50)

    assert len(emissions) == 1
    assert picker.checked_attributes() == frozenset(
        {("Extra Category", "Zoom"), ("Gone", "Missing")}
    )

    for category in ("Beam", "Physical Properties"):
        section = picker.section_item(category)
        for index in range(section.childCount()):
            assert section.child(index).checkState(0) == Qt.CheckState.Unchecked

    assert picker.leaf_item("Extra Category", "Zoom").checkState(0) == Qt.CheckState.Checked
    assert picker.section_item("Extra Category").isExpanded() is True
    assert picker.section_item("Beam").isExpanded() is False

    extended_catalog = (
        ("Beam", ("BeamAngle", "FieldAngle", "BeamType", "NewBeamAttr")),
        ("Physical Properties", ("Weight", "Width")),
        ("Extra Category", ("Zoom", "Focus")),
    )
    picker.set_catalog(extended_catalog)

    checked = picker.checked_attributes()
    assert ("Beam", "NewBeamAttr") not in checked
    assert ("Gone", "Missing") in checked


def test_tests_never_touch_real_profile_folder(qtbot, tmp_path):
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.profile_repository.path.startswith(str(tmp_path))


@pytest.fixture
def capture_dialogs(monkeypatch):
    """Monkeypatch QMessageBox.exec to record (text, textFormat) and return 0."""
    dialogs = []

    def _fake_exec(self):
        dialogs.append((self.text(), self.textFormat()))
        return 0

    monkeypatch.setattr(QMessageBox, "exec", _fake_exec)
    return dialogs


def test_save_existing_name_confirms_overwrite(qtbot, make_gdtf, monkeypatch, tmp_path):
    target, comparison = _make_target_and_comparison(make_gdtf)
    repo = ProfileRepository(base_dir=str(tmp_path / "profiles"))
    repo.save("Moving Head Spec", {(CATEGORY_PHYSICAL, "Weight")})
    original_bytes = open(repo.path, "rb").read()

    window = MainWindow(profile_repository=repo)
    qtbot.addWidget(window)
    _run(qtbot, window, target, comparison)

    monkeypatch.setattr(window, "_ask_profile_name", lambda *a, **k: "  moving head spec ")
    confirm_calls = []

    def _confirm_no(message):
        confirm_calls.append(message)
        return False

    monkeypatch.setattr(window, "_confirm", _confirm_no)
    qtbot.mouseClick(window.save_profile_button, Qt.MouseButton.LeftButton)

    assert confirm_calls == [
        main_window_module.OVERWRITE_PROFILE_TEMPLATE.format(name="Moving Head Spec")
    ]
    assert open(repo.path, "rb").read() == original_bytes
    assert [
        window.profile_combo.itemText(i) for i in range(window.profile_combo.count())
    ] == ["Moving Head Spec"]

    window2 = MainWindow(profile_repository=repo)
    qtbot.addWidget(window2)
    _run(qtbot, window2, target, comparison)
    monkeypatch.setattr(window2, "_ask_profile_name", lambda *a, **k: "  moving head spec ")
    monkeypatch.setattr(window2, "_confirm", lambda message: True)

    qtbot.mouseClick(window2.save_profile_button, Qt.MouseButton.LeftButton)

    profiles = repo.load_all()
    assert len(profiles) == 1
    assert profiles[0].name == "moving head spec"
    assert profiles[0].attributes == window2.attribute_picker.checked_attributes()
    assert [
        window2.profile_combo.itemText(i) for i in range(window2.profile_combo.count())
    ] == ["moving head spec"]
    assert window2.profile_combo.currentText() == "moving head spec"
    assert window2.statusBar().currentMessage() == main_window_module.PROFILE_SAVED_TEMPLATE.format(
        name="moving head spec", count=len(profiles[0].attributes)
    )


def test_new_name_saves_without_asking(qtbot, monkeypatch):
    window = MainWindow()
    qtbot.addWidget(window)

    def _confirm_fails(message):
        pytest.fail("confirm should not be called for a new profile name")

    monkeypatch.setattr(window, "_confirm", _confirm_fails)
    monkeypatch.setattr(window, "_ask_profile_name", lambda *a, **k: "Brand New")

    qtbot.mouseClick(window.save_profile_button, Qt.MouseButton.LeftButton)

    assert window.profile_repository.find("Brand New") is not None


def test_invalid_name_shows_friendly_error_and_writes_nothing(qtbot, monkeypatch, capture_dialogs):
    window = MainWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(window, "_ask_profile_name", lambda *a, **k: "   ")

    qtbot.mouseClick(window.save_profile_button, Qt.MouseButton.LeftButton)

    with pytest.raises(ProfileNameError) as exc_info:
        normalize_profile_name("   ")
    expected_message = str(exc_info.value)

    assert len(capture_dialogs) == 1
    text, text_format = capture_dialogs[0]
    assert text == expected_message
    assert text_format == Qt.TextFormat.PlainText
    assert os.path.exists(window.profile_repository.path) is False


def test_confirm_dialog_is_plain_text_and_defaults_to_no(qtbot, monkeypatch):
    window = MainWindow()
    qtbot.addWidget(window)

    recorded = []

    def _fake_exec(self):
        recorded.append(
            (
                self.text(),
                self.textFormat(),
                self.defaultButton() == self.button(QMessageBox.StandardButton.No),
                self.icon(),
            )
        )
        return 0

    monkeypatch.setattr(QMessageBox, "exec", _fake_exec)

    monkeypatch.setattr(
        QMessageBox,
        "clickedButton",
        lambda self: self.button(QMessageBox.StandardButton.Yes),
    )
    assert window._confirm("Replace <b>x</b>?") is True

    monkeypatch.setattr(
        QMessageBox,
        "clickedButton",
        lambda self: self.button(QMessageBox.StandardButton.No),
    )
    assert window._confirm("Replace <b>x</b>?") is False

    assert len(recorded) == 2
    for text, text_format, default_is_no, icon in recorded:
        assert text == "Replace <b>x</b>?"
        assert text_format == Qt.TextFormat.PlainText
        assert default_is_no is True
        assert icon == QMessageBox.Icon.Question

    monkeypatch.setattr(QMessageBox, "clickedButton", lambda self: None)
    assert window._confirm("Replace <b>x</b>?") is False


def test_save_prompt_defaults_to_loaded_profile_name(qtbot, tmp_path):
    repo = ProfileRepository(base_dir=str(tmp_path / "profiles"))
    repo.save("Spec", {(CATEGORY_PHYSICAL, "Weight")})

    window = MainWindow(profile_repository=repo)
    qtbot.addWidget(window)

    window.profile_combo.setCurrentIndex(0)
    with qtbot.waitSignal(window.attribute_picker.selection_changed, timeout=1000):
        window.profile_combo.activated.emit(0)

    recorded_defaults = []

    def _recording_ask(title, label, default_text=""):
        recorded_defaults.append(default_text)
        return None

    window._ask_profile_name = _recording_ask
    window._save_profile()
    assert recorded_defaults == ["Spec"]

    fresh_window = MainWindow()
    qtbot.addWidget(fresh_window)
    fresh_recorded = []

    def _fresh_recording_ask(title, label, default_text=""):
        fresh_recorded.append(default_text)
        return None

    fresh_window._ask_profile_name = _fresh_recording_ask
    fresh_window._save_profile()
    assert fresh_recorded == [""]


def test_empty_profile_round_trips_and_unchecks_everything(qtbot, make_gdtf, tmp_path):
    target, comparison = _make_target_and_comparison(make_gdtf)
    repo = ProfileRepository(base_dir=str(tmp_path / "profiles"))
    repo.save("Empty", [])

    window = MainWindow(profile_repository=repo)
    qtbot.addWidget(window)
    _run(qtbot, window, target, comparison)

    window.profile_combo.setCurrentIndex(0)
    with qtbot.waitSignal(window.attribute_picker.selection_changed, timeout=1000):
        window.profile_combo.activated.emit(0)

    assert window.attribute_picker.checked_attributes() == frozenset()
    assert window.table_view.model().rowCount() == 0
    assert (
        window.statusBar().currentMessage()
        == main_window_module.NO_ATTRIBUTES_SELECTED_MESSAGE
    )


def test_reloading_same_profile_is_idempotent(qtbot, make_gdtf, tmp_path):
    target, comparison = _make_target_and_comparison(make_gdtf)
    repo = ProfileRepository(base_dir=str(tmp_path / "profiles"))
    repo.save("Spec", {(CATEGORY_PHYSICAL, "Weight")})

    window = MainWindow(profile_repository=repo)
    qtbot.addWidget(window)
    _run(qtbot, window, target, comparison)

    picker = window.attribute_picker
    emissions = []
    picker.selection_changed.connect(lambda: emissions.append(True))

    window.profile_combo.setCurrentIndex(0)
    with qtbot.waitSignal(picker.selection_changed, timeout=1000):
        window.profile_combo.activated.emit(0)
    qtbot.wait(50)
    assert len(emissions) == 1
    first_checked = picker.checked_attributes()
    first_count = window.profile_combo.count()

    with qtbot.waitSignal(picker.selection_changed, timeout=1000):
        window.profile_combo.activated.emit(0)
    qtbot.wait(50)
    assert len(emissions) == 2
    assert picker.checked_attributes() == first_checked
    assert window.profile_combo.count() == first_count
