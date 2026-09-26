"""Unit tests for core.extract: per-GeometryBeam and per-Model namespacing (D-11)."""

import pygdtf
import pytest

from gdtf_comparer.core.extract import DescriptionMismatchError, extract_attributes
from gdtf_comparer.core.hardening import prevalidate_gdtf_document
from gdtf_comparer.core.models import (
    CATEGORY_BEAM,
    CATEGORY_PHYSICAL,
    FIXTURE_LEVEL_PATH,
    AttributeKey,
)


def _extract(path):
    """Validate + open a .gdtf file and return its namespaced attribute dict."""
    validated = prevalidate_gdtf_document(str(path))
    with pygdtf.FixtureType(str(path)) as fixture_type:
        return extract_attributes(fixture_type, validated.description_root)


def test_omitted_weight_is_none_not_zero(make_gdtf):
    path = make_gdtf("fixture.gdtf", weight=None)

    with pygdtf.FixtureType(str(path)) as fixture_type:
        # pygdtf itself backfills 0 for an omitted Weight -- proves the
        # substitution this test guards against is real.
        assert fixture_type.properties.weight == 0

    attributes = _extract(path)

    weight_key = AttributeKey(CATEGORY_PHYSICAL, FIXTURE_LEVEL_PATH, "Weight")
    assert attributes[weight_key] is None


def test_declared_zero_weight_is_kept(make_gdtf):
    path = make_gdtf("fixture.gdtf", weight=0.0)

    attributes = _extract(path)

    weight_key = AttributeKey(CATEGORY_PHYSICAL, FIXTURE_LEVEL_PATH, "Weight")
    assert attributes[weight_key] == 0.0
    assert attributes[weight_key] is not None


def test_two_beams_same_names_do_not_collide(make_gdtf):
    geometries_xml = (
        '<Geometry Name="Body">'
        '<Geometry Name="Head1"><Beam Name="Beam" BeamAngle="10" FieldAngle="15"/></Geometry>'
        '<Geometry Name="Head2"><Beam Name="Beam" BeamAngle="30" FieldAngle="40"/></Geometry>'
        "</Geometry>"
    )
    path = make_gdtf("fixture.gdtf", geometries_xml=geometries_xml)

    attributes = _extract(path)

    assert attributes[AttributeKey(CATEGORY_BEAM, "Body/Head1/Beam", "BeamAngle")] == 10.0
    assert attributes[AttributeKey(CATEGORY_BEAM, "Body/Head2/Beam", "BeamAngle")] == 30.0
    assert attributes[AttributeKey(CATEGORY_BEAM, "Body/Head1/Beam", "FieldAngle")] == 15.0
    assert attributes[AttributeKey(CATEGORY_BEAM, "Body/Head2/Beam", "FieldAngle")] == 40.0


def test_beam_attribute_set_and_order(make_gdtf):
    geometries_xml = (
        '<Geometry Name="Head">'
        '<Beam Name="Beam" BeamAngle="10" FieldAngle="15" PowerConsumption="500"'
        ' LuminousFlux="2000" ColorTemperature="3000" BeamType="Wash"/>'
        "</Geometry>"
    )
    path = make_gdtf("fixture.gdtf", geometries_xml=geometries_xml)

    attributes = _extract(path)

    beam_keys = [key for key in attributes if key.category == CATEGORY_BEAM]
    assert [key.attribute for key in beam_keys] == [
        "BeamAngle",
        "FieldAngle",
        "PowerConsumption",
        "LuminousFlux",
        "ColorTemperature",
        "BeamType",
    ]


def test_beam_type_is_plain_string(make_gdtf):
    geometries_xml = '<Geometry Name="Head"><Beam Name="Beam" BeamType="Wash"/></Geometry>'
    path = make_gdtf("fixture.gdtf", geometries_xml=geometries_xml)

    attributes = _extract(path)

    value = attributes[AttributeKey(CATEGORY_BEAM, "Head/Beam", "BeamType")]
    assert value == "Wash"
    assert isinstance(value, str)


def test_duplicate_geometry_paths_get_suffix(make_gdtf):
    geometries_xml = (
        '<Geometry Name="Head"><Beam Name="Beam" BeamAngle="1"/></Geometry>'
        '<Geometry Name="Head"><Beam Name="Beam" BeamAngle="2"/></Geometry>'
    )
    path = make_gdtf("fixture.gdtf", geometries_xml=geometries_xml)

    attributes = _extract(path)

    assert attributes[AttributeKey(CATEGORY_BEAM, "Head/Beam", "BeamAngle")] == 1.0
    assert attributes[AttributeKey(CATEGORY_BEAM, "Head/Beam#2", "BeamAngle")] == 2.0


