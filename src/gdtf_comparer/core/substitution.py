"""Pure fixture-substitution scoring, keyed by AttributeKey (SUB-02, SUB-04, D-04..D-06, D-10..D-12).

A pure, Qt-free variant of core.comparator's value comparison: given a target
fixture's marked requirements and a candidate fixture, decide green/yellow/red
per requirement and rank candidates. This module has zero Qt imports and
never touches disk (D-16).
"""

import math
import os
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Optional, Tuple

from gdtf_comparer.core.comparator import compare
from gdtf_comparer.core.errors import CandidateFolderError, GDTFError
from gdtf_comparer.core.models import AttributeKey, AttributeValue, FixtureModel, format_value, values_equal
from gdtf_comparer.core.repository import FixtureRepository


class Direction(str, Enum):
    """How a candidate's value compares to the target's for one requirement."""

    HIGHER = "higher"
    LOWER = "lower"
    CLOSEST = "closest"
    EXACT = "exact"


DIRECTION_LABELS = {
    Direction.HIGHER: "Higher is better",
    Direction.LOWER: "Lower is better",
    Direction.CLOSEST: "Closest to target",
    Direction.EXACT: "Must match",
}

NUMERIC_DIRECTIONS = (Direction.HIGHER, Direction.LOWER, Direction.CLOSEST)


class MatchState(str, Enum):
    """A candidate's color for one requirement."""

    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


# Task 2 decision (D-08, D-10): option a -- "Tolerance is the 'might still
# work' limit, typed in the attribute's own units." The tolerance always
# means "anything worse than this, by this much, is red." For Direction.
# CLOSEST, green is within half the tolerance and yellow is within the full
# tolerance either side of the target.
TOLERANCE_KIND = "absolute"
CLOSEST_GREEN_FACTOR = 0.5
CLOSEST_YELLOW_FACTOR = 1.0


@dataclass(frozen=True)
class Requirement:
    """One marked attribute: the target value, how it's compared and by how much.

    Parameters:
        key: The AttributeKey this requirement is about.
        target: The target fixture's value for this attribute.
        direction: How a candidate's value compares to target.
        tolerance: How far off a candidate may be and still be green/yellow
            (meaning depends on direction and TOLERANCE_KIND).
    """

    key: AttributeKey
    target: AttributeValue
    direction: Direction
    tolerance: float


@dataclass(frozen=True)
class RequirementSet:
    """A fixture type's full set of marked requirements (SUB-02, D-06).

    Parameters:
        fixture_name: The fixture's display name.
        manufacturer: The fixture's manufacturer name.
        gdtf_file: The GDTF file name this fixture type was loaded from.
        requirements: The marked Requirements, in marking order.
    """

    fixture_name: str
    manufacturer: str
    gdtf_file: str
    requirements: Tuple[Requirement, ...]


def requirement_options(fixture: FixtureModel) -> Tuple[Tuple[AttributeKey, AttributeValue], ...]:
    """Return the (key, value) pairs a requirements editor may offer for fixture.

    Parameters:
        fixture: The FixtureModel to list eligible attributes for.

    Returns:
        One (key, value) pair per row of compare(fixture, ()) whose
        target_value is not None (RESEARCH Pitfall 6: only declared values
        qualify), in compare()'s order -- the same order the comparison
        table and Attributes panel use.
    """
    return tuple(
        (row.key, row.target_value) for row in compare(fixture, ()).rows if row.target_value is not None
    )


def default_direction(key: AttributeKey, value: AttributeValue) -> Direction:
    """Return the default Direction for a newly-marked requirement.

    Parameters:
        key: The AttributeKey being marked (unused by this default; kept for
            a future per-attribute table, Plan 05-03 D-05).
        value: The target fixture's value for key.

    Returns:
        Direction.EXACT for a str value, else Direction.CLOSEST.
    """
    if isinstance(value, str):
        return Direction.EXACT
    return Direction.CLOSEST


def default_tolerance(key: AttributeKey, value: AttributeValue, direction: Direction) -> float:
    """Return the default tolerance for a newly-marked requirement.

    Parameters:
        key: The AttributeKey being marked (unused by this default).
        value: The target fixture's value for key.
        direction: The requirement's direction.

    Returns:
        0.0 for Direction.EXACT; 10.0 when TOLERANCE_KIND == "percent";
        otherwise 10% of abs(value), rounded to 3 decimal places.
    """
    if direction == Direction.EXACT:
        return 0.0
    if TOLERANCE_KIND == "percent":
        return 10.0
    return round(abs(float(value)) * 0.10, 3)


