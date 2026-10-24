"""Final scan rules, scoring edges and ranking fairness for Check Inventory
(SUB-02, SUB-04, D-10, D-11, D-12).
"""

import os
import shutil
import time
from pathlib import Path

import pytest

import gdtf_comparer.core.substitution as substitution_module
from gdtf_comparer.core.errors import CandidateFolderError
from gdtf_comparer.core.models import CATEGORY_BEAM, CATEGORY_PHYSICAL, AttributeKey, FixtureModel
from gdtf_comparer.core.repository import FixtureRepository
from gdtf_comparer.core.substitution import (
    CLOSEST_GREEN_FACTOR,
    CLOSEST_YELLOW_FACTOR,
    NO_GDTF_FILES_TEMPLATE,
    NO_REQUIREMENTS_MESSAGE,
    NONE_READABLE_TEMPLATE,
    TOLERANCE_KIND,
    Direction,
    MatchState,
    Requirement,
    RequirementSet,
    rank,
    scan_candidate_folder,
    scan_summary_message,
    score_candidate,
    score_value,
)

# Shared test data (per plan): _req builds one Requirement, _set builds the
# RequirementSet every scan test scores candidates against.
WEIGHT_TOLERANCE = 2.0


def _req(attribute, target, direction, tolerance, category=CATEGORY_PHYSICAL, element=""):
    return Requirement(
        key=AttributeKey(category, element, attribute),
        target=target,
        direction=direction,
        tolerance=tolerance,
    )


def _set(*reqs):
    return RequirementSet("Acme Spot", "Acme", "Acme@Spot.gdtf", tuple(reqs))


def _weight_requirements():
    return _set(_req("Weight", 15.0, Direction.LOWER, WEIGHT_TOLERANCE))


def _folder_snapshot(folder) -> dict:
    """Return {path: (bytes, mtime_ns)} for every file under folder, recursively."""
    snapshot = {}
    for root, _dirs, files in os.walk(folder):
        for name in files:
            path = os.path.join(root, name)
            snapshot[path] = (Path(path).read_bytes(), os.stat(path).st_mtime_ns)
    return snapshot


# --- Task 1: scan rules (D-12), summary wording, read-only, duplicates ---


def test_scans_only_gdtf_files_in_that_folder(tmp_path, make_gdtf):
    folder = tmp_path / "messy"
    folder.mkdir()
    (folder / "old").mkdir()
    make_gdtf("messy/Beta.gdtf", weight=14.0)
    make_gdtf("messy/Gamma.GDTF", weight=16.0)
    (folder / "notes.txt").write_text("not a gdtf")
    make_gdtf("messy/old/Delta.gdtf", weight=20.0)
    (folder / "Broken.gdtf").write_bytes(b"not a zip")

    scan = scan_candidate_folder(str(folder), _weight_requirements())

    ranked_names = {score.candidate.file_name for score in scan.ranked}
    assert ranked_names == {"Beta.gdtf", "Gamma.GDTF"}
    assert len(scan.failures) == 1
    assert os.path.basename(scan.failures[0].path) == "Broken.gdtf"
    assert "not a valid GDTF file" in scan.failures[0].reason


def test_folder_is_never_modified(tmp_path, make_gdtf):
    folder = tmp_path / "inventory"
    folder.mkdir()
    make_gdtf("inventory/Beta.gdtf", weight=14.0)
    (folder / "Broken.gdtf").write_bytes(b"not a zip")

    before = _folder_snapshot(folder)
    scan_candidate_folder(str(folder), _weight_requirements())
    after = _folder_snapshot(folder)

    assert before == after


def test_duplicates_are_not_merged(tmp_path, make_gdtf):
    folder = tmp_path / "inventory"
    folder.mkdir()
    beta = make_gdtf("inventory/Beta.gdtf", weight=14.0)
    shutil.copy(beta, folder / "Beta copy.gdtf")

    scan = scan_candidate_folder(str(folder), _weight_requirements())

    assert len(scan.ranked) == 2
    names = {score.candidate.file_name for score in scan.ranked}
    assert names == {"Beta.gdtf", "Beta copy.gdtf"}


def test_empty_folder(tmp_path):
    folder = tmp_path / "empty"
    folder.mkdir()

    scan = scan_candidate_folder(str(folder), _weight_requirements())

    assert scan.ranked == ()
    assert scan.failures == ()
    assert scan_summary_message(scan) == NO_GDTF_FILES_TEMPLATE.format(folder=str(folder))


