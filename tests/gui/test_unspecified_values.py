"""App-level proof that undeclared attributes render as N/A, not pygdtf's
spec-default substitute (closes 01-VERIFICATION.md Truth 6 / 01-REVIEW.md CR-01).
"""

from PySide6.QtCore import Qt

from gdtf_comparer.core.models import CATEGORY_BEAM, CATEGORY_PHYSICAL
from gdtf_comparer.gui.main_window import MainWindow


def _run(qtbot, target_path, comparison_path):
    window = MainWindow()
    qtbot.addWidget(window)

    window.set_target_file(str(target_path))
    window.add_compare_files([str(comparison_path)])

    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.run_button.isEnabled(), timeout=10000)

    return window


def test_omitted_weight_cell_reads_na(qtbot, make_gdtf):
    target = make_gdtf("target.gdtf", name="Target Fixture", weight=None)
    comparison = make_gdtf("comparison.gdtf", name="Comparison Fixture", weight=0.0)

    window = _run(qtbot, target, comparison)
    model = window.table_model

    weight_row = model.find_row(CATEGORY_PHYSICAL, "", "Weight")
    assert weight_row >= 0

    target_cell = model.data(model.index(weight_row, model.COL_TARGET))
    comparison_cell = model.data(model.index(weight_row, model.COL_TARGET + 1))
    assert target_cell == "N/A"
    assert comparison_cell == "0"

    row = model.result().rows[weight_row]
    assert row.differs == (True,)


def test_omitted_beam_attribute_cell_reads_na(qtbot, make_gdtf):
    target = make_gdtf(
        "target.gdtf",
        name="Target Fixture",
        geometries_xml='<Geometry Name="Head"><Beam Name="Beam" BeamAngle="10"/></Geometry>',
    )
    comparison = make_gdtf(
        "comparison.gdtf",
        name="Comparison Fixture",
        geometries_xml=(
            '<Geometry Name="Head">'
            '<Beam Name="Beam" BeamAngle="10" FieldAngle="25"/>'
            "</Geometry>"
        ),
    )

    window = _run(qtbot, target, comparison)
    model = window.table_model

    field_angle_row = model.find_row(CATEGORY_BEAM, "Head/Beam", "FieldAngle")
    assert field_angle_row >= 0

    target_cell = model.data(model.index(field_angle_row, model.COL_TARGET))
    comparison_cell = model.data(model.index(field_angle_row, model.COL_TARGET + 1))
    assert target_cell == "N/A"
    assert comparison_cell == "25"
