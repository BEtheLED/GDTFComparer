"""End-to-end attribute selection tests: checking/unchecking drives the
results table (ATTR-01, ATTR-02, D-01..D-04)."""

from PySide6.QtCore import Qt

from gdtf_comparer.core.models import CATEGORY_BEAM, CATEGORY_PHYSICAL
from gdtf_comparer.gui.main_window import MainWindow
from gdtf_comparer.gui.table_model import ComparisonTableModel

# Two beam geometries (12 rows: 6 BEAM_ATTRIBUTES x 2 beams) + one
# fixture-level Weight row + two models' Width/Height/Length (6 rows) = 19
# source rows once compare() stops filtering by category.
_GEOMETRIES_XML = (
    '<Geometry Name="Body">'
    '<Geometry Name="Head1"><Beam Name="Beam" BeamAngle="10"/></Geometry>'
    '<Geometry Name="Head2"><Beam Name="Beam" BeamAngle="30"/></Geometry>'
    "</Geometry>"
)
_MODELS_XML = (
    '<Model Name="Base" Width="0.4" Height="0.1" Length="0.4"/>'
    '<Model Name="Head" Width="0.2" Height="0.25" Length="0.3"/>'
)


def _run_comparison(qtbot, make_gdtf) -> MainWindow:
    target = make_gdtf(
        "target.gdtf",
        name="Target Fixture",
        geometries_xml=_GEOMETRIES_XML,
        models_xml=_MODELS_XML,
    )
    comparison = make_gdtf(
        "comparison.gdtf",
        name="Comparison Fixture",
        geometries_xml=_GEOMETRIES_XML,
        models_xml=_MODELS_XML,
    )

    window = MainWindow()
    qtbot.addWidget(window)

    window.set_target_file(str(target))
    window.add_compare_files([str(comparison)])

    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.run_button.isEnabled(), timeout=10000)

    return window


def test_picker_lists_default_categories_checked(qtbot, make_gdtf):
    window = _run_comparison(qtbot, make_gdtf)
    picker = window.attribute_picker

    section_texts = [
        picker.tree.topLevelItem(index).text(0)
        for index in range(picker.tree.topLevelItemCount())
    ]
    assert section_texts == [CATEGORY_BEAM, CATEGORY_PHYSICAL]

    for section_index in range(picker.tree.topLevelItemCount()):
        section = picker.tree.topLevelItem(section_index)
        for child_index in range(section.childCount()):
            assert section.child(child_index).checkState(0) == Qt.CheckState.Checked

    checked = picker.checked_attributes()
    assert (CATEGORY_BEAM, "BeamAngle") in checked
    assert (CATEGORY_PHYSICAL, "Weight") in checked

    assert window.table_view.model().rowCount() == 19
    assert window.table_model.rowCount() == 19


def test_unchecking_attribute_hides_its_rows(qtbot, make_gdtf):
    window = _run_comparison(qtbot, make_gdtf)
    picker = window.attribute_picker

    leaf = picker.leaf_item(CATEGORY_BEAM, "BeamAngle")
    with qtbot.waitSignal(picker.selection_changed, timeout=1000):
        leaf.setCheckState(0, Qt.CheckState.Unchecked)

    view_model = window.table_view.model()
    assert view_model.rowCount() == 17
    for row in range(view_model.rowCount()):
        index = view_model.index(row, ComparisonTableModel.COL_ATTRIBUTE)
        assert view_model.data(index) != "BeamAngle"

    assert (
        window.table_model.find_row(CATEGORY_BEAM, "Body/Head1/Beam", "BeamAngle") >= 0
    )

    with qtbot.waitSignal(picker.selection_changed, timeout=1000):
        leaf.setCheckState(0, Qt.CheckState.Checked)
    assert window.table_view.model().rowCount() == 19


def test_side_panel_is_always_visible(qtbot, make_gdtf):
    window = _run_comparison(qtbot, make_gdtf)
    window.show()
    qtbot.waitExposed(window)

    assert window.attributes_group.title() == "Attributes"
    assert window.attribute_picker.isVisible() is True
    assert window.content_splitter.childrenCollapsible() is False


def test_selection_survives_rerun(qtbot, make_gdtf):
    window = _run_comparison(qtbot, make_gdtf)
    picker = window.attribute_picker

    with qtbot.waitSignal(picker.selection_changed, timeout=1000):
        picker.leaf_item(CATEGORY_BEAM, "BeamAngle").setCheckState(0, Qt.CheckState.Unchecked)

    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.run_button.isEnabled(), timeout=10000)

    assert (CATEGORY_BEAM, "BeamAngle") not in picker.checked_attributes()
    assert (CATEGORY_BEAM, "FieldAngle") in picker.checked_attributes()
    assert window.table_view.model().rowCount() == 17
