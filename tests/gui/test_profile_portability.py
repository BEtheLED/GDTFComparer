"""Real-run D-06 tests: a loaded compare profile reports which of its spec
items weren't found in the current comparison's files, recomputed on every
selection change and every re-run (Phase 3 D-06, ATTR-03)."""

import os

from PySide6.QtCore import Qt

from gdtf_comparer.core.models import CATEGORY_BEAM, CATEGORY_PHYSICAL
from gdtf_comparer.core.profile_repository import ProfileRepository
from gdtf_comparer.gui import main_window as main_window_module
from gdtf_comparer.gui.main_window import MainWindow
from gdtf_comparer.gui.table_model import ComparisonTableModel

# One Beam geometry (6 Beam pairs) plus the fixture-level Weight pair
# (shared GUI test data, 03-01-PLAN.md).
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


def _full_files(make_gdtf, suffix=""):
    """Target and comparison both have every PROFILE_PAIRS item."""
    target = make_gdtf(
        f"target_full{suffix}.gdtf",
        name="Target Fixture",
        geometries_xml=_GEOMETRIES_XML,
        attributes_xml=_PAN_XML + _TILT_XML + _DIMMER_XML,
    )
    comparison = make_gdtf(
        f"comparison_full{suffix}.gdtf",
        name="Comparison Fixture",
        geometries_xml=_GEOMETRIES_XML,
        attributes_xml=_PAN_XML + _TILT_XML + _DIMMER_XML,
    )
    return target, comparison


def _build_window(qtbot, tmp_path, profiles):
    """Save each (name, pairs) in profiles, then build a MainWindow over them."""
    repo = ProfileRepository(base_dir=str(tmp_path / "profiles"))
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


def _load_profile(qtbot, window, index):
    """Select index and activate it, waiting for the coalesced selection_changed."""
    window.profile_combo.setCurrentIndex(index)
    with qtbot.waitSignal(window.attribute_picker.selection_changed, timeout=1000):
        window.profile_combo.activated.emit(index)


def _load_profile_named(qtbot, window, name):
    _load_profile(qtbot, window, _index_of(window, name))


def _run(qtbot, window, target, comparison):
    """Set target/comparison files on window, click Run, and wait."""
    window.set_target_file(str(target))
    window.add_compare_files([str(comparison)])
    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.run_button.isEnabled(), timeout=10000)


def _swap_files(qtbot, window, target, comparison):
    """Replace window's target/comparison with new files and re-run."""
    window.compare_list.selectAll()
    window.remove_selected_files()
    window.set_target_file(str(target))
    window.add_compare_files([str(comparison)])
    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.run_button.isEnabled(), timeout=10000)


def _attribute_texts(window):
    view_model = window.table_view.model()
    return {
        view_model.data(view_model.index(row, ComparisonTableModel.COL_ATTRIBUTE))
        for row in range(view_model.rowCount())
    }


def test_loaded_profile_reports_items_missing_from_both_files(qtbot, make_gdtf, tmp_path):
    target, comparison = _lacking_files(make_gdtf)
    window = _build_window(qtbot, tmp_path, [("Moving Head Spec", PROFILE_PAIRS)])
    _run(qtbot, window, target, comparison)
    _load_profile(qtbot, window, 0)

    assert (
        window.statusBar().currentMessage()
        == main_window_module.PROFILE_ITEMS_NOT_FOUND_TEMPLATE.format(
            missing=2, total=5, name="Moving Head Spec", names="Pan, Tilt"
        )
    )
    assert _attribute_texts(window) == {"BeamAngle", "Weight", "Dimmer"}


def test_item_on_only_one_file_counts_as_found(qtbot, make_gdtf, tmp_path):
    target = make_gdtf(
        "target_one.gdtf",
        name="Target Fixture",
        geometries_xml=_GEOMETRIES_XML,
        attributes_xml=_PAN_XML + _DIMMER_XML,
    )
    comparison = make_gdtf(
        "comparison_one.gdtf",
        name="Comparison Fixture",
        geometries_xml=_GEOMETRIES_XML,
        attributes_xml=_DIMMER_XML,
    )
    window = _build_window(qtbot, tmp_path, [("Moving Head Spec", PROFILE_PAIRS)])
    _run(qtbot, window, target, comparison)
    _load_profile(qtbot, window, 0)

    assert (
        window.statusBar().currentMessage()
        == main_window_module.PROFILE_ITEMS_NOT_FOUND_TEMPLATE.format(
            missing=1, total=5, name="Moving Head Spec", names="Tilt"
        )
    )
    assert "Pan" in _attribute_texts(window)


