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
- Model dimensions are per-Model entry: every fixture_type.models entry
  contributes its own MODEL_ATTRIBUTES (Width, Height, Length) keys under
  CATEGORY_PHYSICAL, keyed by that model's name (or a positional
  "(unnamed model N)" label when the model has no name). Every model gets
  its own three rows -- none is dropped, merged, or aggregated (RESEARCH
  Pitfall 3: Weight is one fixture-level scalar, Width/Height/Length are N
  per-model values, and both cardinalities are represented explicitly).
- DMX attribute definitions are per-Attribute entry: every
  fixture_type.attributes entry (the flat <AttributeDefinitions><Attributes>
  vocabulary -- Pan, Tilt, Dimmer, Gobo1, and so on; DMX modes/channels are
  out of scope, Plan 02-02) contributes its own six
  ATTRIBUTE_DEFINITION_PROPERTIES keys under "DMX: <feature group>"
  (dmx_attribute_category), keyed by that definition's Name (or a positional
  "(unnamed attribute N)" label). The prefix guarantees a file-supplied
  feature-group or attribute name can never collide with, merge into, or
  silently default-check CATEGORY_BEAM/CATEGORY_PHYSICAL.

Duplicate or missing element names never overwrite each other: a repeated
path gets a "#N" suffix (_unique_path) and an unnamed geometry gets the
UNNAMED_GEOMETRY placeholder.

Presence, not value (Plan 01-06): pygdtf 1.4.5 backfills GDTF-spec defaults
for every omitted Beam attribute (BeamAngle/FieldAngle 25, PowerConsumption
1000, LuminousFlux 10000, ColorTemperature 6000, BeamType Wash), Weight (0)
and Model dimension (Width/Height/Length 0) into its object model, and never
exposes that the value was defaulted rather than declared. extract_attributes
is therefore handed the validated <GDTF> tree (core.hardening.ValidatedGDTF.
description_root, from the same read pygdtf parsed) alongside the pygdtf
FixtureType, and checks -- for every displayed attribute -- whether the
manufacturer's file actually declared it, by looking for that exact XML
attribute name on the paired element. An undeclared attribute is always None
("N/A" via format_value), even when pygdtf's backfilled value happens to
equal what a real declaration would show; a declared value is always shown
as declared, even when it equals the spec default. The validated tree and
pygdtf's parsed model must be walked in lockstep (the same child-tag filter
pygdtf itself applies, pygdtf.geometries.TAG_TO_GEOMETRY_CLASS) so presence
is read from the correct paired element; any divergence raises
DescriptionMismatchError rather than guessing (fail closed, T-01-23).
"""

from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, Set, Tuple
from xml.etree.ElementTree import Element

from gdtf_comparer.core.models import (
    CATEGORY_BEAM,
    CATEGORY_PHYSICAL,
    DMX_ATTRIBUTE_CATEGORY_PREFIX,
    FIXTURE_LEVEL_PATH,
    UNGROUPED_FEATURE_GROUP,
    AttributeKey,
    AttributeValue,
)

from pygdtf.geometries import TAG_TO_GEOMETRY_CLASS, GeometryBeam


class DescriptionMismatchError(ValueError):
    """Raised when the validated description.xml tree cannot be paired with
    pygdtf's parsed model.

    Extraction never parses bytes itself -- it only reads the tree it is
    given. This is raised when that tree cannot be walked in lockstep with
    pygdtf's own object model (a missing FixtureType element, or a geometry/
    model count or type mismatch during the lockstep walk), so that a
    possibly-misattributed presence result is never silently shown. Its
    message is fixed text that never includes file content (T-01-25); the
    repository reports only this exception's type name in the user-facing
    error (T-01-17).
    """

BEAM_ATTRIBUTES: Tuple[Tuple[str, str], ...] = (
    ("BeamAngle", "beam_angle"),
    ("FieldAngle", "field_angle"),
    ("PowerConsumption", "power_consumption"),
    ("LuminousFlux", "luminous_flux"),
    ("ColorTemperature", "color_temperature"),
    ("BeamType", "beam_type"),
)

MODEL_ATTRIBUTES: Tuple[Tuple[str, str], ...] = (
    ("Width", "width"),
    ("Height", "height"),
    ("Length", "length"),
)

# (XML attribute name, pygdtf field name, value transform) triple used by the
# DMX attribute-definition presence check (_declared_values).
AttributeSpec = Tuple[str, str, Callable[[Any], AttributeValue]]


def _as_float(raw: Any) -> AttributeValue:
    """Return raw as a float."""
    return float(raw)


def _enum_value(raw: Any) -> AttributeValue:
    """Return a pygdtf Enum-like value's validated text (its .value)."""
    return raw.value


