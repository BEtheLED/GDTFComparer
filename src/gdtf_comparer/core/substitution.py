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
from typing import Iterable, Mapping, Optional, Tuple

from gdtf_comparer.core.comparator import compare
from gdtf_comparer.core.errors import CandidateFolderError, GDTFError
from gdtf_comparer.core.models import (
    CATEGORY_BEAM,
    CATEGORY_PHYSICAL,
    AttributeKey,
    AttributeValue,
    FixtureModel,
    format_value,
    values_equal,
)
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


# D-05 defaults table (RESEARCH A1, A2): a per-attribute sensible starting
# direction, keyed by bare GDTF attribute name, only consulted for the two
# legacy categories (Beam, Physical Properties) -- a DMX attribute
# definition literally named "Weight" never borrows this table (its value is
# always text, so default_direction's str check already routes it to EXACT
# first). Every default is overridable per attribute in the editor; a
# wrong-feeling default costs the LD one click, never a blocked workflow.
DEFAULT_DIRECTIONS: Mapping[str, Direction] = {
    "Weight": Direction.LOWER,
    "PowerConsumption": Direction.LOWER,
    "LuminousFlux": Direction.HIGHER,
    "BeamAngle": Direction.CLOSEST,
    "FieldAngle": Direction.CLOSEST,
    "ColorTemperature": Direction.CLOSEST,
}

# Display-only units (never change a stored number) for the Beam and
# Physical Properties numeric attributes GDTF reports in these units.
ATTRIBUTE_UNITS: Mapping[str, str] = {
    "Weight": "kg",
    "BeamAngle": "°",
    "FieldAngle": "°",
    "PowerConsumption": "W",
    "LuminousFlux": "lm",
    "ColorTemperature": "K",
}


def attribute_unit(key: AttributeKey) -> str:
    """Return the display unit for key, or "" when it has none.

    Parameters:
        key: The AttributeKey to look up a unit for.

    Returns:
        ATTRIBUTE_UNITS.get(key.attribute, "") when key.category is
        CATEGORY_BEAM or CATEGORY_PHYSICAL, else "" -- a DMX attribute
        definition or an unknown numeric attribute never gets a unit
        guessed for it.
    """
    if key.category not in (CATEGORY_BEAM, CATEGORY_PHYSICAL):
        return ""
    return ATTRIBUTE_UNITS.get(key.attribute, "")


def default_direction(key: AttributeKey, value: AttributeValue) -> Direction:
    """Return the default Direction for a newly-marked requirement (D-05).

    Parameters:
        key: The AttributeKey being marked.
        value: The target fixture's value for key.

    Returns:
        Direction.EXACT for a str value (checked before any name lookup, so
        a DMX attribute definition literally named "Weight" is never routed
        to the numeric table below); else, when key.category is
        CATEGORY_BEAM or CATEGORY_PHYSICAL and key.attribute is in
        DEFAULT_DIRECTIONS, that table's direction; else Direction.CLOSEST.
    """
    if isinstance(value, str):
        return Direction.EXACT
    if key.category in (CATEGORY_BEAM, CATEGORY_PHYSICAL) and key.attribute in DEFAULT_DIRECTIONS:
        return DEFAULT_DIRECTIONS[key.attribute]
    return Direction.CLOSEST


