"""Final scan rules, scoring edges and ranking fairness for Check Inventory
(SUB-02, SUB-04, D-10, D-11, D-12).
"""

import os
import shutil
from pathlib import Path

import pytest

from gdtf_comparer.core.errors import CandidateFolderError
from gdtf_comparer.core.models import CATEGORY_PHYSICAL, AttributeKey
from gdtf_comparer.core.repository import FixtureRepository
from gdtf_comparer.core.substitution import (
    NO_GDTF_FILES_TEMPLATE,
    NO_REQUIREMENTS_MESSAGE,
    NONE_READABLE_TEMPLATE,
    Direction,
    Requirement,
    RequirementSet,
    scan_candidate_folder,
    scan_summary_message,
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
