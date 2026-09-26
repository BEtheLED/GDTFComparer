"""Comparator-level tests over real namespaced attribute extraction (D-11, D-13)."""

from gdtf_comparer.core.comparator import compare_files
from gdtf_comparer.core.models import (
    CATEGORY_BEAM,
    CATEGORY_PHYSICAL,
    DISPLAY_CATEGORIES,
    format_value,
)


def _two_beam_geometries(angle_1: float, angle_2: float) -> str:
    return (
        '<Geometry Name="Body">'
        f'<Geometry Name="Head1"><Beam Name="Beam" BeamAngle="{angle_1}"/></Geometry>'
        f'<Geometry Name="Head2"><Beam Name="Beam" BeamAngle="{angle_2}"/></Geometry>'
        "</Geometry>"
    )


def test_no_attribute_collision(make_gdtf):
    target = make_gdtf(
        "target.gdtf",
        name="Target",
        geometries_xml=_two_beam_geometries(10, 30),
    )
    comparison = make_gdtf(
        "comparison.gdtf",
        name="Comparison",
        geometries_xml=_two_beam_geometries(15, 35),
    )

    result = compare_files(str(target), [str(comparison)])

    beam_angle_rows = [
        row
        for row in result.rows
        if row.key.category == CATEGORY_BEAM and row.key.attribute == "BeamAngle"
    ]
    assert len(beam_angle_rows) == 2

    by_path = {row.key.element_path: row for row in beam_angle_rows}
    head1_row = by_path["Body/Head1/Beam"]
    head2_row = by_path["Body/Head2/Beam"]

    assert head1_row.target_value == 10.0
    assert head1_row.comparison_values == (15.0,)
    assert head1_row.differs == (True,)

    assert head2_row.target_value == 30.0
    assert head2_row.comparison_values == (35.0,)
    assert head2_row.differs == (True,)


def test_missing_key_is_none_and_differs(make_gdtf):
    target = make_gdtf("target.gdtf", name="Target", geometries_xml="")
    comparison = make_gdtf(
        "comparison.gdtf",
        name="Comparison",
        geometries_xml='<Geometry Name="Head"><Beam Name="Beam" BeamAngle="20"/></Geometry>',
    )

    result = compare_files(str(target), [str(comparison)])

    beam_angle_rows = [
        row
        for row in result.rows
        if row.key.category == CATEGORY_BEAM and row.key.attribute == "BeamAngle"
    ]
    assert len(beam_angle_rows) == 1
    row = beam_angle_rows[0]

    assert row.target_value is None
    assert format_value(row.target_value) == "N/A"
    assert row.differs == (True,)


def test_rows_ordered_beam_then_physical(make_gdtf):
    models_xml = '<Model Name="Base" Width="0.1" Height="0.1" Length="0.1"/>'
    target = make_gdtf(
        "target.gdtf",
        name="Target",
        models_xml=models_xml,
        geometries_xml=_two_beam_geometries(10, 30),
    )
    comparison = make_gdtf(
        "comparison.gdtf",
        name="Comparison",
        models_xml=models_xml,
        geometries_xml=_two_beam_geometries(15, 35),
    )

    result = compare_files(str(target), [str(comparison)])

    categories = [row.key.category for row in result.rows]
    last_beam_index = max(i for i, c in enumerate(categories) if c == CATEGORY_BEAM)
    first_physical_index = min(i for i, c in enumerate(categories) if c == CATEGORY_PHYSICAL)
    assert last_beam_index < first_physical_index


def test_both_files_omitting_attribute_show_na_not_default(make_gdtf):
    geometries_xml = '<Geometry Name="Head"><Beam Name="Beam" BeamAngle="10"/></Geometry>'
    target = make_gdtf("target.gdtf", name="Target", geometries_xml=geometries_xml)
    comparison = make_gdtf(
        "comparison.gdtf", name="Comparison", geometries_xml=geometries_xml
    )

    result = compare_files(str(target), [str(comparison)])

    field_angle_rows = [
        row
        for row in result.rows
        if row.key.category == CATEGORY_BEAM and row.key.attribute == "FieldAngle"
    ]
    assert len(field_angle_rows) == 1
    row = field_angle_rows[0]

    assert row.target_value is None
    assert row.comparison_values == (None,)
    assert row.differs == (False,)
    assert format_value(row.target_value) == "N/A"
    assert format_value(row.comparison_values[0]) == "N/A"


def test_omitted_vs_declared_default_differs(make_gdtf):
    target = make_gdtf(
        "target.gdtf",
        name="Target",
        geometries_xml='<Geometry Name="Head"><Beam Name="Beam" FieldAngle="20"/></Geometry>',
    )
    comparison = make_gdtf(
        "comparison.gdtf",
        name="Comparison",
        geometries_xml=(
            '<Geometry Name="Head">'
            '<Beam Name="Beam" BeamAngle="25" FieldAngle="20"/>'
            "</Geometry>"
        ),
    )

    result = compare_files(str(target), [str(comparison)])

    beam_angle_rows = [
        row
        for row in result.rows
        if row.key.category == CATEGORY_BEAM and row.key.attribute == "BeamAngle"
    ]
    assert len(beam_angle_rows) == 1
    beam_angle_row = beam_angle_rows[0]
    assert beam_angle_row.target_value is None
    assert beam_angle_row.comparison_values == (25.0,)
    assert beam_angle_row.differs == (True,)

    field_angle_rows = [
        row
        for row in result.rows
        if row.key.category == CATEGORY_BEAM and row.key.attribute == "FieldAngle"
    ]
    assert len(field_angle_rows) == 1
    assert field_angle_rows[0].differs == (False,)


def test_only_display_categories(make_gdtf):
    models_xml = '<Model Name="Base" Width="0.1" Height="0.1" Length="0.1"/>'
    target = make_gdtf(
        "target.gdtf",
        name="Target",
        models_xml=models_xml,
        geometries_xml=_two_beam_geometries(10, 30),
    )
    comparison = make_gdtf(
        "comparison.gdtf",
        name="Comparison",
        models_xml=models_xml,
        geometries_xml=_two_beam_geometries(15, 35),
    )

    result = compare_files(str(target), [str(comparison)])

    assert all(row.key.category in DISPLAY_CATEGORIES for row in result.rows)
