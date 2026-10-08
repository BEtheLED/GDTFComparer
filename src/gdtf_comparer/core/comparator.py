"""Pure comparison logic and the batch service API (D-13, D-15).

compare() is a pure function of already-loaded FixtureModels. compare_files()
is the one and only core service call the GUI makes (via gui/worker.py);
never gets called with a Qt import anywhere on this side (D-16).

compare() lines rows up across files through a per-file cross-file view
(positional Beam rows, no per-model dimension rows; 03-UAT.md G-03-3), while
each FixtureModel keeps its own namespaced keys (D-11) untouched.
"""

from typing import Dict, List, Optional, Sequence, Tuple

from gdtf_comparer.core.models import (
    CATEGORY_BEAM,
    CATEGORY_PHYSICAL,
    FIXTURE_LEVEL_PATH,
    LEADING_CATEGORIES,
    AttributeKey,
    AttributeValue,
    ComparisonResult,
    ComparisonRow,
    FixtureModel,
    values_equal,
)
from gdtf_comparer.core.extract import MODEL_ATTRIBUTES
from gdtf_comparer.core.repository import FixtureRepository

# Row label for a cross-file Beam position (03-UAT.md G-03-3, user decision
# 2026-10-07): beam rows are matched across files by POSITION (1st beam vs
# 1st beam, 2nd vs 2nd, ...) rather than by each file's own geometry-element
# name, since different manufacturers almost never reuse the same names.
BEAM_POSITION_LABEL_TEMPLATE = "Beam {position}"

# Per-model physical-dimension attribute names (G-03-3, user decision
# 2026-10-07): these rows are dropped from cross-file comparison entirely --
# scoped to the comparison table only. Read from core.extract.MODEL_ATTRIBUTES
# so extraction stays the single source of truth for which GDTF names these
# are.
_MODEL_DIMENSION_ATTRIBUTES = frozenset(spec[0] for spec in MODEL_ATTRIBUTES)


def beam_position_label(position: int) -> str:
    """Return the row label a beam at a 1-based position gets in a cross-file comparison.

    Parameters:
        position: The beam's 1-based position within its file (geometry
            document order).

    Returns:
        BEAM_POSITION_LABEL_TEMPLATE formatted with that position.
    """
    return BEAM_POSITION_LABEL_TEMPLATE.format(position=position)


def _cross_file_attributes(model: FixtureModel) -> Dict[AttributeKey, AttributeValue]:
    """Return the per-file view compare() lines rows up with (G-03-3).

    Within one file, two beams still get two distinct positions (Phase 01
    D-11 non-collision preserved); across files, the manufacturer-chosen
    geometry and model names no longer decide which values share a row. A
    file with fewer beams simply has no key at the missing position, which
    compare() reports as None ("N/A"). Dimension values stay on
    FixtureModel.attributes untouched -- only the cross-file comparison
    omits them.

    Parameters:
        model: The FixtureModel to build a cross-file view for.

    Returns:
        A new dict (model.attributes is never mutated, and model itself is
        never replaced): per-model dimension keys omitted; Beam keys re-keyed
        by position (beam_position_label), assigned in first-seen order
        (geometry document order, since core.extract.extract_attributes
        inserts beams in iter_geometry_paths order); every other key passes
        through unchanged.
    """
    cross_file_attributes: Dict[AttributeKey, AttributeValue] = {}
    beam_positions: Dict[str, int] = {}

    for key, value in model.attributes.items():
        if (
            key.category == CATEGORY_PHYSICAL
            and key.element_path != FIXTURE_LEVEL_PATH
            and key.attribute in _MODEL_DIMENSION_ATTRIBUTES
        ):
            continue

        if key.category == CATEGORY_BEAM:
            if key.element_path not in beam_positions:
                beam_positions[key.element_path] = len(beam_positions) + 1
            position = beam_positions[key.element_path]
            cross_file_key = AttributeKey(
                CATEGORY_BEAM, beam_position_label(position), key.attribute
            )
            cross_file_attributes[cross_file_key] = value
            continue

        cross_file_attributes[key] = value

    return cross_file_attributes


