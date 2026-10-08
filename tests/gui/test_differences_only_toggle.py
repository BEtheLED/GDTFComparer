""""Show differences only" toggle tests: hides rows where every file agrees
with the target, on top of the cell highlighting, never instead of it
(DIFF-01, Phase 2 D-06)."""

from PySide6.QtCore import Qt

from gdtf_comparer.core.models import (
    AttributeKey,
    CATEGORY_BEAM,
    ComparisonResult,
    ComparisonRow,
    FixtureModel,
)
from gdtf_comparer.gui import main_window as main_window_module
from gdtf_comparer.gui.main_window import MainWindow
from gdtf_comparer.gui.table_model import (
    ANY_DIFFERS_ROLE,
    ComparisonTableModel,
    DifferencesOnlyProxyModel,
)

_GEOMETRIES_XML = (
    '<Geometry Name="Head"><Beam Name="Beam" BeamAngle="10" FieldAngle="15"/></Geometry>'
)
_COMPARISON_GEOMETRIES_XML = (
    '<Geometry Name="Head"><Beam Name="Beam" BeamAngle="30" FieldAngle="15"/></Geometry>'
)
_TARGET_ATTRIBUTES_XML = (
    '<Attribute Name="Pan" Pretty="P" Feature="Position.PanTilt" PhysicalUnit="Angle"/>'
    '<Attribute Name="Dimmer" Pretty="Dim" Feature="Dimmer.Dimmer" PhysicalUnit="Percent"/>'
)
_COMPARISON_ATTRIBUTES_XML = (
    '<Attribute Name="Dimmer" Pretty="Dim" Feature="Dimmer.Dimmer" PhysicalUnit="Percent"/>'
)

_EXPECTED_DIFFERING_TRIPLES = (
    (CATEGORY_BEAM, "Beam 1", "BeamAngle"),
    ("DMX: Position", "Pretty", "Pan"),
    ("DMX: Position", "Feature", "Pan"),
    ("DMX: Position", "PhysicalUnit", "Pan"),
)


def _run_comparison(qtbot, make_gdtf) -> MainWindow:
    target = make_gdtf(
        "target.gdtf",
        name="Target Fixture",
        geometries_xml=_GEOMETRIES_XML,
        attributes_xml=_TARGET_ATTRIBUTES_XML,
    )
    comparison = make_gdtf(
        "comparison.gdtf",
        name="Comparison Fixture",
        geometries_xml=_COMPARISON_GEOMETRIES_XML,
        attributes_xml=_COMPARISON_ATTRIBUTES_XML,
    )

    window = MainWindow()
    qtbot.addWidget(window)

    window.set_target_file(str(target))
    window.add_compare_files([str(comparison)])

    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.run_button.isEnabled(), timeout=10000)

    picker = window.attribute_picker
    with qtbot.waitSignal(picker.selection_changed, timeout=1000):
        picker.section_item("DMX: Position").setCheckState(0, Qt.CheckState.Checked)
    with qtbot.waitSignal(picker.selection_changed, timeout=1000):
        picker.section_item("DMX: Dimmer").setCheckState(0, Qt.CheckState.Checked)

    return window


def _row_triples(view_model):
    triples = []
    for row in range(view_model.rowCount()):
        triples.append(
            (
                view_model.data(view_model.index(row, ComparisonTableModel.COL_CATEGORY)),
                view_model.data(view_model.index(row, ComparisonTableModel.COL_ELEMENT)),
                view_model.data(view_model.index(row, ComparisonTableModel.COL_ATTRIBUTE)),
            )
        )
    return triples


def test_toggle_starts_unticked_above_table(qtbot, make_gdtf):
    window = _run_comparison(qtbot, make_gdtf)

    assert window.differences_only_checkbox.text() == main_window_module.DIFFERENCES_ONLY_LABEL
    assert window.differences_only_checkbox.isChecked() is False
    assert window.results_panel.isAncestorOf(window.differences_only_checkbox) is True

    window.show()
    qtbot.waitExposed(window)

    checkbox_top = window.differences_only_checkbox.mapTo(
        window, window.differences_only_checkbox.rect().topLeft()
    ).y()
    table_top = window.table_view.mapTo(window, window.table_view.rect().topLeft()).y()
    assert checkbox_top < table_top


def test_toggle_hides_rows_without_differences(qtbot, make_gdtf):
    window = _run_comparison(qtbot, make_gdtf)

    original_order = _row_triples(window.table_view.model())
    assert len(original_order) == 19

    with qtbot.waitSignal(window.differences_only_checkbox.toggled, timeout=1000):
        window.differences_only_checkbox.setChecked(True)

    view_model = window.table_view.model()
    assert view_model.rowCount() == 4

    for row in range(view_model.rowCount()):
        assert view_model.data(view_model.index(row, 0), ANY_DIFFERS_ROLE) is True

    assert _row_triples(view_model) == list(_EXPECTED_DIFFERING_TRIPLES)

    beam_row = 0
    comparison_col = ComparisonTableModel.COL_TARGET + 1
    assert (
        view_model.data(
            view_model.index(beam_row, comparison_col), Qt.ItemDataRole.BackgroundRole
        )
        is not None
    )

    pretty_row = 1
    assert (
        view_model.data(view_model.index(pretty_row, comparison_col))
        == "N/A"
    )
    assert (
        view_model.data(
            view_model.index(pretty_row, comparison_col), Qt.ItemDataRole.BackgroundRole
        )
        is not None
    )

    with qtbot.waitSignal(window.differences_only_checkbox.toggled, timeout=1000):
        window.differences_only_checkbox.setChecked(False)

    unticked_model = window.table_view.model()
    activation_group_row = None
    for row in range(unticked_model.rowCount()):
        if (
            unticked_model.data(unticked_model.index(row, ComparisonTableModel.COL_CATEGORY))
            == "DMX: Position"
            and unticked_model.data(unticked_model.index(row, ComparisonTableModel.COL_ELEMENT))
            == "ActivationGroup"
        ):
            activation_group_row = row
            break
    assert activation_group_row is not None
    assert (
        unticked_model.data(
            unticked_model.index(activation_group_row, comparison_col),
            Qt.ItemDataRole.BackgroundRole,
        )
        is None
    )

    assert _row_triples(unticked_model) == original_order


