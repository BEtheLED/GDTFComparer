"""Pure comparison logic and the batch service API (D-13, D-15).

compare() is a pure function of already-loaded FixtureModels. compare_files()
is the one and only core service call the GUI makes (via gui/worker.py);
never gets called with a Qt import anywhere on this side (D-16).
"""

from typing import Dict, List, Optional, Sequence, Tuple

from gdtf_comparer.core.models import (
    LEADING_CATEGORIES,
    ComparisonResult,
    ComparisonRow,
    FixtureModel,
    values_equal,
)
from gdtf_comparer.core.repository import FixtureRepository


def compare(target: FixtureModel, comparisons: Sequence[FixtureModel]) -> ComparisonResult:
    """Compare a target fixture against one or more comparison fixtures.

    Parameters:
        target: The target FixtureModel.
        comparisons: The comparison FixtureModels, in display order.

    Returns:
        A ComparisonResult whose rows cover every key present on the target
        or any comparison, first-seen order, no duplicates; Beam then
        Physical Properties first (LEADING_CATEGORIES), then every other
        category in first-seen order. compare() never filters by category --
        the GUI decides what is shown (ATTR-01, ATTR-02); this stays a pure,
        selection-unaware function.
    """
    ordered_keys = []
    seen = set()
    first_seen_index = {}
    for model in (target, *comparisons):
        for key in model.attributes:
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
        target_value = target.attributes.get(key)
        comparison_values = tuple(model.attributes.get(key) for model in comparisons)
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