def test_nothing_readable(tmp_path):
    folder = tmp_path / "broken"
    folder.mkdir()
    (folder / "A.gdtf").write_bytes(b"not a zip")
    (folder / "B.gdtf").write_bytes(b"also not a zip")

    scan = scan_candidate_folder(str(folder), _weight_requirements())

    assert scan.ranked == ()
    assert len(scan.failures) == 2
    assert scan_summary_message(scan) == NONE_READABLE_TEMPLATE.format(count=2, folder=str(folder))


def test_single_candidate(tmp_path, make_gdtf):
    folder = tmp_path / "inventory"
    folder.mkdir()
    make_gdtf("inventory/Beta.gdtf", weight=14.0)

    scan = scan_candidate_folder(str(folder), _weight_requirements())

    assert len(scan.ranked) == 1


def test_no_requirements_skips_scoring(tmp_path, monkeypatch):
    def _fail_if_called(self, path):
        raise AssertionError("FixtureRepository.load must not be called with no requirements")

    monkeypatch.setattr(FixtureRepository, "load", _fail_if_called)

    folder = tmp_path / "inventory"
    folder.mkdir()
    (folder / "Beta.gdtf").write_bytes(b"irrelevant -- never opened")

    scan = scan_candidate_folder(str(folder), _set())

    assert scan.ranked == ()
    assert scan.failures == ()
    assert scan_summary_message(scan) == NO_REQUIREMENTS_MESSAGE


def test_summary_wording(tmp_path, make_gdtf):
    folder = tmp_path / "inventory"
    folder.mkdir()
    make_gdtf("inventory/Beta.gdtf", weight=14.0)
    make_gdtf("inventory/Gamma.gdtf", weight=16.0)
    (folder / "Broken.gdtf").write_bytes(b"not a zip")

    scan = scan_candidate_folder(str(folder), _weight_requirements())

    assert scan_summary_message(scan) == (
        "Checked 2 candidates against 1 requirement for 'Acme Spot'. "
        "1 could not be read and is listed at the bottom."
    )


def test_unreadable_folder_raises_friendly_error(tmp_path):
    missing = tmp_path / "does-not-exist"

    with pytest.raises(CandidateFolderError) as exc_info:
        scan_candidate_folder(str(missing), _weight_requirements())

    assert str(missing) in str(exc_info.value)


# --- Task 2: VALIDATION -- scoring matches the user's chosen rule exactly ---


def _weight_fixture(source_path: str, weight: float) -> FixtureModel:
    key = AttributeKey(CATEGORY_PHYSICAL, "", "Weight")
    return FixtureModel(source_path=source_path, name=source_path, manufacturer="", attributes={key: weight})


def test_score_and_rank():
    """VALIDATION: Weight 14/16.5/20 against a lower-is-better 15 (tolerance 2) rank green, yellow, red."""
    requirement_set = _weight_requirements()
    low = _weight_fixture("/inventory/low.gdtf", 14.0)
    mid = _weight_fixture("/inventory/mid.gdtf", 16.5)
    high = _weight_fixture("/inventory/high.gdtf", 20.0)

    scores = [score_candidate(requirement_set, model) for model in (high, low, mid)]
    ranked = rank(scores)

    assert [score.candidate.file_name for score in ranked] == ["low.gdtf", "mid.gdtf", "high.gdtf"]
    assert ranked[0].states == (MatchState.GREEN,)
    assert ranked[1].states == (MatchState.YELLOW,)
    assert ranked[2].states == (MatchState.RED,)


def test_worked_examples_from_decision():
    """The exact numbers from the chosen option (a) in 05-01 Task 2's decision."""
    assert TOLERANCE_KIND == "absolute"
    assert CLOSEST_GREEN_FACTOR == 0.5
    assert CLOSEST_YELLOW_FACTOR == 1.0

    weight = _req("Weight", 15.0, Direction.LOWER, 2.0)
    assert score_value(weight, 14.0) == MatchState.GREEN
    assert score_value(weight, 16.5) == MatchState.YELLOW
    assert score_value(weight, 17.5) == MatchState.RED

    beam = _req("BeamAngle", 20.0, Direction.CLOSEST, 4.0, category=CATEGORY_BEAM, element="Beam 1")
    assert score_value(beam, 21.5) == MatchState.GREEN
    assert score_value(beam, 23.5) == MatchState.YELLOW
    assert score_value(beam, 25.0) == MatchState.RED