def _link_text(raw: Any) -> AttributeValue:
    """Return a pygdtf NodeLink's raw link text.

    Never use str() on a NodeLink here -- an omitted link's str() is the
    four-letter word "None" (RESEARCH.md, Design notes), which would read as
    a declared value instead of the correct N/A.
    """
    return raw.str_link


def _as_text(raw: Any) -> AttributeValue:
    """Return raw as plain text (str(raw)) -- used for Pretty and Color."""
    return str(raw)


ATTRIBUTE_DEFINITION_PROPERTIES: Tuple[AttributeSpec, ...] = (
    ("Pretty", "pretty", _as_text),
    ("Feature", "feature", _link_text),
    ("ActivationGroup", "activation_group", _link_text),
    ("MainAttribute", "main_attribute", _link_text),
    ("PhysicalUnit", "physical_unit", _enum_value),
    ("Color", "color", _as_text),
)

PATH_SEPARATOR = "/"
UNNAMED_GEOMETRY = "(unnamed)"


def _geometry_children(element: Optional[Element]) -> List[Element]:
    """Return element's children whose tag pygdtf treats as a geometry node.

    Parameters:
        element: The XML element whose children to filter, or None.

    Returns:
        The children of element, in document order, whose tag is a key of
        pygdtf.geometries.TAG_TO_GEOMETRY_CLASS -- exactly the filter pygdtf
        itself applies both when collecting the top-level Geometries and
        inside Geometry._read_xml. An empty list when element is None.
    """
    if element is None:
        return []
    return [child for child in element if child.tag in TAG_TO_GEOMETRY_CLASS]


def iter_geometry_paths(
    fixture_type: Any, fixture_type_element: Element
) -> Iterator[Tuple[str, Any, Element]]:
    """Walk fixture_type.geometries and the validated tree in lockstep.

    Parameters:
        fixture_type: A parsed pygdtf.FixtureType instance.
        fixture_type_element: The <FixtureType> element from the validated
            description.xml tree.

    Yields:
        (path, node, element) triples, one per geometry node encountered in
        a depth-first pre-order walk using an explicit stack (no recursion).
        path is the "/"-joined chain of ancestor names down to and including
        node's own name (UNNAMED_GEOMETRY for a missing name). element is
        node's paired XML element from the validated tree, so a caller can
        check which attributes it actually declares. Descent stops at a
        GeometryReference (it has no .geometries attribute and pygdtf never
        parses its children), so each defined beam is yielded exactly once
        regardless of how many DMX modes exist.

    Raises:
        DescriptionMismatchError: the validated tree and pygdtf's parsed
            model cannot be paired element-for-element at some level (a
            child-count mismatch, or a tag that does not match the paired
            node's type).
    """
    root_nodes = list(getattr(fixture_type, "geometries", None) or [])
    root_elements = _geometry_children(fixture_type_element.find("Geometries"))
    if len(root_nodes) != len(root_elements):
        raise DescriptionMismatchError(
            "the validated description.xml tree's top-level geometries do "
            "not match pygdtf's parsed geometries."
        )

    # Push children reversed so popping from the end preserves document order.
    stack: List[Tuple[Any, Element, str]] = [
        (node, element, "")
        for node, element in reversed(list(zip(root_nodes, root_elements)))
    ]
    while stack:
        node, element, ancestor_path = stack.pop()
        if TAG_TO_GEOMETRY_CLASS.get(element.tag) is not type(node):
            raise DescriptionMismatchError(
                "the validated description.xml tree's geometry tag does not "
                "match pygdtf's parsed geometry type."
            )

        name = getattr(node, "name", None) or UNNAMED_GEOMETRY
        path = name if not ancestor_path else f"{ancestor_path}{PATH_SEPARATOR}{name}"
        yield path, node, element

        if not hasattr(node, "geometries"):
            # GeometryReference has no .geometries attribute; pygdtf never
            # descends into a reference's children, and neither do we.
            continue
        child_nodes = list(node.geometries or [])
        child_elements = _geometry_children(element)
        if len(child_nodes) != len(child_elements):
            raise DescriptionMismatchError(
                "the validated description.xml tree's geometry children do "
                "not match pygdtf's parsed geometry children."
            )
        for child_pair in reversed(list(zip(child_nodes, child_elements))):
            stack.append((*child_pair, path))


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


