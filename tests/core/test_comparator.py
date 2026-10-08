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

    # Two beams in one file still stay distinct rows (Phase 01 D-11); across
    # files they are labelled by position, not by element path (G-03-3).
    by_path = {row.key.element_path: row for row in beam_angle_rows}
    head1_row = by_path["Beam 1"]
    head2_row = by_path["Beam 2"]

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
    assert row.key.element_path == "Beam 1"


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
    # Per-model dimensions (Width/Height/Length) are not part of a
    # cross-file comparison (G-03-3) -- only the fixture-level Weight is.
    assert catalog[1] == (CATEGORY_PHYSICAL, ("Weight",))


def test_attribute_catalog_empty_result():
    target = _fixture_model("/fixtures/target.gdtf", "Target", {})

    result = compare(target, [])

    assert result.rows == ()
    assert attribute_catalog(result) == ()


# --- G-03-3: beams matched across files by position; per-model dimension
# rows dropped from cross-file comparison entirely (both 2026-10-07 user
# decisions, 03-UAT.md). ---


def test_beams_match_by_position_across_different_geometry_names(make_gdtf):
    target = make_gdtf(
        "target.gdtf",
        name="Target",
        geometries_xml=(
            '<Geometry Name="Base 1">'
            '<Geometry Name="LED 1">'
            '<Beam Name="Pixel 1" BeamAngle="60" FieldAngle="107" PowerConsumption="250"/>'
            "</Geometry></Geometry>"
        ),
    )
    comparison = make_gdtf(
        "comparison.gdtf",
        name="Comparison",
        geometries_xml=(
            '<Geometry Name="Body">'
            '<Beam Name="Beam" BeamAngle="58.1" FieldAngle="79.8" PowerConsumption="200"/>'
            "</Geometry>"
        ),
    )

    result = compare_files(str(target), [str(comparison)])

    beam_rows = [row for row in result.rows if row.key.category == CATEGORY_BEAM]
    assert len(beam_rows) == 6
    assert all(row.key.element_path == "Beam 1" for row in beam_rows)
    assert not any(row.key.element_path == "Base 1/LED 1/Pixel 1" for row in result.rows)
    assert not any(row.key.element_path == "Body/Beam" for row in result.rows)

    by_attribute = {row.key.attribute: row for row in beam_rows}
    assert by_attribute["BeamAngle"].target_value == 60.0
    assert by_attribute["BeamAngle"].comparison_values == (58.1,)
    assert by_attribute["BeamAngle"].differs == (True,)
    assert by_attribute["FieldAngle"].target_value == 107.0
    assert by_attribute["FieldAngle"].comparison_values == (79.8,)
    assert by_attribute["PowerConsumption"].target_value == 250.0
    assert by_attribute["PowerConsumption"].comparison_values == (200.0,)


def test_identical_beams_with_different_names_do_not_differ(make_gdtf):
    target = make_gdtf(
        "target.gdtf",
        name="Target",
        geometries_xml=(
            '<Geometry Name="Head"><Beam Name="Beam" BeamAngle="10" FieldAngle="15"/></Geometry>'
        ),
    )
    comparison = make_gdtf(
        "comparison.gdtf",
        name="Comparison",
        geometries_xml=(
            '<Geometry Name="Lamp"><Beam Name="Lens" BeamAngle="10" FieldAngle="15"/></Geometry>'
        ),
    )

    result = compare_files(str(target), [str(comparison)])

    beam_rows = [row for row in result.rows if row.key.category == CATEGORY_BEAM]
    assert beam_rows
    assert all(row.differs == (False,) for row in beam_rows)


