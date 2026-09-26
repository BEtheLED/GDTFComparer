"""Typed domain models for GDTF attribute comparison (D-09, D-11, D-13).

Attributes are keyed by :class:`AttributeKey` (category, element path,
attribute name) instead of a bare attribute name, so same-named attributes on
different elements (multiple GeometryBeam nodes, multiple Model entries)
never collide. This module has zero Qt imports and no module-level mutable
state (D-16).
"""

import math
import os
from dataclasses import dataclass, field
from typing import Any, Mapping, Union

AttributeValue = Union[float, int, str, None]

CATEGORY_BEAM = "Beam"
CATEGORY_PHYSICAL = "Physical Properties"
DISPLAY_CATEGORIES: tuple = (CATEGORY_BEAM, CATEGORY_PHYSICAL)
FIXTURE_LEVEL_PATH = ""


@dataclass(frozen=True)
class AttributeKey:
    """Namespaced identity of a single comparable attribute value.

    Parameters:
        category: Display category, one of DISPLAY_CATEGORIES.
        element_path: Full path to the owning element (e.g. a geometry path
            or a model name), or FIXTURE_LEVEL_PATH for fixture-level values.
        attribute: The GDTF attribute name (e.g. "Weight", "BeamAngle").
    """

    category: str
    element_path: str
    attribute: str

    @property
    def element_label(self) -> str:
        """Return "Fixture" for fixture-level keys, else the element path."""
        if self.element_path == FIXTURE_LEVEL_PATH:
            return "Fixture"
        return self.element_path


@dataclass(frozen=True)
class FixtureModel:
    """A single loaded GDTF fixture, its namespaced attributes, and the raw model.

    Parameters:
        source_path: Path to the .gdtf file this model was loaded from.
        name: The fixture's display name.
        manufacturer: The fixture's manufacturer name.
        attributes: The namespaced display projection of this fixture's
            attributes for the Phase-1 categories (D-10/D-11) -- keyed by
            AttributeKey, not by bare attribute name.
        fixture_type: The full pygdtf FixtureType object model retained
            verbatim (D-09), exposing .geometries, .dmx_modes, .wheels,
            .models and .properties for later phases. Excluded from repr
            and equality since it is not a plain value type.
    """

    source_path: str
    name: str
    manufacturer: str
    attributes: Mapping["AttributeKey", AttributeValue]
    fixture_type: Any = field(default=None, repr=False, compare=False)

    @property
    def file_name(self) -> str:
        """Return the base file name of source_path."""
        return os.path.basename(self.source_path)


@dataclass(frozen=True)
class ComparisonRow:
    """One comparable row: a target value and each comparison file's value.

    Parameters:
        key: The AttributeKey identifying this row.
        target_value: The target fixture's value for this key, or None.
        comparison_values: Each comparison fixture's value for this key, in
            the same order as ComparisonResult.comparisons.
        differs: Whether each comparison value differs from target_value,
            in the same order as comparison_values.
    """

    key: AttributeKey
    target_value: AttributeValue
    comparison_values: tuple
    differs: tuple

    @property
    def any_differs(self) -> bool:
        """Return True if any comparison value differs from the target."""
        return any(self.differs)


@dataclass(frozen=True)
class ComparisonResult:
    """The full result of comparing a target fixture against N comparisons.

    Parameters:
        target: The target FixtureModel.
        comparisons: The comparison FixtureModels, in the order compared.
        rows: The comparable rows produced by core.comparator.compare.
    """

    target: FixtureModel
    comparisons: tuple
    rows: tuple


def format_value(value: AttributeValue) -> str:
    """Format an attribute value for display.

    Parameters:
        value: The value to format.

    Returns:
        "N/A" for None; a compact decimal string for float (no trailing
        zeros); str(value) for int; the string itself for str.
    """
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return format(value, ".10g")
    if isinstance(value, int):
        return str(value)
    return value


def values_equal(a: AttributeValue, b: AttributeValue) -> bool:
    """Compare two attribute values for display-equivalence.

    Parameters:
        a: The first value.
        b: The second value.

    Returns:
        True if both are None; False if exactly one is None; a
        tolerance-based comparison (rel_tol=1e-9, abs_tol=1e-12) if both are
        int/float; otherwise plain equality.
    """
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(float(a), float(b), rel_tol=1e-9, abs_tol=1e-12)
    return a == b
