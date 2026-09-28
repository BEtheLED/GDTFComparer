"""Gap-closure tests for 01-UAT.md G-01-1 and G-01-2 (table header readability).

G-01-1: fixed column headers (CATEGORY/ELEMENT/ATTRIBUTE) were clipped in both
qt-material themes because Qt sizes columns from the model's mixed-case labels
while qt-material paints them uppercase.

G-01-2: per-file column headers showed the raw Manufacturer@Model@Revision.gdtf
file name, forcing wide columns and a horizontal scrollbar that pushed the
start of the header off screen.
"""

import pytest
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
from gdtf_comparer.gui.table_model import ComparisonTableModel
from gdtf_comparer.gui.theme import DARK_THEME, LIGHT_THEME, apply_theme

# qt-material 2.17's QHeaderView::section rule at the default density sets
# `padding: 0 24px`. Qt sizes a section from the model's DisplayRole text, so
# a correctly-sized section must be at least the uppercased label's advance
# plus this padding on both sides.
QT_MATERIAL_SECTION_PADDING_PX = 24


def _make_short_result(target_name: str = "T", comparison_name: str = "C") -> ComparisonResult:
    """Build a hand-made ComparisonResult with one short row.

    Short cell text (a single BeamAngle row) means header text -- not cell
    content -- decides column widths, isolating the header-sizing behavior
    under test from the cell-content sizing already covered elsewhere.
    """
    target = FixtureModel(
        source_path="/fixtures/target.gdtf",
        name=target_name,
        manufacturer="M",
        attributes={},
    )
    comparison = FixtureModel(
        source_path="/fixtures/other.gdtf",
        name=comparison_name,
        manufacturer="M",
        attributes={},
    )
    key = AttributeKey(CATEGORY_BEAM, "Beam", "BeamAngle")
    row = ComparisonRow(key=key, target_value=10.0, comparison_values=(12.0,), differs=(True,))
    return ComparisonResult(target=target, comparisons=(comparison,), rows=(row,))


@pytest.mark.parametrize("theme", [LIGHT_THEME, DARK_THEME])
def test_fixed_headers_fit_uppercased_labels(qapp, qtbot, theme):
    """Category/Element/Attribute sections fit their uppercased labels, in both themes."""
    apply_theme(qapp, theme)

    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)

    window.on_comparison_ready(_make_short_result())

    header = window.table_view.horizontalHeader()
    failures = []
    for section in (
        ComparisonTableModel.COL_CATEGORY,
        ComparisonTableModel.COL_ELEMENT,
        ComparisonTableModel.COL_ATTRIBUTE,
    ):
        label = window.table_model.headerData(section, Qt.Orientation.Horizontal)
        needed = header.fontMetrics().horizontalAdvance(label.upper()) + (
            2 * QT_MATERIAL_SECTION_PADDING_PX
        )
        size = header.sectionSize(section)
        if size < needed:
            failures.append((label, size, needed))

    assert not failures, (
        f"theme={theme}: sections too small for their uppercased label "
        f"(label, size, needed)={failures}"
    )


