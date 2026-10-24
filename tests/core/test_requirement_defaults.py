"""Default direction/tolerance table, units and declared-only options (D-05, D-06, SUB-02).

Pure, Qt-free tests for core.substitution's defaults: a sensible starting
direction and tolerance per attribute, a display unit alongside Beam and
Physical Properties numbers, and the rule that only values a fixture's own
file actually declares can ever become a markable row (RESEARCH Pitfall 6).
"""

import pytest

from gdtf_comparer.core.models import CATEGORY_BEAM, CATEGORY_PHYSICAL, AttributeKey
from gdtf_comparer.core.repository import FixtureRepository
from gdtf_comparer.core.substitution import (
    TOLERANCE_KIND,
    Direction,
    attribute_unit,
    default_direction,
    default_tolerance,
    requirement_options,
)


@pytest.mark.parametrize(
    "key, value, expected",
    [
        (AttributeKey(CATEGORY_PHYSICAL, "", "Weight"), 15.0, Direction.LOWER),
        (AttributeKey(CATEGORY_BEAM, "Beam 1", "PowerConsumption"), 450.0, Direction.LOWER),
        (AttributeKey(CATEGORY_BEAM, "Beam 1", "LuminousFlux"), 18000.0, Direction.HIGHER),
        (AttributeKey(CATEGORY_BEAM, "Beam 1", "BeamAngle"), 20.0, Direction.CLOSEST),
        (AttributeKey(CATEGORY_BEAM, "Beam 1", "FieldAngle"), 25.0, Direction.CLOSEST),
        (AttributeKey(CATEGORY_BEAM, "Beam 1", "ColorTemperature"), 6500.0, Direction.CLOSEST),
        (AttributeKey(CATEGORY_BEAM, "Beam 1", "BeamType"), "Spot", Direction.EXACT),
        (AttributeKey("DMX: Position", "PhysicalUnit", "Pan"), "Angle", Direction.EXACT),
        (AttributeKey("DMX: Position", "SomeProperty", "Weight"), "abc", Direction.EXACT),
        (AttributeKey(CATEGORY_BEAM, "Beam 1", "SomeUnknownAttribute"), 5.0, Direction.CLOSEST),
    ],
)
def test_default_directions(key, value, expected):
    assert default_direction(key, value) == expected


def test_default_tolerance_exact_is_zero():
    key = AttributeKey(CATEGORY_BEAM, "Beam 1", "BeamType")
    assert default_tolerance(key, "Spot", Direction.EXACT) == 0.0


def test_default_tolerance_numeric():
    weight_key = AttributeKey(CATEGORY_PHYSICAL, "", "Weight")
    if TOLERANCE_KIND == "percent":
        assert default_tolerance(weight_key, 15.0, Direction.LOWER) == 10.0
        assert default_tolerance(weight_key, -20.0, Direction.LOWER) == 10.0
        assert default_tolerance(weight_key, 0.0, Direction.LOWER) == 10.0
    else:
        assert default_tolerance(weight_key, 15.0, Direction.LOWER) == 1.5
        assert default_tolerance(weight_key, -20.0, Direction.LOWER) == 2.0
        assert default_tolerance(weight_key, 0.0, Direction.LOWER) == 0.0


def test_attribute_unit():
    assert attribute_unit(AttributeKey(CATEGORY_PHYSICAL, "", "Weight")) == "kg"
    assert attribute_unit(AttributeKey(CATEGORY_BEAM, "Beam 1", "BeamAngle")) == "°"
    assert attribute_unit(AttributeKey(CATEGORY_BEAM, "Beam 1", "LuminousFlux")) == "lm"
    assert attribute_unit(AttributeKey(CATEGORY_BEAM, "Beam 1", "ColorTemperature")) == "K"
    assert attribute_unit(AttributeKey(CATEGORY_BEAM, "Beam 1", "PowerConsumption")) == "W"
    assert attribute_unit(AttributeKey("DMX: Position", "SomeProperty", "Weight")) == ""
    assert attribute_unit(AttributeKey(CATEGORY_BEAM, "Beam 1", "SomeUnknownAttribute")) == ""


def test_only_declared_values_are_options(make_gdtf):
    """RESEARCH Pitfall 6 / P4: pygdtf's spec-default backfill never becomes an option.

    The fixture declares only BeamAngle and omits Weight entirely; pygdtf
    still backfills PowerConsumption=1000, LuminousFlux=10000,
    ColorTemperature=6000, FieldAngle=25, BeamType=Wash and Weight=0 into
    its object model, none of which may surface as a markable requirement.
    """
    path = make_gdtf(
        "sparse.gdtf",
        weight=None,
        geometries_xml='<Geometry Name="Head"><Beam Name="Beam" BeamAngle="20"/></Geometry>',
    )
    fixture = FixtureRepository().load(str(path))

    options = requirement_options(fixture)
    keys = [key for key, _ in options]

    assert keys == [AttributeKey(CATEGORY_BEAM, "Beam 1", "BeamAngle")]
    values = [value for _, value in options]
    assert 1000.0 not in values
    assert 10000.0 not in values
