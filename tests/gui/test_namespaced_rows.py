"""App-level proof that namespaced Beam and Model rows render distinctly (D-11)."""

from PySide6.QtCore import Qt

from gdtf_comparer.core.models import CATEGORY_BEAM, CATEGORY_PHYSICAL
from gdtf_comparer.gui.main_window import MainWindow

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


def test_table_shows_distinct_element_paths(qtbot, make_gdtf):
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

    model = window.table_model

    head1_row = model.find_row(CATEGORY_BEAM, "Body/Head1/Beam", "BeamAngle")
    head2_row = model.find_row(CATEGORY_BEAM, "Body/Head2/Beam", "BeamAngle")
    assert head1_row >= 0
    assert head2_row >= 0
    assert head1_row != head2_row

    assert model.data(model.index(head1_row, model.COL_ELEMENT)) == "Body/Head1/Beam"
    assert model.data(model.index(head2_row, model.COL_ELEMENT)) == "Body/Head2/Beam"

    width_row = model.find_row(CATEGORY_PHYSICAL, "Head", "Width")
    assert width_row >= 0

    weight_row = model.find_row(CATEGORY_PHYSICAL, "", "Weight")
    assert weight_row >= 0
    assert model.data(model.index(weight_row, model.COL_ELEMENT)) == "Fixture"
