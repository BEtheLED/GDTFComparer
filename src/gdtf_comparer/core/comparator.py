"""Pure comparison logic and the batch service API (D-13, D-15).

compare() is a pure function of already-loaded FixtureModels. compare_files()
is the one and only core service call the GUI makes (via gui/worker.py);
never gets called with a Qt import anywhere on this side (D-16).
"""

from typing import Optional, Sequence

from gdtf_comparer.core.models import (
    DISPLAY_CATEGORIES,
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
        or any comparison (first-seen order, no duplicates) whose category
        is one of DISPLAY_CATEGORIES (D-10), stable-sorted by category.
    """
    ordered_keys = []
    seen = set()
    for model in (target, *comparisons):
        for key in model.attributes:
            if key.category not in DISPLAY_CATEGORIES:
                continue
            if key in seen:
                continue
            seen.add(key)
            ordered_keys.append(key)

    # list.sort() is stable, so this only reorders by category while
    # preserving each key's first-seen relative order within that category.
    ordered_keys.sort(key=lambda k: DISPLAY_CATEGORIES.index(k.category))

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
