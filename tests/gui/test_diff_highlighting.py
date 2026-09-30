"""Diff-highlight tests: differing comparison cells are tinted with the live
qt-material theme's accent color, painted on screen through a delegate, and
follow ComparisonRow.differs/any_differs precisely -- never display text
(DIFF-01, Phase 2 D-05).
"""

import qt_material
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from gdtf_comparer.core.models import (
    AttributeKey,
    CATEGORY_BEAM,
    ComparisonResult,
    ComparisonRow,
    FixtureModel,
)
from gdtf_comparer.gui import theme as theme_module
from gdtf_comparer.gui.main_window import MainWindow
from gdtf_comparer.gui.table_model import ComparisonTableModel
from gdtf_comparer.gui.theme import DARK_THEME, LIGHT_THEME, apply_theme

_GEOMETRIES_XML = (
    '<Geometry Name="Head"><Beam Name="Beam" BeamAngle="10" FieldAngle="15"/></Geometry>'
)


def _run_comparison(qtbot, make_gdtf, *, target_geometries_xml=None, comparison_geometries_xml=None) -> MainWindow:
    target = make_gdtf(
        "target.gdtf",
        name="Target Fixture",
        geometries_xml=target_geometries_xml if target_geometries_xml is not None else _GEOMETRIES_XML,
    )
    comparison = make_gdtf(
        "comparison.gdtf",
        name="Comparison Fixture",
        geometries_xml=comparison_geometries_xml
        if comparison_geometries_xml is not None
        else '<Geometry Name="Head"><Beam Name="Beam" BeamAngle="30" FieldAngle="15"/></Geometry>',
    )

    window = MainWindow()
    qtbot.addWidget(window)

    window.set_target_file(str(target))
    window.add_compare_files([str(comparison)])

    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.run_button.isEnabled(), timeout=10000)

    return window


def _find_row(model, category: str, attribute: str) -> int:
    for row in range(model.rowCount()):
        if (
            model.data(model.index(row, ComparisonTableModel.COL_CATEGORY)) == category
            and model.data(model.index(row, ComparisonTableModel.COL_ATTRIBUTE)) == attribute
        ):
            return row
    return -1


def test_differing_comparison_cell_is_highlighted(qtbot, make_gdtf):
    window = _run_comparison(qtbot, make_gdtf)
    model = window.table_model
    highlight = model.highlight_color()
    assert highlight is not None

    beam_row = _find_row(model, CATEGORY_BEAM, "BeamAngle")
    assert beam_row >= 0

    comparison_col = ComparisonTableModel.COL_TARGET + 1
    brush = model.data(model.index(beam_row, comparison_col), Qt.ItemDataRole.BackgroundRole)
    assert brush is not None
    assert brush.color() == highlight

    for column in (
        ComparisonTableModel.COL_TARGET,
        ComparisonTableModel.COL_CATEGORY,
        ComparisonTableModel.COL_ELEMENT,
        ComparisonTableModel.COL_ATTRIBUTE,
    ):
        assert model.data(model.index(beam_row, column), Qt.ItemDataRole.BackgroundRole) is None

    field_row = _find_row(model, CATEGORY_BEAM, "FieldAngle")
    assert field_row >= 0
    assert (
        model.data(model.index(field_row, comparison_col), Qt.ItemDataRole.BackgroundRole) is None
    )

    power_row = _find_row(model, CATEGORY_BEAM, "PowerConsumption")
    assert power_row >= 0
    assert (
        model.data(model.index(power_row, comparison_col), Qt.ItemDataRole.BackgroundRole) is None
    )

    weight_row = _find_row(model, "Physical Properties", "Weight")
    assert weight_row >= 0
    assert (
        model.data(model.index(weight_row, comparison_col), Qt.ItemDataRole.BackgroundRole) is None
    )

    view_model = window.table_view.model()
    for row in range(view_model.rowCount()):
        if view_model.data(view_model.index(row, ComparisonTableModel.COL_ATTRIBUTE)) == "BeamAngle":
            view_brush = view_model.data(
                view_model.index(row, comparison_col), Qt.ItemDataRole.BackgroundRole
            )
            assert view_brush is not None
            break
    else:
        raise AssertionError("BeamAngle row not found in view model")


