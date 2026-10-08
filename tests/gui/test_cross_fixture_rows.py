"""App-level regression tests for 03-UAT.md gap G-03-3: cross-file Beam rows
must show every comparison file's own real values on the target's rows, not
N/A, when the files' manufacturers named their geometry differently. Both
2026-10-07 user decisions are exercised here: (1) beam rows are matched
across files by POSITION (1st beam vs 1st beam, 2nd vs 2nd, ...), never by
each file's own element name; (2) per-model Width/Height/Length rows are
dropped from the cross-file comparison table and picker entirely.
"""

from PySide6.QtCore import Qt

from gdtf_comparer.core.models import CATEGORY_BEAM, CATEGORY_PHYSICAL
from gdtf_comparer.core.profile_repository import ProfileRepository
from gdtf_comparer.gui import main_window as main_window_module
from gdtf_comparer.gui.main_window import MainWindow


def _run(qtbot, window, target, comparisons) -> None:
    """Set target/comparison files on window, click Run, and wait."""
    window.set_target_file(str(target))
    window.add_compare_files([str(p) for p in comparisons])
    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.run_button.isEnabled(), timeout=10000)


def test_differently_named_comparisons_show_real_beam_values(qtbot, make_gdtf):
    target = make_gdtf(
        "target.gdtf",
        name="Target Fixture",
        geometries_xml=(
            '<Geometry Name="Base 1">'
            '<Geometry Name="LED 1">'
            '<Beam Name="Pixel 1" BeamAngle="60" FieldAngle="107" PowerConsumption="250"/>'
            "</Geometry></Geometry>"
        ),
    )
    pendant = make_gdtf(
        "pendant.gdtf",
        name="Pendant Fixture",
        geometries_xml=(
            '<Geometry Name="Body">'
            '<Beam Name="Beam" BeamAngle="58.1" FieldAngle="79.8" PowerConsumption="200"/>'
            "</Geometry>"
        ),
    )
    patt = make_gdtf(
        "patt.gdtf",
        name="Patt Fixture",
        geometries_xml=(
            '<Geometry Name="One PATT">'
            '<Beam Name="Patt beam" BeamAngle="58" FieldAngle="90" PowerConsumption="40"/>'
            "</Geometry>"
        ),
    )

    window = MainWindow()
    qtbot.addWidget(window)
    _run(qtbot, window, target, [pendant, patt])

    model = window.table_model
    expected = {
        "BeamAngle": ("60", "58.1", "58"),
        "FieldAngle": ("107", "79.8", "90"),
        "PowerConsumption": ("250", "200", "40"),
    }
    for attribute, expected_texts in expected.items():
        row = model.find_row(CATEGORY_BEAM, "Beam 1", attribute)
        assert row >= 0
        for offset, expected_text in enumerate(expected_texts):
            cell = model.data(model.index(row, model.COL_TARGET + offset))
            assert cell == expected_text

    beam_angle_row = model.find_row(CATEGORY_BEAM, "Beam 1", "BeamAngle")
    assert model.data(model.index(beam_angle_row, model.COL_ELEMENT)) == "Beam 1"

    assert (
        sum(1 for r in model.result().rows if r.key.category == CATEGORY_BEAM) == 6
    )


def test_missing_beam_position_reads_na_only_for_that_file(qtbot, make_gdtf):
    target = make_gdtf(
        "target.gdtf",
        name="Target Fixture",
        geometries_xml=(
            '<Geometry Name="Bar">'
            '<Beam Name="Cell A" BeamAngle="10"/>'
            '<Beam Name="Cell B" BeamAngle="20"/>'
            "</Geometry>"
        ),
    )
    comparison = make_gdtf(
        "comparison.gdtf",
        name="Comparison Fixture",
        geometries_xml='<Geometry Name="Spot"><Beam Name="Lens" BeamAngle="10"/></Geometry>',
    )

    window = MainWindow()
    qtbot.addWidget(window)
    _run(qtbot, window, target, [comparison])

    model = window.table_model
    beam_1_row = model.find_row(CATEGORY_BEAM, "Beam 1", "BeamAngle")
    assert model.data(model.index(beam_1_row, model.COL_TARGET)) == "10"
    assert model.data(model.index(beam_1_row, model.COL_TARGET + 1)) == "10"

    beam_2_row = model.find_row(CATEGORY_BEAM, "Beam 2", "BeamAngle")
    assert model.data(model.index(beam_2_row, model.COL_TARGET)) == "20"
    assert model.data(model.index(beam_2_row, model.COL_TARGET + 1)) == "N/A"
    assert model.result().rows[beam_2_row].differs == (True,)


def test_match_dot_meaningful_for_differently_named_fixtures(qtbot, make_gdtf):
    target = make_gdtf(
        "target.gdtf",
        name="Target Fixture",
        geometries_xml=(
            '<Geometry Name="Base 1">'
            '<Geometry Name="LED 1">'
            '<Beam Name="Pixel 1" BeamAngle="60" FieldAngle="107"/>'
            "</Geometry></Geometry>"
        ),
        models_xml='<Model Name="Base Leo" Width="0.3" Height="0.3" Length="0.3"/>',
    )
    same_file = make_gdtf(
        "same.gdtf",
        name="Same Fixture",
        geometries_xml=(
            '<Geometry Name="Body"><Beam Name="Beam" BeamAngle="60" FieldAngle="107"/></Geometry>'
        ),
        models_xml='<Model Name="Body" Width="0.1" Height="0.1" Length="0.1"/>',
    )
    diff_file = make_gdtf(
        "diff.gdtf",
        name="Different Fixture",
        geometries_xml=(
            '<Geometry Name="One PATT">'
            '<Beam Name="Patt beam" BeamAngle="58.1" FieldAngle="107"/>'
            "</Geometry>"
        ),
    )

    window = MainWindow()
    qtbot.addWidget(window)
    _run(qtbot, window, target, [same_file, diff_file])

    assert (
        window.compare_list.item(0).data(main_window_module.COMPARE_MATCH_STATE_ROLE)
        == main_window_module.MATCH_STATE_MATCH
    )
    assert (
        window.compare_list.item(1).data(main_window_module.COMPARE_MATCH_STATE_ROLE)
        == main_window_module.MATCH_STATE_DIFFERS
    )


def test_profile_listing_a_dimension_item_reports_it_not_found(qtbot, tmp_path, make_gdtf):
    repo = ProfileRepository(base_dir=str(tmp_path / "profiles"))
    repo.save("Spec", {(CATEGORY_PHYSICAL, "Weight"), (CATEGORY_PHYSICAL, "Width")})

    window = MainWindow(profile_repository=repo)
    qtbot.addWidget(window)

    target = make_gdtf(
        "target.gdtf",
        name="Target Fixture",
        models_xml='<Model Name="Head" Width="0.2" Height="0.25" Length="0.3"/>',
    )
    comparison = make_gdtf(
        "comparison.gdtf",
        name="Comparison Fixture",
        models_xml='<Model Name="Lens" Width="0.2" Height="0.25" Length="0.3"/>',
    )
    _run(qtbot, window, target, [comparison])

    window.profile_combo.setCurrentIndex(0)
    with qtbot.waitSignal(window.attribute_picker.selection_changed, timeout=1000):
        window.profile_combo.activated.emit(0)

    assert window.statusBar().currentMessage() == (
        main_window_module.PROFILE_ITEMS_NOT_FOUND_TEMPLATE.format(
            missing=1, total=2, name="Spec", names="Width"
        )
    )
