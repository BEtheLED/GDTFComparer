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
