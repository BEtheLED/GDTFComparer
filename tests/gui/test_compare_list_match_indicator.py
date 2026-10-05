"""Compare-with match-indicator tests (03-UAT.md G-03-2): a per-file colored
dot showing whether that comparison file matches the target in the currently
checked attributes, reusing ComparisonRow.differs with zero new comparison
logic, neutral until a comparison runs and reset on every file-list, target
or selection change."""

import os

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QMessageBox

from gdtf_comparer.core.models import CATEGORY_PHYSICAL
from gdtf_comparer.gui import main_window as main_window_module
from gdtf_comparer.gui.main_window import MainWindow


def _run(qtbot, window, target, comparisons) -> None:
    """Set target/comparison files on window, click Run, and wait."""
    window.set_target_file(str(target))
    window.add_compare_files([str(p) for p in comparisons])
    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.run_button.isEnabled(), timeout=10000)


@pytest.fixture
def target(make_gdtf):
    return make_gdtf("target.gdtf", name="Target Fixture", weight=10.0)


@pytest.fixture
def match_file(make_gdtf):
    return make_gdtf("match.gdtf", name="Match Fixture", weight=10.0)


@pytest.fixture
def differs_file(make_gdtf):
    return make_gdtf("differs.gdtf", name="Differs Fixture", weight=20.0)


def test_new_items_start_unknown_with_an_icon(qtbot, match_file, differs_file):
    window = MainWindow()
    qtbot.addWidget(window)

    window.add_compare_files([str(match_file), str(differs_file)])

    for row in range(window.compare_list.count()):
        item = window.compare_list.item(row)
        assert item.data(main_window_module.COMPARE_MATCH_STATE_ROLE) == (
            main_window_module.MATCH_STATE_UNKNOWN
        )
        assert item.icon().isNull() is False


def test_match_and_differs_states_after_run(qtbot, target, match_file, differs_file):
    window = MainWindow()
    qtbot.addWidget(window)

    _run(qtbot, window, target, [match_file, differs_file])

    match_item = window.compare_list.item(0)
    differs_item = window.compare_list.item(1)
    assert match_item.data(main_window_module.COMPARE_MATCH_STATE_ROLE) == (
        main_window_module.MATCH_STATE_MATCH
    )
    assert differs_item.data(main_window_module.COMPARE_MATCH_STATE_ROLE) == (
        main_window_module.MATCH_STATE_DIFFERS
    )


def test_unchecking_the_only_relevant_attribute_falls_back_to_unknown(
    qtbot, target, match_file, differs_file
):
    window = MainWindow()
    qtbot.addWidget(window)

    _run(qtbot, window, target, [match_file, differs_file])

    leaf = window.attribute_picker.leaf_item(CATEGORY_PHYSICAL, "Weight")
    with qtbot.waitSignal(window.attribute_picker.selection_changed):
        leaf.setCheckState(0, Qt.CheckState.Unchecked)

    for row in range(window.compare_list.count()):
        item = window.compare_list.item(row)
        assert item.data(main_window_module.COMPARE_MATCH_STATE_ROLE) == (
            main_window_module.MATCH_STATE_UNKNOWN
        )


def test_adding_a_file_resets_every_indicator_to_unknown(
    qtbot, make_gdtf, target, match_file, differs_file
):
    window = MainWindow()
    qtbot.addWidget(window)

    _run(qtbot, window, target, [match_file, differs_file])
    third_file = make_gdtf("third.gdtf", name="Third Fixture", weight=10.0)
    window.add_compare_files([str(third_file)])

    assert window.compare_list.count() == 3
    for row in range(window.compare_list.count()):
        item = window.compare_list.item(row)
        assert item.data(main_window_module.COMPARE_MATCH_STATE_ROLE) == (
            main_window_module.MATCH_STATE_UNKNOWN
        )


def test_removing_a_file_resets_the_remaining_indicator_to_unknown(
    qtbot, target, match_file, differs_file
):
    window = MainWindow()
    qtbot.addWidget(window)

    _run(qtbot, window, target, [match_file, differs_file])

    window.compare_list.item(0).setSelected(True)
    window.remove_selected_files()

    assert window.compare_list.count() == 1
    remaining = window.compare_list.item(0)
    assert remaining.data(main_window_module.COMPARE_MATCH_STATE_ROLE) == (
        main_window_module.MATCH_STATE_UNKNOWN
    )


def test_changing_target_resets_indicators_to_unknown(
    qtbot, make_gdtf, target, match_file, differs_file
):
    window = MainWindow()
    qtbot.addWidget(window)

    _run(qtbot, window, target, [match_file, differs_file])
    other_target = make_gdtf("other_target.gdtf", name="Other Target", weight=99.0)
    window.set_target_file(str(other_target))

    assert window.compare_list.count() == 2
    for row in range(window.compare_list.count()):
        item = window.compare_list.item(row)
        assert item.data(main_window_module.COMPARE_MATCH_STATE_ROLE) == (
            main_window_module.MATCH_STATE_UNKNOWN
        )