def test_one_beam_vs_two_beams(make_gdtf):
    target = make_gdtf(
        "target.gdtf",
        name="Target",
        geometries_xml='<Geometry Name="Head"><Beam Name="Beam" BeamAngle="10"/></Geometry>',
    )
    comparison = make_gdtf(
        "comparison.gdtf",
        name="Comparison",
        geometries_xml=(
            '<Geometry Name="Bar">'
            '<Beam Name="Cell A" BeamAngle="15"/>'
            '<Beam Name="Cell B" BeamAngle="35"/>'
            "</Geometry>"
        ),
    )

    result = compare_files(str(target), [str(comparison)])

    beam_rows = [row for row in result.rows if row.key.category == CATEGORY_BEAM]
    assert len(beam_rows) == 12
    beam_1_rows = [row for row in beam_rows if row.key.element_path == "Beam 1"]
    beam_2_rows = [row for row in beam_rows if row.key.element_path == "Beam 2"]
    assert len(beam_1_rows) == 6
    assert len(beam_2_rows) == 6
    assert max(result.rows.index(row) for row in beam_1_rows) < min(
        result.rows.index(row) for row in beam_2_rows
    )

    beam_1_angle = next(row for row in beam_1_rows if row.key.attribute == "BeamAngle")
    assert beam_1_angle.target_value == 10.0
    assert beam_1_angle.comparison_values == (15.0,)
    assert beam_1_angle.differs == (True,)

    beam_2_angle = next(row for row in beam_2_rows if row.key.attribute == "BeamAngle")
    assert beam_2_angle.target_value is None
    assert beam_2_angle.comparison_values == (35.0,)
    assert beam_2_angle.differs == (True,)


def test_two_beams_vs_one_beam(make_gdtf):
    target = make_gdtf(
        "target.gdtf",
        name="Target",
        geometries_xml=(
            '<Geometry Name="Bar">'
            '<Beam Name="Cell A" BeamAngle="15"/>'
            '<Beam Name="Cell B" BeamAngle="35"/>'
            "</Geometry>"
        ),
    )
    comparison = make_gdtf(
        "comparison.gdtf",
        name="Comparison",
        geometries_xml='<Geometry Name="Head"><Beam Name="Beam" BeamAngle="10"/></Geometry>',
    )

    result = compare_files(str(target), [str(comparison)])

    beam_rows = [row for row in result.rows if row.key.category == CATEGORY_BEAM]
    beam_1_angle = next(
        row
        for row in beam_rows
        if row.key.element_path == "Beam 1" and row.key.attribute == "BeamAngle"
    )
    assert beam_1_angle.target_value == 15.0
    assert beam_1_angle.comparison_values == (10.0,)
    assert beam_1_angle.differs == (True,)

    beam_2_angle = next(
        row
        for row in beam_rows
        if row.key.element_path == "Beam 2" and row.key.attribute == "BeamAngle"
    )
    assert beam_2_angle.target_value == 35.0
    assert beam_2_angle.comparison_values == (None,)
    assert beam_2_angle.differs == (True,)


def test_zero_beams_vs_one_beam(make_gdtf):
    target = make_gdtf("target.gdtf", name="Target", geometries_xml="")
    comparison = make_gdtf(
        "comparison.gdtf",
        name="Comparison",
        geometries_xml='<Geometry Name="Head"><Beam Name="Beam" BeamAngle="20"/></Geometry>',
    )

    result = compare_files(str(target), [str(comparison)])

    beam_rows = [row for row in result.rows if row.key.category == CATEGORY_BEAM]
    assert len(beam_rows) == 6
    assert all(row.key.element_path == "Beam 1" for row in beam_rows)
    assert all(row.target_value is None for row in beam_rows)

    beam_angle = next(row for row in beam_rows if row.key.attribute == "BeamAngle")
    assert beam_angle.comparison_values == (20.0,)
    assert beam_angle.differs == (True,)

    field_angle = next(row for row in beam_rows if row.key.attribute == "FieldAngle")
    assert field_angle.comparison_values == (None,)
    assert field_angle.differs == (False,)


def test_one_beam_vs_zero_beams(make_gdtf):
    target = make_gdtf(
        "target.gdtf",
        name="Target",
        geometries_xml='<Geometry Name="Head"><Beam Name="Beam" BeamAngle="20"/></Geometry>',
    )
    comparison = make_gdtf("comparison.gdtf", name="Comparison", geometries_xml="")

    result = compare_files(str(target), [str(comparison)])

    beam_rows = [row for row in result.rows if row.key.category == CATEGORY_BEAM]
    beam_angle = next(row for row in beam_rows if row.key.attribute == "BeamAngle")
    assert beam_angle.target_value == 20.0
    assert beam_angle.comparison_values == (None,)
    assert beam_angle.differs == (True,)


