"""Tests for gdtf_comparer.core.models: ComparisonRow.any_differs (IN-01).

any_differs is kept as intended future surface for Phase 2 diff
highlighting (DIFF-01) and Phase 3 diff-only export (EXPORT-02); this
module exercises it so it is not untested dead code.
"""

from gdtf_comparer.core.models import CATEGORY_BEAM, AttributeKey, ComparisonRow

KEY = AttributeKey(CATEGORY_BEAM, "Head/Beam", "BeamAngle")


def test_any_differs_true_when_any_comparison_differs():
    row = ComparisonRow(
        key=KEY,
        target_value=25.0,
        comparison_values=(25.0, 30.0),
        differs=(False, True),
    )
    assert row.any_differs is True


def test_any_differs_false_when_all_match():
    row = ComparisonRow(
        key=KEY,
        target_value=25.0,
        comparison_values=(25.0, 25.0),
        differs=(False, False),
    )
    assert row.any_differs is False


def test_any_differs_false_without_comparisons():
    row = ComparisonRow(
        key=KEY,
        target_value=25.0,
        comparison_values=(),
        differs=(),
    )
    assert row.any_differs is False
