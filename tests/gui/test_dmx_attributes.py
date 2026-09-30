"""Real-run tests: the full DMX attribute-definition vocabulary reaches the
Attributes panel end to end, in unchecked/collapsed "DMX: <feature group>"
sections, without disturbing the default Beam/Physical Properties table
(ATTR-01 success criterion 1, D-01, D-04)."""

from PySide6.QtCore import Qt

from gdtf_comparer.core.comparator import attribute_catalog
from gdtf_comparer.core.models import DMX_ATTRIBUTE_CATEGORY_PREFIX
from gdtf_comparer.gui.main_window import MainWindow
from gdtf_comparer.gui.table_model import ComparisonTableModel

_DMX_GROUPS = ("Dimmer", "Position", "Gobo", "Color", "Beam", "Focus", "Control", "Shapers")

# One Beam geometry: 6 Beam rows + 1 fixture-level Weight row = 7 rows, the
# default table before and after this plan (D-04).
_GEOMETRIES_XML = '<Geometry Name="Head"><Beam Name="Beam" BeamAngle="10"/></Geometry>'

_PAN_XML = (
    '<Attribute Name="Pan" Pretty="P" ActivationGroup="PanTilt"'
    ' Feature="Position.PanTilt" PhysicalUnit="Angle"/>'
)
_TILT_XML = (
    '<Attribute Name="Tilt" Pretty="T" ActivationGroup="PanTilt"'
    ' Feature="Position.PanTilt" PhysicalUnit="Angle"/>'
)


def _sixty_four_definitions_xml() -> str:
    """Build 8 groups x 8 attribute definitions, distinct names per group."""
    parts = []
    for group in _DMX_GROUPS:
        for n in range(1, 9):
            parts.append(
                f'<Attribute Name="{group}{n}" Pretty="{group[:3]}{n}"'
                f' Feature="{group}.{group}"/>'
            )
    return "".join(parts)


def _run_comparison(qtbot, make_gdtf) -> MainWindow:
    target = make_gdtf(
        "target.gdtf",
        name="Target Fixture",
        geometries_xml=_GEOMETRIES_XML,
        attributes_xml=_sixty_four_definitions_xml() + _PAN_XML + _TILT_XML,
    )
    comparison = make_gdtf(
        "comparison.gdtf",
        name="Comparison Fixture",
        geometries_xml=_GEOMETRIES_XML,
        attributes_xml=_sixty_four_definitions_xml() + _TILT_XML,
    )

    window = MainWindow()
    qtbot.addWidget(window)

    window.set_target_file(str(target))
    window.add_compare_files([str(comparison)])

    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.run_button.isEnabled(), timeout=10000)

    return window


def test_dmx_sections_listed_unchecked_and_collapsed(qtbot, make_gdtf):
    window = _run_comparison(qtbot, make_gdtf)
    picker = window.attribute_picker

    section = picker.section_item("DMX: Position")
    assert section is not None
    assert section.checkState(0) == Qt.CheckState.Unchecked
    assert section.isExpanded() is False

    checked = picker.checked_attributes()
    assert not any(
        category.startswith(DMX_ATTRIBUTE_CATEGORY_PREFIX) for category, _ in checked
    )


def test_sixty_plus_definitions_are_browsable(qtbot, make_gdtf):
    window = _run_comparison(qtbot, make_gdtf)
    picker = window.attribute_picker

    total = 0
    for index in range(picker.tree.topLevelItemCount()):
        section = picker.tree.topLevelItem(index)
        if section.text(0).startswith(DMX_ATTRIBUTE_CATEGORY_PREFIX):
            total += section.childCount()
    assert total == 66

    catalog = attribute_catalog(window.table_model.result())
    catalog_total = sum(
        len(names)
        for category, names in catalog
        if category.startswith(DMX_ATTRIBUTE_CATEGORY_PREFIX)
    )
    assert catalog_total == 66


def test_default_table_unchanged_by_dmx_definitions(qtbot, make_gdtf):
    window = _run_comparison(qtbot, make_gdtf)
    assert window.table_view.model().rowCount() == 7


def test_checking_pan_shows_its_definition_rows(qtbot, make_gdtf):
    window = _run_comparison(qtbot, make_gdtf)
    picker = window.attribute_picker

    with qtbot.waitSignal(picker.selection_changed, timeout=1000):
        picker.leaf_item("DMX: Position", "Pan").setCheckState(0, Qt.CheckState.Checked)

    view_model = window.table_view.model()
    assert view_model.rowCount() == 13

    rows = {}
    for row in range(view_model.rowCount()):
        category = view_model.data(view_model.index(row, ComparisonTableModel.COL_CATEGORY))
        attribute = view_model.data(view_model.index(row, ComparisonTableModel.COL_ATTRIBUTE))
        if category == "DMX: Position" and attribute == "Pan":
            element = view_model.data(view_model.index(row, ComparisonTableModel.COL_ELEMENT))
            target_text = view_model.data(view_model.index(row, ComparisonTableModel.COL_TARGET))
            comparison_text = view_model.data(
                view_model.index(row, ComparisonTableModel.COL_TARGET + 1)
            )
            rows[element] = (target_text, comparison_text)

    assert len(rows) == 6
    assert rows["Pretty"] == ("P", "N/A")
    assert rows["Feature"] == ("Position.PanTilt", "N/A")
    assert rows["ActivationGroup"] == ("PanTilt", "N/A")
    assert rows["MainAttribute"] == ("N/A", "N/A")
    assert rows["PhysicalUnit"] == ("Angle", "N/A")
    assert rows["Color"] == ("N/A", "N/A")