def test_positions_align_independently_per_comparison_file(make_gdtf):
    target = make_gdtf(
        "target.gdtf",
        name="Target",
        geometries_xml='<Geometry Name="Head"><Beam Name="Beam" BeamAngle="10"/></Geometry>',
    )
    comparison_a = make_gdtf(
        "comparison_a.gdtf",
        name="Comparison A",
        geometries_xml=(
            '<Geometry Name="Bar">'
            '<Beam Name="Cell A" BeamAngle="10"/>'
            '<Beam Name="Cell B" BeamAngle="20"/>'
            "</Geometry>"
        ),
    )
    comparison_b = make_gdtf("comparison_b.gdtf", name="Comparison B", geometries_xml="")

    result = compare_files(str(target), [str(comparison_a), str(comparison_b)])

    beam_rows = [row for row in result.rows if row.key.category == CATEGORY_BEAM]
    beam_1_angle = next(
        row
        for row in beam_rows
        if row.key.element_path == "Beam 1" and row.key.attribute == "BeamAngle"
    )
    assert beam_1_angle.comparison_values == (10.0, None)
    assert beam_1_angle.differs == (False, True)

    beam_2_angle = next(
        row
        for row in beam_rows
        if row.key.element_path == "Beam 2" and row.key.attribute == "BeamAngle"
    )
    assert beam_2_angle.target_value is None
    assert beam_2_angle.comparison_values == (20.0, None)
    assert beam_2_angle.differs == (True, False)


def test_beam_position_follows_document_order_not_name(make_gdtf):
    target = make_gdtf(
        "target.gdtf",
        name="Target",
        geometries_xml=(
            '<Geometry Name="Zed"><Beam Name="B" BeamAngle="11"/></Geometry>'
            '<Geometry Name="Alpha"><Beam Name="B" BeamAngle="22"/></Geometry>'
        ),
    )
    comparison = make_gdtf(
        "comparison.gdtf",
        name="Comparison",
        geometries_xml='<Geometry Name="Alpha"><Beam Name="B" BeamAngle="11"/></Geometry>',
    )

    result = compare_files(str(target), [str(comparison)])

    beam_rows = [row for row in result.rows if row.key.category == CATEGORY_BEAM]
    beam_1_angle = next(
        row
        for row in beam_rows
        if row.key.element_path == "Beam 1" and row.key.attribute == "BeamAngle"
    )
    assert beam_1_angle.target_value == 11.0
    assert beam_1_angle.differs == (False,)

    beam_2_angle = next(
        row
        for row in beam_rows
        if row.key.element_path == "Beam 2" and row.key.attribute == "BeamAngle"
    )
    assert beam_2_angle.target_value == 22.0
    assert beam_2_angle.comparison_values == (None,)


def test_duplicate_beam_names_still_get_separate_positions(make_gdtf):
    target = make_gdtf(
        "target.gdtf",
        name="Target",
        geometries_xml=(
            '<Geometry Name="Body">'
            '<Beam Name="Beam" BeamAngle="10"/>'
            '<Beam Name="Beam" BeamAngle="30"/>'
            "</Geometry>"
        ),
    )
    comparison = make_gdtf(
        "comparison.gdtf",
        name="Comparison",
        geometries_xml=(
            '<Geometry Name="Lamp">'
            '<Beam Name="Left" BeamAngle="10"/>'
            '<Beam Name="Right" BeamAngle="30"/>'
            "</Geometry>"
        ),
    )

    result = compare_files(str(target), [str(comparison)])

    beam_angle_rows = [
        row
        for row in result.rows
        if row.key.category == CATEGORY_BEAM and row.key.attribute == "BeamAngle"
    ]
    assert len(beam_angle_rows) == 2
    assert all(row.differs == (False,) for row in beam_angle_rows)