def test_toggle_state_survives_rerun(qtbot, make_gdtf):
    window = _run_comparison(qtbot, make_gdtf)

    with qtbot.waitSignal(window.differences_only_checkbox.toggled, timeout=1000):
        window.differences_only_checkbox.setChecked(True)

    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.run_button.isEnabled(), timeout=10000)

    assert window.differences_only_checkbox.isChecked() is True
    assert window.table_view.model().rowCount() == 4


def test_all_equal_shows_no_differences_message(qtbot, make_gdtf):
    target = make_gdtf("target.gdtf", name="Same Fixture", geometries_xml=_GEOMETRIES_XML)
    comparison = make_gdtf(
        "comparison.gdtf", name="Same Fixture", geometries_xml=_GEOMETRIES_XML
    )

    window = MainWindow()
    qtbot.addWidget(window)
    window.set_target_file(str(target))
    window.add_compare_files([str(comparison)])
    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.run_button.isEnabled(), timeout=10000)

    with qtbot.waitSignal(window.differences_only_checkbox.toggled, timeout=1000):
        window.differences_only_checkbox.setChecked(True)

    assert window.table_view.model().rowCount() == 0
    assert window.statusBar().currentMessage() == main_window_module.NO_DIFFERENCES_MESSAGE

    with qtbot.waitSignal(window.differences_only_checkbox.toggled, timeout=1000):
        window.differences_only_checkbox.setChecked(False)

    assert window.statusBar().currentMessage() == "Compared 1 file(s) against target.gdtf"


def test_no_attributes_selected_message_takes_precedence(qtbot, make_gdtf):
    window = _run_comparison(qtbot, make_gdtf)

    with qtbot.waitSignal(window.differences_only_checkbox.toggled, timeout=1000):
        window.differences_only_checkbox.setChecked(True)

    picker = window.attribute_picker
    for index in range(picker.tree.topLevelItemCount()):
        section = picker.tree.topLevelItem(index)
        with qtbot.waitSignal(picker.selection_changed, timeout=1000):
            section.setCheckState(0, Qt.CheckState.Unchecked)

    assert (
        window.statusBar().currentMessage()
        == main_window_module.NO_ATTRIBUTES_SELECTED_MESSAGE
    )


def test_toggle_without_result_is_harmless(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.differences_only_checkbox.setChecked(True)
    window.differences_only_checkbox.setChecked(False)

    assert window.statusBar().currentMessage() == "Ready"
    assert window.table_view.model().rowCount() == 0


def test_toggle_never_mutates_result(qtbot, make_gdtf):
    window = _run_comparison(qtbot, make_gdtf)

    result = window.table_model.result()
    rows = result.rows

    with qtbot.waitSignal(window.differences_only_checkbox.toggled, timeout=1000):
        window.differences_only_checkbox.setChecked(True)
    with qtbot.waitSignal(window.differences_only_checkbox.toggled, timeout=1000):
        window.differences_only_checkbox.setChecked(False)

    assert window.table_model.result() is result
    assert result.rows is rows
    assert window.is_comparison_running() is False


def test_differences_proxy_edge_results():
    target = FixtureModel(source_path="/t.gdtf", name="T", manufacturer="M", attributes={})
    comparison = FixtureModel(source_path="/c.gdtf", name="C", manufacturer="M", attributes={})

    row_a = ComparisonRow(
        key=AttributeKey(CATEGORY_BEAM, "Beam", "BeamAngle"),
        target_value=1.0,
        comparison_values=(),
        differs=(),
    )
    row_b = ComparisonRow(
        key=AttributeKey(CATEGORY_BEAM, "Beam", "FieldAngle"),
        target_value=2.0,
        comparison_values=(),
        differs=(),
    )
    result = ComparisonResult(target=target, comparisons=(), rows=(row_a, row_b))

    model = ComparisonTableModel()
    model.set_result(result)
    proxy = DifferencesOnlyProxyModel()
    proxy.setSourceModel(model)

    assert proxy.rowCount() == 2
    proxy.set_differences_only(True)
    assert proxy.rowCount() == 0

    empty_result = ComparisonResult(target=target, comparisons=(), rows=())
    model.set_result(empty_result)
    proxy.set_differences_only(False)
    assert proxy.rowCount() == 0
    proxy.set_differences_only(True)
    assert proxy.rowCount() == 0

    model.set_result(None)
    assert proxy.rowCount() == 0

    proxy.set_differences_only(True)
    assert proxy.differences_only() is True