def test_rerun_against_other_files_rechecks_profile(qtbot, make_gdtf, tmp_path):
    lacking_target, lacking_comparison = _lacking_files(make_gdtf, suffix="_1")
    full_target, full_comparison = _full_files(make_gdtf, suffix="_1")
    lacking_target_2, lacking_comparison_2 = _lacking_files(make_gdtf, suffix="_2")

    window = _build_window(qtbot, tmp_path, [("Moving Head Spec", PROFILE_PAIRS)])
    _load_profile(qtbot, window, 0)

    _run(qtbot, window, lacking_target, lacking_comparison)
    assert (
        window.statusBar().currentMessage()
        == main_window_module.PROFILE_ITEMS_NOT_FOUND_TEMPLATE.format(
            missing=2, total=5, name="Moving Head Spec", names="Pan, Tilt"
        )
    )

    _swap_files(qtbot, window, full_target, full_comparison)
    assert (
        window.statusBar().currentMessage()
        == f"Compared 1 file(s) against {os.path.basename(str(full_target))}"
    )

    _swap_files(qtbot, window, lacking_target_2, lacking_comparison_2)
    assert (
        window.statusBar().currentMessage()
        == main_window_module.PROFILE_ITEMS_NOT_FOUND_TEMPLATE.format(
            missing=2, total=5, name="Moving Head Spec", names="Pan, Tilt"
        )
    )


def test_check_uses_current_catalog_not_remembered_attributes(qtbot, make_gdtf, tmp_path):
    full_target, full_comparison = _full_files(make_gdtf, suffix="_a")
    lacking_target, lacking_comparison = _lacking_files(make_gdtf, suffix="_a")

    window = _build_window(qtbot, tmp_path, [("Moving Head Spec", PROFILE_PAIRS)])
    _run(qtbot, window, full_target, full_comparison)
    _load_profile(qtbot, window, 0)

    assert (
        window.statusBar().currentMessage()
        == f"Compared 1 file(s) against {os.path.basename(str(full_target))}"
    )

    _swap_files(qtbot, window, lacking_target, lacking_comparison)

    assert (CATEGORY_DMX_POSITION, "Pan") in window.attribute_picker._known
    assert (
        window.statusBar().currentMessage()
        == main_window_module.PROFILE_ITEMS_NOT_FOUND_TEMPLATE.format(
            missing=2, total=5, name="Moving Head Spec", names="Pan, Tilt"
        )
    )


def test_no_message_without_loaded_profile(qtbot, make_gdtf, tmp_path):
    full_target, full_comparison = _full_files(make_gdtf, suffix="_b")
    lacking_target, lacking_comparison = _lacking_files(make_gdtf, suffix="_b")

    window = _build_window(qtbot, tmp_path, [])
    _run(qtbot, window, full_target, full_comparison)

    picker = window.attribute_picker
    with qtbot.waitSignal(picker.selection_changed, timeout=1000):
        picker.section_item(CATEGORY_DMX_POSITION).setCheckState(0, Qt.CheckState.Checked)

    _swap_files(qtbot, window, lacking_target, lacking_comparison)

    assert (
        window.statusBar().currentMessage()
        == f"Compared 1 file(s) against {os.path.basename(str(lacking_target))}"
    )


def test_not_found_check_never_changes_selection_or_result(qtbot, make_gdtf, tmp_path):
    target, comparison = _lacking_files(make_gdtf, suffix="_c")
    window = _build_window(qtbot, tmp_path, [("Moving Head Spec", PROFILE_PAIRS)])
    _run(qtbot, window, target, comparison)
    _load_profile(qtbot, window, 0)

    result = window.table_model.result()
    row_count_before = window.table_view.model().rowCount()

    window._show_result_status()
    window._show_result_status()

    assert window.table_model.result() is result
    assert window.attribute_picker.checked_attributes() == PROFILE_PAIRS
    assert window.table_view.model().rowCount() == row_count_before
    assert window.is_comparison_running() is False


# ---------------------------------------------------------------------------
# Task 2: edges -- before any comparison, all items missing, differences
# only, empty/reloaded/switched profiles.
# ---------------------------------------------------------------------------


def test_load_before_comparison_says_run_a_comparison(qtbot, make_gdtf, tmp_path):
    target, comparison = _lacking_files(make_gdtf, suffix="_d")
    window = _build_window(qtbot, tmp_path, [("Moving Head Spec", PROFILE_PAIRS)])
    _load_profile(qtbot, window, 0)

    expected_pre_result = main_window_module.PROFILE_LOADED_NO_RESULT_TEMPLATE.format(
        name="Moving Head Spec", count=5
    )
    assert window.statusBar().currentMessage() == expected_pre_result
    qtbot.wait(50)
    assert window.statusBar().currentMessage() == expected_pre_result

    _run(qtbot, window, target, comparison)
    assert (
        window.statusBar().currentMessage()
        == main_window_module.PROFILE_ITEMS_NOT_FOUND_TEMPLATE.format(
            missing=2, total=5, name="Moving Head Spec", names="Pan, Tilt"
        )
    )


