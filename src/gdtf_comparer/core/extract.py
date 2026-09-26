"""Builds the namespaced attribute projection of a parsed pygdtf fixture (D-11).

Keys follow the (category, element path, attribute) scheme defined in
core.models.AttributeKey. This tracer extracts exactly one fixture-level
attribute (Physical Properties / Weight); Plan 01-03 adds per-GeometryBeam
and per-Model keys here without touching any other module.
"""

from typing import Any, Dict

from gdtf_comparer.core.models import (
    CATEGORY_PHYSICAL,
    FIXTURE_LEVEL_PATH,
    AttributeKey,
    AttributeValue,
)


def extract_attributes(fixture_type: Any) -> Dict[AttributeKey, AttributeValue]:
    """Build the namespaced attribute map for a parsed pygdtf FixtureType.

    Parameters:
        fixture_type: A parsed pygdtf.FixtureType instance.

    Returns:
        A dict containing the single fixture-level
        AttributeKey(CATEGORY_PHYSICAL, FIXTURE_LEVEL_PATH, "Weight") key
        mapped to float(fixture_type.properties.weight), or None when
        properties or weight is missing.
    """
    weight: AttributeValue = None
    properties = getattr(fixture_type, "properties", None)
    if properties is not None:
        raw_weight = getattr(properties, "weight", None)
        if raw_weight is not None:
            weight = float(raw_weight)

    return {
        AttributeKey(CATEGORY_PHYSICAL, FIXTURE_LEVEL_PATH, "Weight"): weight,
    }