def test_view_uppercases_header_text_only(qapp, qtbot):
    """The view shows uppercase header text; the source model keeps natural case."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.on_comparison_ready(_make_short_result())

    view_model = window.table_view.model()
    assert (
        view_model.headerData(ComparisonTableModel.COL_CATEGORY, Qt.Orientation.Horizontal)
        == "CATEGORY"
    )
    assert (
        window.table_model.headerData(ComparisonTableModel.COL_CATEGORY, Qt.Orientation.Horizontal)
        == "Category"
    )

    target_col = ComparisonTableModel.COL_TARGET
    assert view_model.headerData(
        target_col, Qt.Orientation.Horizontal, Qt.ItemDataRole.ToolTipRole
    ) == window.table_model.headerData(
        target_col, Qt.Orientation.Horizontal, Qt.ItemDataRole.ToolTipRole
    )


def test_value_headers_use_fixture_names(qtbot, make_gdtf):
    """Per-file headers show the fixture name; the target's tooltip shows manufacturer + path."""
    target_path = make_gdtf(
        "Robe_Lighting@MegaPointe@2023.gdtf", name="MegaPointe", manufacturer="Robe Lighting"
    )
    comparison_a = make_gdtf(
        "Martin@MAC_Aura_XB@v2.gdtf", name="MAC Aura XB", manufacturer="Martin"
    )
    comparison_b = make_gdtf("Ayrton@Diablo@v1.gdtf", name="Diablo", manufacturer="Ayrton")

    window = MainWindow()
    qtbot.addWidget(window)

    window.set_target_file(str(target_path))
    window.add_compare_files([str(comparison_a), str(comparison_b)])

    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.run_button.isEnabled(), timeout=10000)

    model = window.table_model
    col_target = ComparisonTableModel.COL_TARGET
    assert model.headerData(col_target, Qt.Orientation.Horizontal) == "Target: MegaPointe"
    assert model.headerData(col_target + 1, Qt.Orientation.Horizontal) == "MAC Aura XB"
    assert model.headerData(col_target + 2, Qt.Orientation.Horizontal) == "Diablo"

    tooltip = model.headerData(
        col_target, Qt.Orientation.Horizontal, Qt.ItemDataRole.ToolTipRole
    )
    assert str(target_path) in tooltip
    assert "Robe Lighting" in tooltip


def test_colliding_or_blank_names_fall_back_to_file_names(qapp):
    """Same-named (case/whitespace-insensitive) or blank fixture names fall back to file names."""
    target = FixtureModel(
        source_path="/fixtures/ASTERA@AF250@V3.gdtf",
        name="AF250 LeoFresnel",
        manufacturer="Astera",
        attributes={},
    )
    same_name_other_case = FixtureModel(
        source_path="/fixtures/ASTERA@AF250@V2.gdtf",
        name="  af250 leofresnel ",
        manufacturer="Astera",
        attributes={},
    )
    distinct = FixtureModel(
        source_path="/fixtures/ASTERA@Titan@V1.gdtf",
        name="Titan Tube",
        manufacturer="Astera",
        attributes={},
    )
    blank = FixtureModel(
        source_path="/fixtures/blank.gdtf",
        name="   ",
        manufacturer="",
        attributes={},
    )
    result = ComparisonResult(
        target=target,
        comparisons=(same_name_other_case, distinct, blank),
        rows=(),
    )

    model = ComparisonTableModel()
    model.set_result(result)

    col_target = ComparisonTableModel.COL_TARGET
    assert model.headerData(col_target, Qt.Orientation.Horizontal) == (
        "Target: ASTERA@AF250@V3.gdtf"
    )
    assert model.headerData(col_target + 1, Qt.Orientation.Horizontal) == (
        "ASTERA@AF250@V2.gdtf"
    )
    assert model.headerData(col_target + 2, Qt.Orientation.Horizontal) == "Titan Tube"
    assert model.headerData(col_target + 3, Qt.Orientation.Horizontal) == "blank.gdtf"

    model.set_result(None)
    assert model.headerData(col_target, Qt.Orientation.Horizontal) == "Target"


def test_long_headers_are_capped_and_elided(qapp, qtbot):
    """Long header labels are capped to MAX_COLUMN_WIDTH_PX, elide in the middle, and the
    table never needs a horizontal scrollbar at the default window size -- while the user
    can still manually widen a column past the cap."""
    apply_theme(qapp, LIGHT_THEME)

    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)

    long_target_name = "Target Fixture With A Very Long Name Indeed " + "X" * 25
    long_comparison_name = "Comparison Fixture With A Very Long Name Too " + "Y" * 25
    result = _make_short_result(
        target_name=long_target_name, comparison_name=long_comparison_name
    )

    window.on_comparison_ready(result)

    header = window.table_view.horizontalHeader()
    col_count = window.table_model.columnCount()
    for section in range(col_count - 1):
        assert header.sectionSize(section) <= main_window_module.MAX_COLUMN_WIDTH_PX

    assert window.table_view.horizontalScrollBar().maximum() == 0
    assert header.textElideMode() == Qt.TextElideMode.ElideMiddle

    col_target = ComparisonTableModel.COL_TARGET
    widened = main_window_module.MAX_COLUMN_WIDTH_PX + 200
    header.resizeSection(col_target, widened)
    assert header.sectionSize(col_target) == widened