def test_all_items_missing_never_says_no_attributes_selected(qtbot, make_gdtf, tmp_path):
    target, comparison = _lacking_files(make_gdtf, suffix="_e")
    pairs = frozenset({(CATEGORY_DMX_POSITION, "Pan"), (CATEGORY_DMX_POSITION, "Tilt")})
    window = _build_window(qtbot, tmp_path, [("Moving Head Spec", pairs)])
    _run(qtbot, window, target, comparison)
    _load_profile(qtbot, window, 0)

    assert window.table_view.model().rowCount() == 0
    expected = main_window_module.PROFILE_ITEMS_NOT_FOUND_TEMPLATE.format(
        missing=2, total=2, name="Moving Head Spec", names="Pan, Tilt"
    )
    assert window.statusBar().currentMessage() == expected
    assert expected != main_window_module.NO_ATTRIBUTES_SELECTED_MESSAGE


def test_missing_items_and_no_differences_are_both_reported(qtbot, make_gdtf, tmp_path):
    target, comparison = _lacking_files(make_gdtf, suffix="_f")
    window = _build_window(qtbot, tmp_path, [("Moving Head Spec", PROFILE_PAIRS)])
    _run(qtbot, window, target, comparison)
    _load_profile(qtbot, window, 0)

    expected_not_found = main_window_module.PROFILE_ITEMS_NOT_FOUND_TEMPLATE.format(
        missing=2, total=5, name="Moving Head Spec", names="Pan, Tilt"
    )
    assert window.statusBar().currentMessage() == expected_not_found

    with qtbot.waitSignal(window.differences_only_checkbox.toggled, timeout=1000):
        window.differences_only_checkbox.setChecked(True)

    assert window.table_view.model().rowCount() == 0
    assert (
        window.statusBar().currentMessage()
        == f"{expected_not_found} {main_window_module.NO_DIFFERENCES_MESSAGE}"
    )

    with qtbot.waitSignal(window.differences_only_checkbox.toggled, timeout=1000):
        window.differences_only_checkbox.setChecked(False)

    assert window.statusBar().currentMessage() == expected_not_found


def test_empty_profile_never_reports_zero_of_zero(qtbot, make_gdtf, tmp_path):
    target, comparison = _full_files(make_gdtf, suffix="_g")
    window = _build_window(qtbot, tmp_path, [("Empty", [])])
    _run(qtbot, window, target, comparison)
    _load_profile(qtbot, window, 0)

    message = window.statusBar().currentMessage()
    assert message == main_window_module.NO_ATTRIBUTES_SELECTED_MESSAGE
    assert "0 of 0" not in message


def test_unticking_found_spec_item_lowers_total(qtbot, make_gdtf, tmp_path):
    target, comparison = _lacking_files(make_gdtf, suffix="_h")
    window = _build_window(qtbot, tmp_path, [("Moving Head Spec", PROFILE_PAIRS)])
    _run(qtbot, window, target, comparison)
    _load_profile(qtbot, window, 0)

    picker = window.attribute_picker
    with qtbot.waitSignal(picker.selection_changed, timeout=1000):
        picker.leaf_item(CATEGORY_BEAM, "BeamAngle").setCheckState(0, Qt.CheckState.Unchecked)

    assert (
        window.statusBar().currentMessage()
        == main_window_module.PROFILE_ITEMS_NOT_FOUND_TEMPLATE.format(
            missing=2, total=4, name="Moving Head Spec", names="Pan, Tilt"
        )
    )


def test_reloading_profile_keeps_same_message(qtbot, make_gdtf, tmp_path):
    target, comparison = _lacking_files(make_gdtf, suffix="_i")
    window = _build_window(qtbot, tmp_path, [("Moving Head Spec", PROFILE_PAIRS)])
    _run(qtbot, window, target, comparison)

    _load_profile(qtbot, window, 0)
    first_message = window.statusBar().currentMessage()

    _load_profile(qtbot, window, 0)
    second_message = window.statusBar().currentMessage()

    assert first_message == second_message
    assert window.attribute_picker.checked_attributes() == PROFILE_PAIRS


def test_loading_another_profile_replaces_tracking(qtbot, make_gdtf, tmp_path):
    target, comparison = _lacking_files(make_gdtf, suffix="_j")
    basic_pairs = frozenset({(CATEGORY_BEAM, "BeamAngle")})
    window = _build_window(
        qtbot, tmp_path, [("Moving Head Spec", PROFILE_PAIRS), ("Basic", basic_pairs)]
    )
    _run(qtbot, window, target, comparison)

    _load_profile_named(qtbot, window, "Moving Head Spec")
    assert (
        window.statusBar().currentMessage()
        == main_window_module.PROFILE_ITEMS_NOT_FOUND_TEMPLATE.format(
            missing=2, total=5, name="Moving Head Spec", names="Pan, Tilt"
        )
    )

    _load_profile_named(qtbot, window, "Basic")
    assert window.attribute_picker.checked_attributes() == basic_pairs
    assert (
        window.statusBar().currentMessage()
        == f"Compared 1 file(s) against {os.path.basename(str(target))}"
    )