def test_highlight_color_is_theme_primary_tint(qapp, qtbot):
    apply_theme(qapp, LIGHT_THEME)
    window = MainWindow()
    qtbot.addWidget(window)

    expected_hex = qt_material.get_theme(LIGHT_THEME, invert_secondary=True)["primaryColor"]
    expected = QColor(expected_hex)
    actual = window.table_model.highlight_color()
    assert actual is not None
    assert actual.rgb() == expected.rgb()
    assert abs(actual.alphaF() - theme_module.DIFF_HIGHLIGHT_ALPHA) < 0.01

    dark = theme_module.diff_highlight_color(DARK_THEME)
    light = theme_module.diff_highlight_color(LIGHT_THEME)
    assert dark.rgb() != light.rgb()

    light_a = theme_module.diff_highlight_color(LIGHT_THEME)
    light_b = theme_module.diff_highlight_color(LIGHT_THEME)
    assert light_a.rgb() == light_b.rgb()
    assert light_a is not light_b


def _sample_pixel_at_right_edge(view, view_row: int, column: int):
    """Sample a pixel near the right edge of a visible cell's rect."""
    index = view.model().index(view_row, column)
    rect = view.visualRect(index)
    point = rect.topRight()
    point.setX(point.x() - 3)
    point.setY(rect.center().y())
    image = view.viewport().grab().toImage()
    return image.pixelColor(point)


def test_highlight_is_painted_under_qt_material(qapp, qtbot, make_gdtf):
    apply_theme(qapp, LIGHT_THEME)
    window = _run_comparison(qtbot, make_gdtf)
    window.show()
    qtbot.waitExposed(window)

    view = window.table_view
    view_model = view.model()

    beam_view_row = None
    field_view_row = None
    for row in range(view_model.rowCount()):
        attribute = view_model.data(view_model.index(row, ComparisonTableModel.COL_ATTRIBUTE))
        if attribute == "BeamAngle":
            beam_view_row = row
        elif attribute == "FieldAngle":
            field_view_row = row
    assert beam_view_row is not None
    assert field_view_row is not None

    comparison_col = ComparisonTableModel.COL_TARGET + 1
    target_col = ComparisonTableModel.COL_TARGET

    beam_target_pixel = _sample_pixel_at_right_edge(view, beam_view_row, target_col)
    beam_comparison_pixel = _sample_pixel_at_right_edge(view, beam_view_row, comparison_col)
    assert beam_target_pixel != beam_comparison_pixel

    field_target_pixel = _sample_pixel_at_right_edge(view, field_view_row, target_col)
    field_comparison_pixel = _sample_pixel_at_right_edge(view, field_view_row, comparison_col)
    assert field_target_pixel == field_comparison_pixel


def test_highlight_follows_differs_flags_not_text():
    model = ComparisonTableModel()
    model.set_highlight_color(QColor("#ff0000"))

    target = FixtureModel(source_path="/t.gdtf", name="T", manufacturer="M", attributes={})
    comparison = FixtureModel(source_path="/c.gdtf", name="C", manufacturer="M", attributes={})

    row0 = ComparisonRow(
        key=AttributeKey(CATEGORY_BEAM, "Beam", "BeamAngle"),
        target_value=1.0,
        comparison_values=(1.0,),
        differs=(True,),
    )
    row1 = ComparisonRow(
        key=AttributeKey(CATEGORY_BEAM, "Beam", "Other"),
        target_value="x",
        comparison_values=("y",),
        differs=(False,),
    )
    result = ComparisonResult(target=target, comparisons=(comparison,), rows=(row0, row1))
    model.set_result(result)

    comparison_col = ComparisonTableModel.COL_TARGET + 1
    assert model.data(model.index(0, comparison_col), Qt.ItemDataRole.BackgroundRole) is not None
    assert model.data(model.index(1, comparison_col), Qt.ItemDataRole.BackgroundRole) is None

    fresh_model = ComparisonTableModel()
    fresh_model.set_result(result)
    for row in range(fresh_model.rowCount()):
        for column in range(fresh_model.columnCount()):
            assert (
                fresh_model.data(fresh_model.index(row, column), Qt.ItemDataRole.BackgroundRole)
                is None
            )