def _weight_declared(fixture_type_element: Element) -> bool:
    """Return True only when the file declares <Weight Value=...>.

    Mirrors pygdtf's own lookup chain exactly (Properties._read_xml): a
    first-match find of PhysicalDescriptions, then Properties, then Weight,
    with the Weight element additionally required to carry a "Value"
    attribute (the attribute pygdtf itself reads).

    Parameters:
        fixture_type_element: The <FixtureType> element from the validated
            description.xml tree.

    Returns:
        True only when PhysicalDescriptions, then Properties, then Weight
        are each found by a first-match find, and the Weight element has a
        "Value" attribute.
    """
    physical_descriptions = fixture_type_element.find("PhysicalDescriptions")
    if physical_descriptions is None:
        return False
    properties_element = physical_descriptions.find("Properties")
    if properties_element is None:
        return False
    weight_element = properties_element.find("Weight")
    if weight_element is None:
        return False
    return "Value" in weight_element.attrib


def _declared_values(
    node: Any, element: Element, specs: Sequence[AttributeSpec]
) -> Iterator[Tuple[str, AttributeValue]]:
    """Apply the declared-vs-default presence check uniformly (Plan 01-06).

    This is the single presence-check path every displayed attribute in this
    module goes through: presence is read from the validated XML element
    (element.attrib), and the value is read from pygdtf (node) -- so a
    pygdtf default or placeholder is never reported as declared.

    Parameters:
        node: The pygdtf object instance carrying the parsed fields.
        element: node's paired XML element from the validated tree.
        specs: (gdtf_xml_name, pygdtf_field_name, value_transform) triples,
            in the order rows should be produced.

    Yields:
        (gdtf_xml_name, value) pairs, one per spec, in spec order. value is
        None when gdtf_xml_name is not in element.attrib, or when the raw
        pygdtf field itself is None; otherwise transform(raw pygdtf value).
    """
    for gdtf_name, field_name, transform in specs:
        if gdtf_name not in element.attrib:
            yield gdtf_name, None
            continue
        raw_value = getattr(node, field_name, None)
        yield gdtf_name, (transform(raw_value) if raw_value is not None else None)


def dmx_attribute_category(feature_link: Optional[str]) -> str:
    """Return the picker section a DMX attribute definition belongs to (D-01).

    Parameters:
        feature_link: The definition's Feature link text (its
            "<FeatureGroup>.<Feature>" string), or None.

    Returns:
        DMX_ATTRIBUTE_CATEGORY_PREFIX plus the text before feature_link's
        first ".", stripped, or plus UNGROUPED_FEATURE_GROUP when that text
        is missing or blank. The prefix guarantees this can never collide
        with CATEGORY_BEAM, CATEGORY_PHYSICAL, or any other legacy category
        (assumption_delta_decision, 02-02-PLAN.md).
    """
    group = (feature_link or "").split(".", 1)[0].strip()
    return DMX_ATTRIBUTE_CATEGORY_PREFIX + (group or UNGROUPED_FEATURE_GROUP)


def _attribute_definition_elements(fixture_type_element: Element) -> List[Element]:
    """Return the <Attribute> elements declared under AttributeDefinitions.

    Mirrors pygdtf's own lookup chain exactly (FixtureType._read_xml): a
    first-match find of AttributeDefinitions, then of Attributes, then
    findall("Attribute").

    Parameters:
        fixture_type_element: The <FixtureType> element from the validated
            description.xml tree.

    Returns:
        The <Attribute> elements in document order, or [] when either
        container is missing.
    """
    definitions_element = fixture_type_element.find("AttributeDefinitions")
    if definitions_element is None:
        return []
    attributes_element = definitions_element.find("Attributes")
    if attributes_element is None:
        return []
    return attributes_element.findall("Attribute")