def _at_most(a: float, b: float) -> bool:
    """Return True if a <= b, or a and b are close enough to count as equal.

    A value exactly on a boundary therefore always takes the better color.
    """
    return a <= b or math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12)


def _tolerance_amount(requirement: Requirement) -> float:
    """Return a requirement's tolerance converted to the target's own units."""
    if TOLERANCE_KIND == "percent":
        return abs(float(requirement.target)) * requirement.tolerance / 100
    return requirement.tolerance


def score_value(requirement: Requirement, candidate_value: AttributeValue) -> MatchState:
    """Score one candidate value against one requirement (SUB-02, D-10).

    Parameters:
        requirement: The Requirement to score against.
        candidate_value: The candidate fixture's value for requirement.key.

    Returns:
        MatchState.RED when candidate_value is None (not listed). For
        Direction.EXACT, GREEN when values_equal to the target, else RED.
        For a numeric direction with a non-numeric value on either side,
        RED. Otherwise: HIGHER/LOWER compute a shortfall (how much worse the
        candidate is than the target) and are GREEN when the shortfall is at
        most 0, YELLOW when at most the tolerance amount, else RED. CLOSEST
        computes the absolute distance from the target and is GREEN within
        CLOSEST_GREEN_FACTOR of the tolerance amount, YELLOW within
        CLOSEST_YELLOW_FACTOR, else RED.
    """
    if candidate_value is None:
        return MatchState.RED

    if requirement.direction == Direction.EXACT:
        return MatchState.GREEN if values_equal(candidate_value, requirement.target) else MatchState.RED

    if not isinstance(candidate_value, (int, float)) or not isinstance(requirement.target, (int, float)):
        return MatchState.RED

    target = float(requirement.target)
    candidate = float(candidate_value)
    amount = _tolerance_amount(requirement)

    if requirement.direction == Direction.HIGHER:
        shortfall = target - candidate
    elif requirement.direction == Direction.LOWER:
        shortfall = candidate - target
    else:
        shortfall = None

    if shortfall is not None:
        if _at_most(shortfall, 0.0):
            return MatchState.GREEN
        if _at_most(shortfall, amount):
            return MatchState.YELLOW
        return MatchState.RED

    distance = abs(candidate - target)
    if _at_most(distance, amount * CLOSEST_GREEN_FACTOR):
        return MatchState.GREEN
    if _at_most(distance, amount * CLOSEST_YELLOW_FACTOR):
        return MatchState.YELLOW
    return MatchState.RED


@dataclass(frozen=True)
class CandidateScore:
    """One candidate fixture's scored values against a RequirementSet.

    Parameters:
        candidate: The scored FixtureModel.
        values: The candidate's value for each requirement, in
            RequirementSet.requirements order.
        states: The MatchState for each requirement, in the same order.
    """

    candidate: FixtureModel
    values: tuple
    states: tuple

    @property
    def green_count(self) -> int:
        """Return how many requirements scored GREEN."""
        return sum(1 for state in self.states if state == MatchState.GREEN)

    @property
    def yellow_count(self) -> int:
        """Return how many requirements scored YELLOW."""
        return sum(1 for state in self.states if state == MatchState.YELLOW)

    @property
    def red_count(self) -> int:
        """Return how many requirements scored RED."""
        return sum(1 for state in self.states if state == MatchState.RED)


def score_candidate(requirement_set: RequirementSet, candidate: FixtureModel) -> CandidateScore:
    """Score one candidate fixture against every requirement in requirement_set.

    Parameters:
        requirement_set: The requirements to score against.
        candidate: The candidate FixtureModel to score.

    Returns:
        A CandidateScore built from the candidate's own compare(candidate,
        ()) cross-file view, so beam positions line up the same way the
        comparison table does.
    """
    candidate_view = {row.key: row.target_value for row in compare(candidate, ()).rows}
    values = tuple(candidate_view.get(requirement.key) for requirement in requirement_set.requirements)
    states = tuple(
        score_value(requirement, value) for requirement, value in zip(requirement_set.requirements, values)
    )
    return CandidateScore(candidate=candidate, values=values, states=states)