def test_nested_beam_path_includes_every_ancestor(make_gdtf):
    depth = 100
    xml = '<Beam Name="Beam" BeamAngle="7"/>'
    for i in range(depth, 0, -1):
        xml = f'<Geometry Name="G{i}">{xml}</Geometry>'
    path = make_gdtf("fixture.gdtf", geometries_xml=xml)

    attributes = _extract(path)

    beam_key = next(key for key in attributes if key.category == CATEGORY_BEAM)
    segments = beam_key.element_path.split("/")
    assert len(segments) == depth + 1
    assert segments[-1] == "Beam"
    assert attributes[beam_key] == 7.0


def test_fixture_without_beams_has_no_beam_keys(make_gdtf):
    geometries_xml = '<Geometry Name="Body"/>'
    path = make_gdtf("fixture.gdtf", weight=5.0, geometries_xml=geometries_xml)

    attributes = _extract(path)

    assert not any(key.category == CATEGORY_BEAM for key in attributes)
    assert attributes[AttributeKey(CATEGORY_PHYSICAL, FIXTURE_LEVEL_PATH, "Weight")] == 5.0


def test_models_dimensions_namespaced_per_model(make_gdtf):
    models_xml = (
        '<Model Name="Base" Width="0.4" Height="0.1" Length="0.4"/>'
        '<Model Name="Head" Width="0.2" Height="0.25" Length="0.3"/>'
    )
    path = make_gdtf("fixture.gdtf", models_xml=models_xml)

    attributes = _extract(path)

    assert attributes[AttributeKey(CATEGORY_PHYSICAL, "Base", "Width")] == 0.4
    assert attributes[AttributeKey(CATEGORY_PHYSICAL, "Base", "Height")] == 0.1
    assert attributes[AttributeKey(CATEGORY_PHYSICAL, "Base", "Length")] == 0.4
    assert attributes[AttributeKey(CATEGORY_PHYSICAL, "Head", "Width")] == 0.2
    assert attributes[AttributeKey(CATEGORY_PHYSICAL, "Head", "Height")] == 0.25
    assert attributes[AttributeKey(CATEGORY_PHYSICAL, "Head", "Length")] == 0.3

    model_keys = [
        key
        for key in attributes
        if key.category == CATEGORY_PHYSICAL and key.element_path in ("Base", "Head")
    ]
    assert [key.element_path for key in model_keys] == [
        "Base",
        "Base",
        "Base",
        "Head",
        "Head",
        "Head",
    ]
    assert [key.attribute for key in model_keys[:3]] == ["Width", "Height", "Length"]


def test_weight_single_fixture_level_key(make_gdtf):
    models_xml = (
        '<Model Name="Base" Width="0.4" Height="0.1" Length="0.4"/>'
        '<Model Name="Head" Width="0.2" Height="0.25" Length="0.3"/>'
    )
    path = make_gdtf("fixture.gdtf", weight=9.0, models_xml=models_xml)

    attributes = _extract(path)

    weight_keys = [key for key in attributes if key.attribute == "Weight"]
    assert len(weight_keys) == 1
    assert weight_keys[0].element_path == FIXTURE_LEVEL_PATH
    assert attributes[weight_keys[0]] == 9.0


def test_duplicate_model_names_get_suffix(make_gdtf):
    models_xml = (
        '<Model Name="Head" Width="0.1" Height="0.1" Length="0.1"/>'
        '<Model Name="Head" Width="0.2" Height="0.2" Length="0.2"/>'
    )
    path = make_gdtf("fixture.gdtf", models_xml=models_xml)

    attributes = _extract(path)

    assert attributes[AttributeKey(CATEGORY_PHYSICAL, "Head", "Width")] == 0.1
    assert attributes[AttributeKey(CATEGORY_PHYSICAL, "Head#2", "Width")] == 0.2


def test_unnamed_model_label(make_gdtf):
    models_xml = '<Model Width="0.1" Height="0.1" Length="0.1"/>'
    path = make_gdtf("fixture.gdtf", models_xml=models_xml)

    attributes = _extract(path)

    assert attributes[AttributeKey(CATEGORY_PHYSICAL, "(unnamed model 1)", "Width")] == 0.1


def test_omitted_beam_attributes_are_none(make_gdtf):
    geometries_xml = '<Geometry Name="Head"><Beam Name="Beam" BeamAngle="10"/></Geometry>'
    path = make_gdtf("fixture.gdtf", geometries_xml=geometries_xml)

    with pygdtf.FixtureType(str(path)) as fixture_type:
        # pygdtf itself backfills spec defaults for every omitted attribute --
        # proves the substitution this test guards against is real.
        beam_node = fixture_type.geometries[0].geometries[0]
        assert beam_node.field_angle == 25.0
        assert beam_node.power_consumption == 1000.0
        assert beam_node.luminous_flux == 10000.0
        assert beam_node.color_temperature == 6000.0
        assert beam_node.beam_type.value == "Wash"

    attributes = _extract(path)

    assert attributes[AttributeKey(CATEGORY_BEAM, "Head/Beam", "BeamAngle")] == 10.0
    assert attributes[AttributeKey(CATEGORY_BEAM, "Head/Beam", "FieldAngle")] is None
    assert attributes[AttributeKey(CATEGORY_BEAM, "Head/Beam", "PowerConsumption")] is None
    assert attributes[AttributeKey(CATEGORY_BEAM, "Head/Beam", "LuminousFlux")] is None
    assert attributes[AttributeKey(CATEGORY_BEAM, "Head/Beam", "ColorTemperature")] is None
    assert attributes[AttributeKey(CATEGORY_BEAM, "Head/Beam", "BeamType")] is None
    beam_keys = [
        key
        for key in attributes
        if key.category == CATEGORY_BEAM and key.element_path == "Head/Beam"
    ]
    assert len(beam_keys) == 6