def extract_attributes(
    fixture_type: Any, description_root: Element
) -> Dict[AttributeKey, AttributeValue]:
    """Build the namespaced attribute map for a parsed pygdtf FixtureType.

    Parameters:
        fixture_type: A parsed pygdtf.FixtureType instance.
        description_root: The validated <GDTF> root element (from
            core.hardening.prevalidate_gdtf_document, parsed from the same
            bytes pygdtf parsed), used only to decide whether each displayed
            attribute was declared in the manufacturer's file. Extraction
            never parses XML itself -- it only reads this tree.

    Returns:
        A dict keyed by AttributeKey covering: the single fixture-level
        Weight key; six BEAM_ATTRIBUTES keys per GeometryBeam node found by
        iter_geometry_paths, namespaced by that beam's unique element path;
        three MODEL_ATTRIBUTES keys per fixture_type.models entry, namespaced
        by that model's unique name (or a positional unnamed-model label);
        and, per <AttributeDefinitions><Attributes><Attribute> entry, six
        ATTRIBUTE_DEFINITION_PROPERTIES keys under
        "DMX: <feature group>" (dmx_attribute_category), namespaced by that
        definition's unique Name (or a positional unnamed-attribute label).
        Only the flat AttributeDefinitions vocabulary is read here -- DMX
        modes, channels, logical channels, channel functions and channel
        sets are out of scope for this extraction (assumption_delta_decision,
        02-02-PLAN.md).
        A key's value is None when the attribute was not declared in this
        file, even if pygdtf's object model carries a GDTF-spec-default
        substitute for it; declared values (including ones equal to the
        spec default) are always shown as declared, from pygdtf.

    Raises:
        DescriptionMismatchError: description_root has no FixtureType
            element, or the validated tree cannot be paired element-for-
            element with pygdtf's parsed model or attribute definitions.
    """
    fixture_type_element = description_root.find("FixtureType")
    if fixture_type_element is None:
        raise DescriptionMismatchError(
            "the validated description.xml tree has no FixtureType element."
        )

    attributes: Dict[AttributeKey, AttributeValue] = {}

    weight: AttributeValue = None
    properties = getattr(fixture_type, "properties", None)
    if properties is not None and _weight_declared(fixture_type_element):
        raw_weight = getattr(properties, "weight", None)
        if raw_weight is not None:
            weight = float(raw_weight)
    attributes[AttributeKey(CATEGORY_PHYSICAL, FIXTURE_LEVEL_PATH, "Weight")] = weight

    beam_paths: Set[str] = set()
    for path, node, element in iter_geometry_paths(fixture_type, fixture_type_element):
        if not isinstance(node, GeometryBeam):
            continue
        element_path = _unique_path(path, beam_paths)
        for gdtf_name, field_name in BEAM_ATTRIBUTES:
            if gdtf_name not in element.attrib:
                value: AttributeValue = None
            else:
                raw_value = getattr(node, field_name, None)
                if gdtf_name == "BeamType":
                    # pygdtf's beam_type is never None -- a None here comes
                    # only from the presence check above (closes REVIEW IN-03).
                    value = raw_value.value if raw_value is not None else None
                else:
                    value = float(raw_value) if raw_value is not None else None
            attributes[AttributeKey(CATEGORY_BEAM, element_path, gdtf_name)] = value

    models_element = fixture_type_element.find("Models")
    raw_models = models_element.findall("Model") if models_element is not None else []
    models = list(getattr(fixture_type, "models", None) or [])
    if len(models) != len(raw_models):
        raise DescriptionMismatchError(
            "the validated description.xml tree's Models do not match "
            "pygdtf's parsed models."
        )

    model_paths: Set[str] = set()
    for index, (model, model_element) in enumerate(zip(models, raw_models), start=1):
        model_name = getattr(model, "name", None) or f"(unnamed model {index})"
        element_path = _unique_path(model_name, model_paths)
        for gdtf_name, field_name in MODEL_ATTRIBUTES:
            if gdtf_name not in model_element.attrib:
                value = None
            else:
                raw_value = getattr(model, field_name, None)
                value = float(raw_value) if raw_value is not None else None
            attributes[AttributeKey(CATEGORY_PHYSICAL, element_path, gdtf_name)] = value

    raw_definitions = _attribute_definition_elements(fixture_type_element)
    definitions = list(getattr(fixture_type, "attributes", None) or [])
    if len(definitions) != len(raw_definitions):
        raise DescriptionMismatchError(
            "the validated description.xml tree's attribute definitions do "
            "not match pygdtf's parsed attribute definitions."
        )

    definition_names: Set[str] = set()
    for index, (definition, element) in enumerate(zip(definitions, raw_definitions), start=1):
        name = getattr(definition, "name", None) or f"(unnamed attribute {index})"
        attribute_name = _unique_path(name, definition_names)
        values = list(_declared_values(definition, element, ATTRIBUTE_DEFINITION_PROPERTIES))
        feature = dict(values)["Feature"]
        category = dmx_attribute_category(feature if isinstance(feature, str) else None)
        for property_name, value in values:
            attributes[AttributeKey(category, property_name, attribute_name)] = value

    return attributes