def test_formula_for_each_option(monkeypatch):
    """Pin the arithmetic for all three Task 2 options, even the two not chosen."""
    # option a: TOLERANCE_KIND="absolute", CLOSEST_GREEN_FACTOR=0.5, CLOSEST_YELLOW_FACTOR=1.0 (chosen)
    monkeypatch.setattr(substitution_module, "TOLERANCE_KIND", "absolute")
    monkeypatch.setattr(substitution_module, "CLOSEST_GREEN_FACTOR", 0.5)
    monkeypatch.setattr(substitution_module, "CLOSEST_YELLOW_FACTOR", 1.0)
    weight_a = _req("Weight", 15.0, Direction.LOWER, 2.0)
    assert score_value(weight_a, 14.0) == MatchState.GREEN
    assert score_value(weight_a, 16.5) == MatchState.YELLOW
    assert score_value(weight_a, 17.5) == MatchState.RED
    beam_a = _req("BeamAngle", 20.0, Direction.CLOSEST, 4.0, category=CATEGORY_BEAM, element="Beam 1")
    assert score_value(beam_a, 21.5) == MatchState.GREEN
    assert score_value(beam_a, 23.5) == MatchState.YELLOW
    assert score_value(beam_a, 25.0) == MatchState.RED

    # option b: TOLERANCE_KIND="absolute", CLOSEST_GREEN_FACTOR=1.0, CLOSEST_YELLOW_FACTOR=2.0
    monkeypatch.setattr(substitution_module, "TOLERANCE_KIND", "absolute")
    monkeypatch.setattr(substitution_module, "CLOSEST_GREEN_FACTOR", 1.0)
    monkeypatch.setattr(substitution_module, "CLOSEST_YELLOW_FACTOR", 2.0)
    beam_b = _req("BeamAngle", 20.0, Direction.CLOSEST, 2.0, category=CATEGORY_BEAM, element="Beam 1")
    assert score_value(beam_b, 21.5) == MatchState.GREEN
    assert score_value(beam_b, 23.5) == MatchState.YELLOW
    assert score_value(beam_b, 25.0) == MatchState.RED

    # option c: TOLERANCE_KIND="percent", CLOSEST_GREEN_FACTOR=0.5, CLOSEST_YELLOW_FACTOR=1.0
    monkeypatch.setattr(substitution_module, "TOLERANCE_KIND", "percent")
    monkeypatch.setattr(substitution_module, "CLOSEST_GREEN_FACTOR", 0.5)
    monkeypatch.setattr(substitution_module, "CLOSEST_YELLOW_FACTOR", 1.0)
    weight_c = _req("Weight", 15.0, Direction.LOWER, 10.0)
    assert score_value(weight_c, 14.0) == MatchState.GREEN
    assert score_value(weight_c, 16.2) == MatchState.YELLOW
    assert score_value(weight_c, 17.0) == MatchState.RED


def test_boundaries_take_better_color():
    """A value exactly on a boundary always takes the better color (every option shares this rule)."""
    closest = _req("BeamAngle", 20.0, Direction.CLOSEST, 4.0, category=CATEGORY_BEAM, element="Beam 1")
    assert score_value(closest, 20.0) == MatchState.GREEN  # exactly target
    assert score_value(closest, 22.0) == MatchState.GREEN  # exactly target + the green edge (2)
    assert score_value(closest, 18.0) == MatchState.GREEN  # exactly target - the green edge (2)
    assert score_value(closest, 24.0) == MatchState.YELLOW  # exactly the yellow edge (+4)
    assert score_value(closest, 16.0) == MatchState.YELLOW  # exactly the yellow edge (-4)

    # Float noise on a boundary still counts as on the boundary.
    noisy = _req("PowerConsumption", 0.3, Direction.HIGHER, 0.01)
    assert score_value(noisy, 0.1 + 0.2) == MatchState.GREEN


def test_zero_tolerance():
    higher = _req("LuminousFlux", 1000.0, Direction.HIGHER, 0.0)
    assert score_value(higher, 1000.0) == MatchState.GREEN
    assert score_value(higher, 900.0) == MatchState.RED
    assert score_value(higher, 1100.0) == MatchState.GREEN

    closest = _req("BeamAngle", 20.0, Direction.CLOSEST, 0.0, category=CATEGORY_BEAM, element="Beam 1")
    assert score_value(closest, 20.0) == MatchState.GREEN
    assert score_value(closest, 20.1) == MatchState.RED
    assert score_value(closest, 19.9) == MatchState.RED


def test_negative_values(monkeypatch):
    """Percent amounts are taken of the size of the target, proven with a negative target."""
    monkeypatch.setattr(substitution_module, "TOLERANCE_KIND", "absolute")
    req_absolute = _req("PowerConsumption", -10.0, Direction.HIGHER, 2.0)
    assert score_value(req_absolute, -9.0) == MatchState.GREEN
    assert score_value(req_absolute, -11.5) == MatchState.YELLOW
    assert score_value(req_absolute, -13.0) == MatchState.RED

    monkeypatch.setattr(substitution_module, "TOLERANCE_KIND", "percent")
    req_percent = _req("PowerConsumption", -10.0, Direction.HIGHER, 20.0)
    assert score_value(req_percent, -9.0) == MatchState.GREEN
    assert score_value(req_percent, -11.5) == MatchState.YELLOW
    assert score_value(req_percent, -13.0) == MatchState.RED