def compare(target: FixtureModel, comparisons: Sequence[FixtureModel]) -> ComparisonResult:
    """Compare a target fixture against one or more comparison fixtures.

    Parameters:
        target: The target FixtureModel.
        comparisons: The comparison FixtureModels, in display order.

    Returns:
        A ComparisonResult whose rows cover every cross-file row key (each
        model's _cross_file_attributes view), first-seen order, no
        duplicates; Beam then Physical Properties first (LEADING_CATEGORIES),
        then every other category in first-seen order. Beam rows are
        labelled "Beam 1", "Beam 2", ... by position, per-model dimension
        rows are omitted, and everything else is keyed exactly as extracted
        -- rows are matched by position rather than by each file's own
        element names because different manufacturers almost never reuse the
        same names (03-UAT.md G-03-3). compare() never filters by category --
        the GUI decides what is shown (ATTR-01, ATTR-02); this stays a pure,
        selection-unaware function.
    """
    target_view = _cross_file_attributes(target)
    comparison_views = [_cross_file_attributes(model) for model in comparisons]

    ordered_keys = []
    seen = set()
    first_seen_index = {}
    for view in (target_view, *comparison_views):
        for key in view:
            if key in seen:
                continue
            seen.add(key)
            ordered_keys.append(key)
            if key.category not in first_seen_index:
                first_seen_index[key.category] = len(first_seen_index)

    def _sort_key(key):
        if key.category in LEADING_CATEGORIES:
            return (0, LEADING_CATEGORIES.index(key.category))
        return (1, first_seen_index[key.category])

    # list.sort() is stable, so this only reorders by category while
    # preserving each key's first-seen relative order within that category.
    ordered_keys.sort(key=_sort_key)

    rows = []
    for key in ordered_keys:
        target_value = target_view.get(key)
        comparison_values = tuple(view.get(key) for view in comparison_views)
        differs = tuple(not values_equal(target_value, value) for value in comparison_values)
        rows.append(
            ComparisonRow(
                key=key,
                target_value=target_value,
                comparison_values=comparison_values,
                differs=differs,
            )
        )

    return ComparisonResult(target=target, comparisons=tuple(comparisons), rows=tuple(rows))


def compare_files(
    target_path: str,
    compare_paths: Sequence[str],
    repository: Optional[FixtureRepository] = None,
) -> ComparisonResult:
    """Load a target and comparison files and compare them (D-15 batch API).

    Parameters:
        target_path: Path to the target .gdtf file.
        compare_paths: Paths to the comparison .gdtf files, in order.
        repository: The FixtureRepository to load files with. Defaults to a
            new FixtureRepository() when None.

    Returns:
        A ComparisonResult covering the target and all comparison files.

    Any load error propagates unchanged -- this function never returns a
    partial result.
    """
    repo = repository or FixtureRepository()
    target = repo.load(target_path)
    comparisons = [repo.load(path) for path in compare_paths]
    return compare(target, comparisons)


def attribute_catalog(
    result: ComparisonResult,
) -> Tuple[Tuple[str, Tuple[str, ...]], ...]:
    """Return the picker's (category, attribute-names) catalog for a result.

    The selection unit for gui.attribute_picker.AttributePicker is
    (category, attribute), never a full AttributeKey (Research Pattern 2):
    a fixture with several geometry instances of the same beam still gets
    one "BeamAngle" checkbox, not one per element path. This function
    collapses result.rows down to that unit, one entry per distinct
    attribute name within each category.

    Parameters:
        result: The ComparisonResult to build a catalog for.

    Returns:
        One (category, attribute_names) pair per category present in
        result.rows, in the same category order as result.rows (Beam then
        Physical Properties first, then every other category in first-seen
        order -- see compare()). attribute_names lists each distinct
        attribute name within that category, in first-appearance order,
        deduplicated across every element path that declares it. An empty
        tuple when result.rows is empty.
    """
    categories: Dict[str, List[str]] = {}
    for row in result.rows:
        names = categories.setdefault(row.key.category, [])
        if row.key.attribute not in names:
            names.append(row.key.attribute)
    return tuple((category, tuple(names)) for category, names in categories.items())