def rank(scores: Iterable[CandidateScore]) -> Tuple[CandidateScore, ...]:
    """Sort candidate scores best-first, deterministically (D-11).

    Parameters:
        scores: The CandidateScores to sort.

    Returns:
        scores sorted by (red_count, yellow_count, file name casefold, file
        name, source path) ascending -- fewest reds first, then fewest
        yellows, then file name.
    """
    return tuple(
        sorted(
            scores,
            key=lambda score: (
                score.red_count,
                score.yellow_count,
                score.candidate.file_name.casefold(),
                score.candidate.file_name,
                score.candidate.source_path,
            ),
        )
    )


@dataclass(frozen=True)
class CandidateFailure:
    """A candidate file that could not be loaded while scanning a folder.

    Parameters:
        path: Path to the file that failed to load.
        reason: The friendly user_message from the GDTFError it raised.
    """

    path: str
    reason: str


@dataclass(frozen=True)
class CandidateScan:
    """The result of scanning a folder of candidate GDTF files (SUB-04).

    Parameters:
        requirement_set: The requirements candidates were scored against.
        folder: The scanned folder path.
        ranked: The successfully scored candidates, best first (rank()).
        failures: The candidate files that could not be loaded.
    """

    requirement_set: RequirementSet
    folder: str
    ranked: tuple
    failures: tuple


def scan_candidate_folder(
    folder: str, requirement_set: RequirementSet, repository: Optional[FixtureRepository] = None
) -> CandidateScan:
    """Scan a folder of .gdtf files and rank them against requirement_set (SUB-04).

    Parameters:
        folder: Path to the folder to scan.
        requirement_set: The requirements to score each candidate against.
        repository: The FixtureRepository to load candidates with. Defaults
            to a new FixtureRepository() when None.

    Returns:
        A CandidateScan with no work done (empty ranked/failures) when
        requirement_set has no requirements. Otherwise every *.gdtf file in
        folder (case-insensitive extension match, sorted by casefolded then
        plain name), scored and ranked, with any file that failed to load
        recorded as a CandidateFailure instead of stopping the whole scan.

    Raises:
        CandidateFolderError: folder could not be listed.
    """
    if not requirement_set.requirements:
        return CandidateScan(requirement_set, folder, (), ())

    try:
        names = os.listdir(folder)
    except OSError as exc:
        raise CandidateFolderError(
            f"Could not read the inventory folder '{folder}' ({exc.strerror})."
        ) from exc

    gdtf_names = sorted(
        (name for name in names if name.casefold().endswith(".gdtf")),
        key=lambda name: (name.casefold(), name),
    )

    repo = repository or FixtureRepository()
    scores = []
    failures = []
    for name in gdtf_names:
        path = os.path.join(folder, name)
        try:
            candidate = repo.load(path)
        except GDTFError as exc:
            failures.append(CandidateFailure(path, exc.user_message))
            continue
        scores.append(score_candidate(requirement_set, candidate))

    return CandidateScan(requirement_set, folder, rank(scores), tuple(failures))


def scan_summary_message(scan: CandidateScan) -> str:
    """Return a friendly one-line summary of a CandidateScan.

    Parameters:
        scan: The CandidateScan to summarize.

    Returns:
        A message describing how many candidates were checked against how
        many requirements, or why nothing was checked.
    """
    if not scan.requirement_set.requirements:
        return "This requirements file has no attributes marked important, so there is nothing to check."
    if not scan.ranked and not scan.failures:
        return f"No GDTF files were found in '{scan.folder}'."

    message = (
        f"Checked {len(scan.ranked)} candidate(s) against "
        f"{len(scan.requirement_set.requirements)} requirement(s) for "
        f"'{scan.requirement_set.fixture_name}'."
    )
    if scan.failures:
        message += f" {len(scan.failures)} file(s) could not be read."
    return message


def describe_requirements(requirement_set: RequirementSet) -> str:
    """Return a friendly one-line description of a RequirementSet.

    Parameters:
        requirement_set: The RequirementSet to describe.

    Returns:
        "{name} ({manufacturer}) — {k} requirement(s): attr1 value1
        (direction1), ..." -- just the name when manufacturer is blank.
    """
    if requirement_set.manufacturer.strip():
        heading = f"{requirement_set.fixture_name} ({requirement_set.manufacturer})"
    else:
        heading = requirement_set.fixture_name

    items = ", ".join(
        f"{requirement.key.attribute} {format_value(requirement.target)} "
        f"({DIRECTION_LABELS[requirement.direction].lower()})"
        for requirement in requirement_set.requirements
    )
    return f"{heading} — {len(requirement_set.requirements)} requirement(s): {items}"