def test_model_dimension_rows_are_not_compared(make_gdtf):
    target = make_gdtf(
        "target.gdtf",
        name="Target",
        weight=10.0,
        models_xml=(
            '<Model Name="Base" Width="0.4" Height="0.1" Length="0.4"/>'
            '<Model Name="Head" Width="0.2" Height="0.25" Length="0.3"/>'
        ),
    )
    comparison = make_gdtf(
        "comparison.gdtf",
        name="Comparison",
        weight=12.0,
        models_xml=(
            '<Model Name="Lens" Width="0.1" Height="0.1" Length="0.1"/>'
            '<Model Name="Pigtail" Width="0.01" Height="0.01" Length="1.5"/>'
        ),
    )

    result = compare_files(str(target), [str(comparison)])

    physical_rows = [row for row in result.rows if row.key.category == CATEGORY_PHYSICAL]
    assert len(physical_rows) == 1
    weight_row = physical_rows[0]
    assert weight_row.key.element_path == ""
    assert weight_row.key.attribute == "Weight"
    assert weight_row.target_value == 10.0
    assert weight_row.comparison_values == (12.0,)

    assert not any(row.key.attribute in ("Width", "Height", "Length") for row in result.rows)

    assert AttributeKey(CATEGORY_PHYSICAL, "Head", "Width") in result.target.attributes
    assert AttributeKey(CATEGORY_PHYSICAL, "Lens", "Width") in result.comparisons[0].attributes


def test_model_dimension_rows_dropped_even_with_identical_model_names(make_gdtf):
    target = make_gdtf(
        "target.gdtf", name="Target", models_xml=_TWO_MODEL_XML
    )
    comparison = make_gdtf(
        "comparison.gdtf", name="Comparison", models_xml=_TWO_MODEL_XML
    )

    result = compare_files(str(target), [str(comparison)])

    assert not any(row.key.attribute in ("Width", "Height", "Length") for row in result.rows)


def test_other_categories_still_match_by_exact_key():
    target = _fixture_model(
        "/fixtures/target.gdtf",
        "Target",
        {
            AttributeKey("DMX: Dimmer", "Pretty", "Dimmer"): "Dim",
            AttributeKey(CATEGORY_PHYSICAL, "", "Weight"): 5.0,
        },
    )
    comparison = _fixture_model(
        "/fixtures/comparison.gdtf",
        "Comparison",
        {
            AttributeKey("DMX: Dimmer", "Pretty", "Dimmer"): "Dim",
            AttributeKey(CATEGORY_PHYSICAL, "", "Weight"): 6.0,
        },
    )

    result = compare(target, [comparison])

    dimmer_rows = [
        row
        for row in result.rows
        if row.key == AttributeKey("DMX: Dimmer", "Pretty", "Dimmer")
    ]
    assert len(dimmer_rows) == 1
    assert dimmer_rows[0].target_value == "Dim"
    assert dimmer_rows[0].comparison_values == ("Dim",)

    weight_rows = [
        row for row in result.rows if row.key == AttributeKey(CATEGORY_PHYSICAL, "", "Weight")
    ]
    assert len(weight_rows) == 1
    assert weight_rows[0].target_value == 5.0
    assert weight_rows[0].comparison_values == (6.0,)


def test_compare_leaves_models_untouched():
    target_attributes = {
        AttributeKey(CATEGORY_BEAM, "Head/Beam", "BeamAngle"): 10.0,
        AttributeKey(CATEGORY_PHYSICAL, "Head", "Width"): 0.2,
    }
    comparison_attributes = {
        AttributeKey(CATEGORY_BEAM, "Lamp/Lens", "BeamAngle"): 12.0,
    }
    target_snapshot = dict(target_attributes)
    comparison_snapshot = dict(comparison_attributes)

    target = _fixture_model("/fixtures/target.gdtf", "Target", target_attributes)
    comparison = _fixture_model("/fixtures/comparison.gdtf", "Comparison", comparison_attributes)

    result = compare(target, [comparison])

    assert result.target is target
    assert result.comparisons[0] is comparison
    assert target.attributes == target_snapshot
    assert comparison.attributes == comparison_snapshot

    beam_rows = [row for row in result.rows if row.key.category == CATEGORY_BEAM]
    assert len(beam_rows) == 1
    assert beam_rows[0].key.element_path == "Beam 1"
    assert beam_rows[0].target_value == 10.0
    assert beam_rows[0].comparison_values == (12.0,)


def test_beam_position_label():
    from gdtf_comparer.core.comparator import beam_position_label

    assert beam_position_label(1) == "Beam 1"
    assert beam_position_label(12) == "Beam 12"
