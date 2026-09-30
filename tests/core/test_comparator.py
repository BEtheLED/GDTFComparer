"""Comparator-level tests over real namespaced attribute extraction (D-11, D-13)."""

from gdtf_comparer.core.comparator import attribute_catalog, compare, compare_files
from gdtf_comparer.core.models import (
    AttributeKey,
    CATEGORY_BEAM,
    CATEGORY_PHYSICAL,
    FixtureModel,
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


_TWO_BEAM_GEOMETRIES_XML = (
    '<Geometry Name="Body">'
    '<Geometry Name="Head1"><Beam Name="Beam" BeamAngle="10" FieldAngle="12"/></Geometry>'
    '<Geometry Name="Head2"><Beam Name="Beam" BeamAngle="15" FieldAngle="17"/></Geometry>'
    "</Geometry>"
)
_TWO_MODEL_XML = (
    '<Model Name="Base" Width="0.4" Height="0.1" Length="0.4"/>'
    '<Model Name="Head" Width="0.2" Height="0.25" Length="0.3"/>'
)


def _fixture_model(source_path: str, name: str, attributes: dict) -> FixtureModel:
    return FixtureModel(
        source_path=source_path,
        name=name,
        manufacturer="M",
        attributes=attributes,
    )


def test_all_categories_are_compared():
    target = _fixture_model(
        "/fixtures/target.gdtf",
        "Target",
        {
            AttributeKey(CATEGORY_BEAM, "Head/Beam", "BeamAngle"): 10.0,
            AttributeKey(CATEGORY_PHYSICAL, "", "Weight"): 5.0,
            AttributeKey("Synthetic Category", "", "X"): 1.0,
        },
    )
    comparison = _fixture_model(
        "/fixtures/comparison.gdtf",
        "Comparison",
        {
            AttributeKey(CATEGORY_BEAM, "Head/Beam", "BeamAngle"): 12.0,
            AttributeKey(CATEGORY_PHYSICAL, "", "Weight"): 6.0,
            AttributeKey("Synthetic Category", "", "X"): 2.0,
        },
    )

    result = compare(target, [comparison])

    assert any(row.key.category == "Synthetic Category" for row in result.rows)


def test_leading_categories_first_then_first_seen():
    target = _fixture_model(
        "/fixtures/target.gdtf",
        "Target",
        {
            AttributeKey("Zeta", "", "A"): 1.0,
            AttributeKey(CATEGORY_PHYSICAL, "", "Weight"): 2.0,
            AttributeKey("Alpha", "", "B"): 3.0,
            AttributeKey(CATEGORY_BEAM, "Head/Beam", "BeamAngle"): 4.0,
        },
    )
    comparison = _fixture_model(
        "/fixtures/comparison.gdtf",
        "Comparison",
        {AttributeKey("Mid", "", "C"): 5.0},
    )

    result = compare(target, [comparison])

    categories = [row.key.category for row in result.rows]
    assert categories == [CATEGORY_BEAM, CATEGORY_PHYSICAL, "Zeta", "Alpha", "Mid"]


def test_attribute_catalog_groups_distinct_attributes(make_gdtf):
    target = make_gdtf(
        "target.gdtf",
        name="Target",
        geometries_xml=_TWO_BEAM_GEOMETRIES_XML,
        models_xml=_TWO_MODEL_XML,
    )
    comparison = make_gdtf(
        "comparison.gdtf",
        name="Comparison",
        geometries_xml=_TWO_BEAM_GEOMETRIES_XML,
        models_xml=_TWO_MODEL_XML,
    )

    result = compare_files(str(target), [str(comparison)])
    catalog = attribute_catalog(result)

    assert catalog[0] == (
        CATEGORY_BEAM,
        (
            "BeamAngle",
            "FieldAngle",
            "PowerConsumption",
            "LuminousFlux",
            "ColorTemperature",
            "BeamType",
        ),
    )
    assert catalog[1] == (
        CATEGORY_PHYSICAL,
        ("Weight", "Width", "Height", "Length"),
    )


def test_attribute_catalog_empty_result():
    target = _fixture_model("/fixtures/target.gdtf", "Target", {})

    result = compare(target, [])

    assert result.rows == ()
    assert attribute_catalog(result) == ()