def test_declared_spec_default_values_are_kept(make_gdtf):
    geometries_xml = (
        '<Geometry Name="Head">'
        '<Beam Name="Beam" BeamAngle="25" FieldAngle="25" PowerConsumption="1000"'
        ' LuminousFlux="10000" ColorTemperature="6000" BeamType="Wash"/>'
        "</Geometry>"
    )
    path = make_gdtf("fixture.gdtf", geometries_xml=geometries_xml)

    attributes = _extract(path)

    assert attributes[AttributeKey(CATEGORY_BEAM, "Head/Beam", "BeamAngle")] == 25.0
    assert attributes[AttributeKey(CATEGORY_BEAM, "Head/Beam", "FieldAngle")] == 25.0
    assert attributes[AttributeKey(CATEGORY_BEAM, "Head/Beam", "PowerConsumption")] == 1000.0
    assert attributes[AttributeKey(CATEGORY_BEAM, "Head/Beam", "LuminousFlux")] == 10000.0
    assert attributes[AttributeKey(CATEGORY_BEAM, "Head/Beam", "ColorTemperature")] == 6000.0
    assert attributes[AttributeKey(CATEGORY_BEAM, "Head/Beam", "BeamType")] == "Wash"


def test_omitted_model_dimensions_are_none(make_gdtf):
    models_xml = '<Model Name="Base" Width="0.4"/>'
    path = make_gdtf("fixture.gdtf", models_xml=models_xml)

    attributes = _extract(path)

    assert attributes[AttributeKey(CATEGORY_PHYSICAL, "Base", "Width")] == 0.4
    assert attributes[AttributeKey(CATEGORY_PHYSICAL, "Base", "Height")] is None
    assert attributes[AttributeKey(CATEGORY_PHYSICAL, "Base", "Length")] is None
    model_keys = [
        key
        for key in attributes
        if key.category == CATEGORY_PHYSICAL and key.element_path == "Base"
    ]
    assert len(model_keys) == 3


def test_presence_alignment_skips_references_and_unknown_tags(make_gdtf):
    geometries_xml = (
        '<Geometry Name="Body">'
        '<Geometry Name="Head1"><Beam Name="Beam" BeamAngle="10"/></Geometry>'
        '<GeometryReference Name="Ref" Geometry="Head1">'
        '<Break DMXOffset="1" DMXBreak="1"/>'
        "</GeometryReference>"
        '<NotAGeometry Name="Unknown"><Beam Name="Beam" BeamAngle="99"/></NotAGeometry>'
        '<Geometry Name="Head2"><Beam Name="Beam" FieldAngle="40"/></Geometry>'
        "</Geometry>"
    )
    path = make_gdtf("fixture.gdtf", geometries_xml=geometries_xml)

    attributes = _extract(path)

    assert attributes[AttributeKey(CATEGORY_BEAM, "Body/Head1/Beam", "BeamAngle")] == 10.0
    assert attributes[AttributeKey(CATEGORY_BEAM, "Body/Head1/Beam", "FieldAngle")] is None
    assert attributes[AttributeKey(CATEGORY_BEAM, "Body/Head2/Beam", "FieldAngle")] == 40.0
    assert attributes[AttributeKey(CATEGORY_BEAM, "Body/Head2/Beam", "BeamAngle")] is None
    beam_paths = {key.element_path for key in attributes if key.category == CATEGORY_BEAM}
    assert beam_paths == {"Body/Head1/Beam", "Body/Head2/Beam"}


def test_mismatched_description_raises(make_gdtf):
    validated_path = make_gdtf(
        "two-beams.gdtf",
        geometries_xml=(
            '<Geometry Name="Head1"><Beam Name="Beam" BeamAngle="10"/></Geometry>'
            '<Geometry Name="Head2"><Beam Name="Beam" BeamAngle="20"/></Geometry>'
        ),
    )
    fixture_path = make_gdtf(
        "one-beam.gdtf",
        geometries_xml='<Geometry Name="Head1"><Beam Name="Beam" BeamAngle="10"/></Geometry>',
    )
    validated = prevalidate_gdtf_document(str(validated_path))

    with pygdtf.FixtureType(str(fixture_path)) as fixture_type:
        with pytest.raises(DescriptionMismatchError):
            extract_attributes(fixture_type, validated.description_root)