def test_missing_and_mismatched_values_are_red():
    for direction in (Direction.HIGHER, Direction.LOWER, Direction.CLOSEST, Direction.EXACT):
        req = _req("Weight", 15.0, direction, 2.0)
        assert score_value(req, None) == MatchState.RED

    numeric_req = _req("Weight", 15.0, Direction.HIGHER, 2.0)
    assert score_value(numeric_req, "fifteen") == MatchState.RED

    exact_req = _req("BeamType", "Spot", Direction.EXACT, 0.0)
    assert score_value(exact_req, "Wash") == MatchState.RED
    assert score_value(exact_req, "Spot") == MatchState.GREEN

    numeric_exact_req = _req("Weight", 3.0, Direction.EXACT, 0.0)
    assert score_value(numeric_exact_req, 3) == MatchState.GREEN


def test_beams_match_by_position(make_gdtf):
    """A requirement keyed "Beam 1" scores against the candidate's own 1st beam, by position."""
    candidate_path = make_gdtf(
        "candidate.gdtf",
        geometries_xml='<Geometry Name="Head"><Beam Name="Lens" BeamAngle="20" FieldAngle="25"/></Geometry>',
    )
    candidate = FixtureRepository().load(str(candidate_path))

    requirement_set = _set(
        _req("BeamAngle", 20.0, Direction.CLOSEST, 4.0, category=CATEGORY_BEAM, element="Beam 1")
    )
    score = score_candidate(requirement_set, candidate)

    assert score.values == (20.0,)
    assert score.states == (MatchState.GREEN,)


def test_ranking_ignores_everything_but_lights(tmp_path, make_gdtf, monkeypatch):
    """Ranking depends only on red/yellow counts plus the file-name tie-break (D-11, P10)."""
    folder = tmp_path / "inventory"
    folder.mkdir()

    make_gdtf("inventory/zeta.gdtf", name="Zeta", manufacturer="AAA", weight=20.0)
    make_gdtf("inventory/Alpha.gdtf", name="Alpha", manufacturer="ZZZ", weight=16.5)
    make_gdtf("inventory/beta.gdtf", name="Beta", manufacturer="MMM", weight=16.0)
    make_gdtf("inventory/Gamma.gdtf", name="Gamma", manufacturer="NNN", weight=14.0)

    requirement_set = _weight_requirements()
    expected_order = ["Gamma.gdtf", "Alpha.gdtf", "beta.gdtf", "zeta.gdtf"]

    scan = scan_candidate_folder(str(folder), requirement_set)
    assert [score.candidate.file_name for score in scan.ranked] == expected_order

    # Shuffling os.listdir's own order and reversing file mtimes must never
    # change the result -- only the lights and the file name may.
    real_listdir = os.listdir

    def _shuffled_listdir(path):
        return list(reversed(real_listdir(path)))

    monkeypatch.setattr(os, "listdir", _shuffled_listdir)

    now = time.time()
    for offset, name in enumerate(["zeta.gdtf", "Alpha.gdtf", "beta.gdtf", "Gamma.gdtf"]):
        mtime = now - offset
        os.utime(folder / name, (mtime, mtime))

    scan_again = scan_candidate_folder(str(folder), requirement_set)
    assert [score.candidate.file_name for score in scan_again.ranked] == expected_order

    monkeypatch.undo()

    # Two files differing only by letter case are ordered by exact file name
    # after the casefold tie -- skipped on a case-insensitive filesystem,
    # where writing both would resolve to the same underlying file.
    probe_folder = tmp_path / "case_probe"
    probe_folder.mkdir()
    (probe_folder / "probe.tmp").write_text("a")
    (probe_folder / "PROBE.tmp").write_text("b")
    if len(list(probe_folder.iterdir())) == 2:
        case_folder = tmp_path / "case_inventory"
        case_folder.mkdir()
        make_gdtf("case_inventory/same.gdtf", name="Same Lower", weight=14.0)
        make_gdtf("case_inventory/Same.gdtf", name="Same Upper", weight=14.0)

        case_scan = scan_candidate_folder(str(case_folder), requirement_set)
        assert [score.candidate.file_name for score in case_scan.ranked] == ["Same.gdtf", "same.gdtf"]
