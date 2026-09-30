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

# Row-order anchor for core.comparator.compare (D-10 legacy order): these
# categories are always sorted first, in this order, ahead of every other
# category (which falls back to first-seen order). Never used to filter rows
# -- compare() returns every category it is given (ATTR-01/ATTR-02).
LEADING_CATEGORIES: tuple = (CATEGORY_BEAM, CATEGORY_PHYSICAL)

# D-04 first-use seed for gui.attribute_picker.AttributePicker: on first use
# (no prior selection), every attribute whose category is in this tuple
# starts checked, and every other attribute starts unchecked. Never used by
# core to filter or order rows -- selection is GUI-layer state only.
DEFAULT_SELECTED_CATEGORIES: tuple = (CATEGORY_BEAM, CATEGORY_PHYSICAL)

# Every category built from a GDTF <AttributeDefinitions><Attributes> entry's
# feature group starts with this prefix (core.extract.dmx_attribute_category).
# No legacy or DEFAULT_SELECTED_CATEGORIES category starts with it, so a
# file-supplied feature-group name (e.g. GDTF's standard "Beam" group) can
# never collide with, merge into, or default-check the legacy sections
# (assumption_delta_decision, 02-02-PLAN.md).
DMX_ATTRIBUTE_CATEGORY_PREFIX = "DMX: "

# Label used in place of a definition's feature group when that group cannot
# be determined (missing, empty, or dot-leading Feature link).
UNGROUPED_FEATURE_GROUP = "(no feature group)"

FIXTURE_LEVEL_PATH = ""


@dataclass(frozen=True)
class AttributeKey:
    """Namespaced identity of a single comparable attribute value.

    Parameters:
        category: Display category produced by core.extract (any string;
            the attribute picker groups by it).
        element_path: Full path to the owning element (e.g. a geometry path
            or a model name), or FIXTURE_LEVEL_PATH for fixture-level
            values, or, for a DMX attribute definition, the name of the
            definition property this row compares (Pretty, Feature,
            ActivationGroup, MainAttribute, PhysicalUnit or Color).
        attribute: The GDTF attribute name (e.g. "Weight", "BeamAngle", or
            a DMX attribute definition's Name such as "Pan").
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
            attributes (D-11) -- keyed by AttributeKey, not by bare
            attribute name. A None value means the
            attribute is not declared for that element in this file: either
            the owning element is absent, or the manufacturer's
            description.xml does not declare that attribute. GDTF-spec
            defaults that pygdtf substitutes for an omitted attribute are
            never reported here as if they were declared values (Plan
            01-06; closes 01-VERIFICATION.md Truth 6 / 01-REVIEW.md CR-01).
            Also includes one key per property of every
            AttributeDefinitions entry (Plan 02-02).
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
        """Return True if any comparison value differs from the target.

        Row-level predicate kept as intended future surface for Phase 2 diff
        highlighting (DIFF-01) and Phase 3 diff-only export (EXPORT-02).
        Review IN-01 decided to keep it unused in Phase 1; exercised by
        tests/core/test_models.py (Plan 01-07).
        """
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
        "N/A" for None (meaning: not specified in this file, per
        FixtureModel.attributes); a compact decimal string for float (no
        trailing zeros); str(value) for int; the string itself for str.
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
