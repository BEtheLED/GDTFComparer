"""Builds the namespaced attribute projection of a parsed pygdtf fixture (D-11).

Keys follow the (category, element path, attribute) scheme defined in
core.models.AttributeKey. Two different cardinalities are covered here
(RESEARCH Pitfall 3):

- Weight is a single fixture-level scalar (element_path = FIXTURE_LEVEL_PATH).
- Beam attributes are per-GeometryBeam node: the fixture's geometry tree is
  walked iteratively (iter_geometry_paths -- explicit stack, document order,
  GeometryReference targets never followed) and every GeometryBeam
  contributes its own BEAM_ATTRIBUTES keys under CATEGORY_BEAM, keyed by the
  full ancestor-to-beam geometry path joined by "/" (e.g. "Body/Head1/Beam").
  Plan 01-03 Task 2 adds per-Model Width/Height/Length keys under
  CATEGORY_PHYSICAL the same way, keyed by model name.

Duplicate or missing element names never overwrite each other: a repeated
path gets a "#N" suffix (_unique_path) and an unnamed geometry gets the
UNNAMED_GEOMETRY placeholder.
"""

from typing import Any, Dict, Iterator, List, Set, Tuple

from gdtf_comparer.core.models import (
    CATEGORY_BEAM,
    CATEGORY_PHYSICAL,
    FIXTURE_LEVEL_PATH,
    AttributeKey,
    AttributeValue,
)

from pygdtf.geometries import GeometryBeam

BEAM_ATTRIBUTES: Tuple[Tuple[str, str], ...] = (
    ("BeamAngle", "beam_angle"),
    ("FieldAngle", "field_angle"),
    ("PowerConsumption", "power_consumption"),
    ("LuminousFlux", "luminous_flux"),
    ("ColorTemperature", "color_temperature"),
    ("BeamType", "beam_type"),
)

PATH_SEPARATOR = "/"
UNNAMED_GEOMETRY = "(unnamed)"


def iter_geometry_paths(fixture_type: Any) -> Iterator[Tuple[str, Any]]:
    """Walk fixture_type.geometries iteratively, in document order.

    Parameters:
        fixture_type: A parsed pygdtf.FixtureType instance.

    Yields:
        (path, node) pairs, one per geometry node encountered in a
        depth-first pre-order walk using an explicit stack (no recursion).
        path is the "/"-joined chain of ancestor names down to and
        including node's own name (UNNAMED_GEOMETRY for a missing name).
        GeometryReference targets are never followed, so each defined beam
        is yielded exactly once regardless of how many DMX modes exist.
    """
    roots = getattr(fixture_type, "geometries", None) or []
    # Push children reversed so popping from the end preserves document order.
    stack: List[Tuple[Any, str]] = [(node, "") for node in reversed(list(roots))]
    while stack:
        node, ancestor_path = stack.pop()
        name = getattr(node, "name", None) or UNNAMED_GEOMETRY
        path = name if not ancestor_path else f"{ancestor_path}{PATH_SEPARATOR}{name}"
        yield path, node
        children = getattr(node, "geometries", None) or []
        for child in reversed(list(children)):
            stack.append((child, path))


def _unique_path(path: str, used: Set[str]) -> str:
    """Return path unchanged if unused, else the first "path#N" not yet used.

    Parameters:
        path: The candidate element path.
        used: The set of paths already assigned during this
            extract_attributes call; mutated in place to record the
            returned path.

    Returns:
        path if not already in used, else "{path}#2", "{path}#3", ... --
        whichever is the first not already present in used.
    """
    if path not in used:
        used.add(path)
        return path
    suffix = 2
    candidate = f"{path}#{suffix}"
    while candidate in used:
        suffix += 1
        candidate = f"{path}#{suffix}"
    used.add(candidate)
    return candidate


def extract_attributes(fixture_type: Any) -> Dict[AttributeKey, AttributeValue]:
    """Build the namespaced attribute map for a parsed pygdtf FixtureType.

    Parameters:
        fixture_type: A parsed pygdtf.FixtureType instance.

    Returns:
        A dict keyed by AttributeKey covering: the single fixture-level
        Weight key; six BEAM_ATTRIBUTES keys per GeometryBeam node found by
        iter_geometry_paths, namespaced by that beam's unique element path.
    """
    attributes: Dict[AttributeKey, AttributeValue] = {}

    weight: AttributeValue = None
    properties = getattr(fixture_type, "properties", None)
    if properties is not None:
        raw_weight = getattr(properties, "weight", None)
        if raw_weight is not None:
            weight = float(raw_weight)
    attributes[AttributeKey(CATEGORY_PHYSICAL, FIXTURE_LEVEL_PATH, "Weight")] = weight

    beam_paths: Set[str] = set()
    for path, node in iter_geometry_paths(fixture_type):
        if not isinstance(node, GeometryBeam):
            continue
        element_path = _unique_path(path, beam_paths)
        for gdtf_name, field_name in BEAM_ATTRIBUTES:
            raw_value = getattr(node, field_name, None)
            if gdtf_name == "BeamType":
                value: AttributeValue = raw_value.value if raw_value is not None else None
            elif raw_value is None:
                value = None
            else:
                value = float(raw_value)
            attributes[AttributeKey(CATEGORY_BEAM, element_path, gdtf_name)] = value

    return attributes