def test_icon_colors_and_shape():
    for state in (
        main_window_module.MATCH_STATE_MATCH,
        main_window_module.MATCH_STATE_DIFFERS,
        main_window_module.MATCH_STATE_UNKNOWN,
    ):
        icon = main_window_module._match_indicator_icon(state)
        diameter = main_window_module._MATCH_INDICATOR_DIAMETER_PX
        image = icon.pixmap(diameter, diameter).toImage()

        center = image.pixelColor(diameter // 2, diameter // 2)
        expected = main_window_module._MATCH_INDICATOR_COLORS[state]
        assert center.name() == expected.name()

        corner = image.pixelColor(0, 0)
        assert corner.alpha() == 0


def test_tooltip_names_the_state(qtbot, target, match_file, differs_file):
    window = MainWindow()
    qtbot.addWidget(window)

    _run(qtbot, window, target, [match_file, differs_file])

    match_item = window.compare_list.item(0)
    differs_item = window.compare_list.item(1)
    assert str(match_file) in match_item.toolTip()
    assert (
        main_window_module.MATCH_STATE_TOOLTIPS[main_window_module.MATCH_STATE_MATCH]
        in match_item.toolTip()
    )
    assert str(differs_file) in differs_item.toolTip()
    assert (
        main_window_module.MATCH_STATE_TOOLTIPS[main_window_module.MATCH_STATE_DIFFERS]
        in differs_item.toolTip()
    )


def test_indicator_never_changes_comparison_or_selection(
    qtbot, target, match_file, differs_file
):
    window = MainWindow()
    qtbot.addWidget(window)

    _run(qtbot, window, target, [match_file, differs_file])

    result = window.table_model.result()
    checked = window.attribute_picker.checked_attributes()
    files = list(window.compare_files)

    window._update_match_indicators()
    window._update_match_indicators()

    assert window.table_model.result() is result
    assert window.attribute_picker.checked_attributes() == checked
    assert window.compare_files == files
    assert window.is_comparison_running() is False


def test_running_again_resets_stale_indicators_before_new_result(
    qtbot, target, match_file, differs_file
):
    """A re-run must not leave the previous run's dots on screen (03-REVIEW.md WR-01):
    run_comparison() clears table_model's result synchronously before starting the
    worker thread, and must reset the dots in that same synchronous step."""
    window = MainWindow()
    qtbot.addWidget(window)

    _run(qtbot, window, target, [match_file, differs_file])
    assert window.compare_list.item(0).data(main_window_module.COMPARE_MATCH_STATE_ROLE) == (
        main_window_module.MATCH_STATE_MATCH
    )

    window.run_comparison()
    for row in range(window.compare_list.count()):
        item = window.compare_list.item(row)
        assert item.data(main_window_module.COMPARE_MATCH_STATE_ROLE) == (
            main_window_module.MATCH_STATE_UNKNOWN
        )
    qtbot.waitUntil(lambda: window.run_button.isEnabled(), timeout=10000)


def test_failed_comparison_resets_stale_indicators_to_unknown(
    qtbot, monkeypatch, target, match_file, differs_file
):
    """A failed re-run must not leave a stale, no-longer-trustworthy verdict on
    screen (03-REVIEW.md WR-01): on_comparison_failed already clears the table's
    result and must reset the dots alongside it."""
    monkeypatch.setattr(QMessageBox, "exec", lambda self: 0)

    window = MainWindow()
    qtbot.addWidget(window)

    _run(qtbot, window, target, [match_file, differs_file])
    assert window.compare_list.item(0).data(main_window_module.COMPARE_MATCH_STATE_ROLE) == (
        main_window_module.MATCH_STATE_MATCH
    )

    window.on_comparison_failed("Something went wrong.")

    for row in range(window.compare_list.count()):
        item = window.compare_list.item(row)
        assert item.data(main_window_module.COMPARE_MATCH_STATE_ROLE) == (
            main_window_module.MATCH_STATE_UNKNOWN
        )


def test_defensive_reset_when_compare_list_and_result_disagree(qtbot, target, match_file):
    window = MainWindow()
    qtbot.addWidget(window)

    _run(qtbot, window, target, [match_file])
    item = window.compare_list.item(0)
    assert item.data(main_window_module.COMPARE_MATCH_STATE_ROLE) == (
        main_window_module.MATCH_STATE_MATCH
    )

    item.setData(Qt.ItemDataRole.UserRole, "bogus-path-not-in-result.gdtf")
    window._update_match_indicators()

    assert item.data(main_window_module.COMPARE_MATCH_STATE_ROLE) == (
        main_window_module.MATCH_STATE_UNKNOWN
    )