# --- Task 3: live theme switch, parse-once cache, multi-comparison edges ---


def test_live_dark_switch_retints_without_rerun(qapp, qtbot, make_gdtf):
    apply_theme(qapp, LIGHT_THEME)
    window = _run_comparison(qtbot, make_gdtf)
    window.show()
    qtbot.waitExposed(window)

    result = window.table_model.result()
    light = window.table_model.highlight_color()

    apply_theme(qapp, DARK_THEME)
    with qtbot.waitSignal(window.table_model.dataChanged, timeout=1000):
        window._on_color_scheme_changed(Qt.ColorScheme.Dark)

    new_highlight = window.table_model.highlight_color()
    assert new_highlight.rgb() == theme_module.diff_highlight_color(DARK_THEME).rgb()
    assert new_highlight.rgb() != light.rgb()

    assert window.table_model.result() is result
    assert window.is_comparison_running() is False
    assert window.run_button.isEnabled() is True

    view = window.table_view
    view_model = view.model()
    beam_view_row = None
    field_view_row = None
    for row in range(view_model.rowCount()):
        attribute = view_model.data(view_model.index(row, ComparisonTableModel.COL_ATTRIBUTE))
        if attribute == "BeamAngle":
            beam_view_row = row
        elif attribute == "FieldAngle":
            field_view_row = row
    assert beam_view_row is not None
    assert field_view_row is not None

    comparison_col = ComparisonTableModel.COL_TARGET + 1
    target_col = ComparisonTableModel.COL_TARGET

    beam_target_pixel = _sample_pixel_at_right_edge(view, beam_view_row, target_col)
    beam_comparison_pixel = _sample_pixel_at_right_edge(view, beam_view_row, comparison_col)
    assert beam_target_pixel != beam_comparison_pixel

    field_target_pixel = _sample_pixel_at_right_edge(view, field_view_row, target_col)
    field_comparison_pixel = _sample_pixel_at_right_edge(view, field_view_row, comparison_col)
    assert field_target_pixel == field_comparison_pixel

    apply_theme(qapp, LIGHT_THEME)


def test_theme_file_parsed_once_per_theme(qtbot, make_gdtf, monkeypatch):
    theme_module._theme_color_hex.cache_clear()
    calls = []
    original_get_theme = theme_module.get_theme

    def _counting_get_theme(*args, **kwargs):
        calls.append((args, kwargs))
        return original_get_theme(*args, **kwargs)

    monkeypatch.setattr(theme_module, "get_theme", _counting_get_theme)

    window = _run_comparison(qtbot, make_gdtf)

    view_model = window.table_view.model()
    for _ in range(3):
        for row in range(view_model.rowCount()):
            for column in range(view_model.columnCount()):
                view_model.data(view_model.index(row, column), Qt.ItemDataRole.BackgroundRole)
        window.table_view.viewport().repaint()

    assert len(calls) == 1

    window._on_color_scheme_changed(Qt.ColorScheme.Dark)
    assert len(calls) == 2

    window._on_color_scheme_changed(Qt.ColorScheme.Dark)
    assert len(calls) == 2
    window._on_color_scheme_changed(Qt.ColorScheme.Light)
    assert len(calls) == 2

    theme_module._theme_color_hex.cache_clear()