def default_tolerance(key: AttributeKey, value: AttributeValue, direction: Direction) -> float:
    """Return the default tolerance for a newly-marked requirement (D-06).

    Every marked attribute gets its own tolerance, starting at 10% of the
    target's own value (absolute mode) or a flat 10% (percent mode) -- never
    one global tolerance shared across attributes. The LD can retype it per
    attribute in the editor.

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


def rank_key(score: CandidateScore) -> tuple:
    """Return rank()'s sort key for score (D-11, SUB-04 fairness prohibition).

    Parameters:
        score: The CandidateScore to build a sort key for.

    Returns:
        (red_count, yellow_count, file name casefold, file name, source
        path) -- fewest reds first, then fewest yellows, then file name
        (case-insensitive, then exact spelling, then full path) as the
        final deterministic tie-break. No other field (manufacturer, file
        date, folder-listing order) may ever enter this key: two shops
        scanning the same folder on different operating systems or with
        different file dates must always see the same order.
    """
    return (
        score.red_count,
        score.yellow_count,
        score.candidate.file_name.casefold(),
        score.candidate.file_name,
        score.candidate.source_path,
    )


def rank(scores: Iterable[CandidateScore]) -> Tuple[CandidateScore, ...]:
    """Sort candidate scores best-first, deterministically (D-11).

    Parameters:
        scores: The CandidateScores to sort.

    Returns:
        scores sorted by rank_key ascending -- fewest reds first, then
        fewest yellows, then file name.
    """
    return tuple(sorted(scores, key=rank_key))


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
    """Scan a folder of .gdtf files and rank them against requirement_set (SUB-04, D-12).

    Looks only at folder itself, never a subfolder (a single, non-recursive
    directory listing): "Check Inventory" scans the one folder the shop
    pointed at. Every entry whose name ends in ".gdtf" in any letter case is kept; every
    other entry (another extension, a subfolder, a file with no extension)
    is ignored. Checking inventory is strictly read-only -- this function
    never opens anything for writing, never renames and never creates
    anything in folder (SUB-04 safety prohibition).

    Parameters:
        folder: Path to the folder to scan.
        requirement_set: The requirements to score each candidate against.
        repository: The FixtureRepository to load candidates with. Defaults
            to a new FixtureRepository() when None.

    Returns:
        A CandidateScan with no work done (empty ranked/failures, and no
        inventory file ever opened) when requirement_set has no
        requirements. Otherwise every *.gdtf file in folder (case-insensitive
        extension match, sorted by casefolded then plain name -- never by
        file date or the operating system's own listing order), scored and
        ranked. Duplicate fixtures (byte-identical copies, or two files
        describing the same manufacturer/model/mode) are never merged: a
        shop can own several units of one fixture, so every readable file
        becomes its own row. A file that failed to load (not a valid GDTF
        archive, or not a regular file -- a folder, pipe or device named
        *.gdtf, caught by core.hardening's regular-file check) is recorded
        as a CandidateFailure instead of stopping the whole scan.

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


def _count(n: int, singular: str, plural: str) -> str:
    """Return "{n} {singular}" or "{n} {plural}" per standard English pluralization.

    A private helper, mirroring core.mvr_repository._count's shape exactly
    -- defined separately here rather than imported, since neither module
    exposes private helpers across module boundaries.
    """
    return f"{n} {singular if n == 1 else plural}"


NO_REQUIREMENTS_MESSAGE = "This requirements file has no attributes marked important, so there is nothing to check."
NO_GDTF_FILES_TEMPLATE = "No GDTF files were found in '{folder}'."
NONE_READABLE_TEMPLATE = "None of the {count} GDTF files in '{folder}' could be read."
CHECKED_TEMPLATE = "Checked {candidates} against {requirements} for '{fixture}'."
UNREADABLE_SUFFIX_TEMPLATE = " {count} could not be read and {verb} listed at the bottom."


def scan_summary_message(scan: CandidateScan) -> str:
    """Return a friendly one-line summary of a CandidateScan.

    Parameters:
        scan: The CandidateScan to summarize.

    Returns:
        NO_REQUIREMENTS_MESSAGE when requirement_set has no requirements
        (SUB-02 empty edge, shop side); NO_GDTF_FILES_TEMPLATE when the
        folder held no *.gdtf file at all (SUB-04 empty edge);
        NONE_READABLE_TEMPLATE when every *.gdtf file found failed to load;
        otherwise CHECKED_TEMPLATE naming how many candidates were checked
        against how many requirements, with an UNREADABLE_SUFFIX_TEMPLATE
        clause appended when any file failed to load (prohibition: a failed
        file is always named, never silently dropped from the count).
    """
    if not scan.requirement_set.requirements:
        return NO_REQUIREMENTS_MESSAGE
    if not scan.ranked and not scan.failures:
        return NO_GDTF_FILES_TEMPLATE.format(folder=scan.folder)
    if not scan.ranked:
        return NONE_READABLE_TEMPLATE.format(count=len(scan.failures), folder=scan.folder)

    message = CHECKED_TEMPLATE.format(
        candidates=_count(len(scan.ranked), "candidate", "candidates"),
        requirements=_count(len(scan.requirement_set.requirements), "requirement", "requirements"),
        fixture=scan.requirement_set.fixture_name,
    )
    if scan.failures:
        count = len(scan.failures)
        message += UNREADABLE_SUFFIX_TEMPLATE.format(
            count=count, verb="is" if count == 1 else "are"
        )
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