def _run_three_comparisons(qtbot, make_gdtf) -> MainWindow:
    target = make_gdtf(
        "target.gdtf",
        name="Target Fixture",
        geometries_xml=(
            '<Geometry Name="Head"><Beam Name="Beam" BeamAngle="10" FieldAngle="15"/></Geometry>'
        ),
    )
    comparison1 = make_gdtf(
        "comparison1.gdtf",
        name="Comparison 1",
        geometries_xml=(
            '<Geometry Name="Head"><Beam Name="Beam" BeamAngle="10" FieldAngle="20"/></Geometry>'
        ),
    )
    comparison2 = make_gdtf(
        "comparison2.gdtf",
        name="Comparison 2",
        geometries_xml=(
            '<Geometry Name="Head"><Beam Name="Beam" BeamAngle="10" FieldAngle="15"/></Geometry>'
        ),
    )
    comparison3 = make_gdtf(
        "comparison3.gdtf",
        name="Comparison 3",
        geometries_xml=(
            '<Geometry Name="Head"><Beam Name="Beam" BeamAngle="30" FieldAngle="15"/></Geometry>'
        ),
    )

    window = MainWindow()
    qtbot.addWidget(window)

    window.set_target_file(str(target))
    window.add_compare_files([str(comparison1), str(comparison2), str(comparison3)])

    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.run_button.isEnabled(), timeout=10000)

    return window


def test_three_comparisons_boundaries(qtbot, make_gdtf):
    window = _run_three_comparisons(qtbot, make_gdtf)
    model = window.table_model

    beam_row = _find_row(model, CATEGORY_BEAM, "BeamAngle")
    field_row = _find_row(model, CATEGORY_BEAM, "FieldAngle")
    assert beam_row >= 0
    assert field_row >= 0

    target_col = ComparisonTableModel.COL_TARGET
    assert model.data(model.index(beam_row, target_col), Qt.ItemDataRole.BackgroundRole) is None
    assert model.data(model.index(field_row, target_col), Qt.ItemDataRole.BackgroundRole) is None

    assert (
        model.data(model.index(beam_row, target_col + 1), Qt.ItemDataRole.BackgroundRole) is None
    )
    assert (
        model.data(model.index(beam_row, target_col + 2), Qt.ItemDataRole.BackgroundRole) is None
    )
    assert (
        model.data(model.index(beam_row, target_col + 3), Qt.ItemDataRole.BackgroundRole)
        is not None
    )

    assert (
        model.data(model.index(field_row, target_col + 1), Qt.ItemDataRole.BackgroundRole)
        is not None
    )
    assert (
        model.data(model.index(field_row, target_col + 2), Qt.ItemDataRole.BackgroundRole) is None
    )
    assert (
        model.data(model.index(field_row, target_col + 3), Qt.ItemDataRole.BackgroundRole) is None
    )

    with qtbot.waitSignal(window.differences_only_checkbox.toggled, timeout=1000):
        window.differences_only_checkbox.setChecked(True)

    view_model = window.table_view.model()
    attributes = [
        view_model.data(view_model.index(row, ComparisonTableModel.COL_ATTRIBUTE))
        for row in range(view_model.rowCount())
    ]
    assert attributes == ["BeamAngle", "FieldAngle"]


def test_short_differs_tuple_never_raises():
    model = ComparisonTableModel()
    model.set_highlight_color(QColor("#ff0000"))

    target = FixtureModel(source_path="/t.gdtf", name="T", manufacturer="M", attributes={})
    comparison1 = FixtureModel(source_path="/c1.gdtf", name="C1", manufacturer="M", attributes={})
    comparison2 = FixtureModel(source_path="/c2.gdtf", name="C2", manufacturer="M", attributes={})

    row = ComparisonRow(
        key=AttributeKey(CATEGORY_BEAM, "Beam", "BeamAngle"),
        target_value=1.0,
        comparison_values=(1.0, 2.0),
        differs=(True,),
    )
    result = ComparisonResult(target=target, comparisons=(comparison1, comparison2), rows=(row,))
    model.set_result(result)

    target_col = ComparisonTableModel.COL_TARGET
    assert (
        model.data(model.index(0, target_col + 1), Qt.ItemDataRole.BackgroundRole) is not None
    )
    assert model.data(model.index(0, target_col + 2), Qt.ItemDataRole.BackgroundRole) is None

    out_of_range = model.index(0, model.columnCount())
    assert out_of_range.isValid() is False
    assert model.data(out_of_range) is None
