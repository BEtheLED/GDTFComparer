"""Unit tests for core.requirements_repository: strict validation, safe
reads, hardened naming and atomic saves of the shareable fixture
requirements sidecar file (SUB-03, D-07..D-09).

A requirements file crosses the phase's main trust boundary (D-07): one
person saves it, a completely different person on a different computer
loads it. Every test here treats that boundary literally -- a round trip
through a real, separate Python process (test_round_trip_in_a_separate_
process), never coercing a file that isn't exactly understood.
"""

import json
import os
import subprocess
import sys
import unicodedata
from pathlib import Path

import pytest

from gdtf_comparer.core.errors import RequirementsFileError
from gdtf_comparer.core.models import AttributeKey
from gdtf_comparer.core.requirements_repository import (
    MAX_SUGGESTED_NAME_LENGTH,
    load_requirements,
    save_requirements,
    suggested_file_name,
)
from gdtf_comparer.core.substitution import Direction, Requirement, RequirementSet

SRC_PATH = Path(__file__).resolve().parents[2] / "src"


def _set(**overrides):
    """Build the shared test RequirementSet, overriding any field."""
    defaults = dict(
        fixture_name="Acme Spot",
        manufacturer="Acme",
        gdtf_file="Acme@Spot.gdtf",
        requirements=(
            Requirement(AttributeKey("Physical Properties", "", "Weight"), 15.0, Direction.LOWER, 2.0),
            Requirement(AttributeKey("Beam", "Beam 1", "BeamType"), "Spot", Direction.EXACT, 0.0),
        ),
    )
    defaults.update(overrides)
    return RequirementSet(**defaults)


def _payload(tmp_path, requirement_set=None, name="source.json"):
    """Save requirement_set (or _set()) and return its decoded JSON payload."""
    path = tmp_path / name
    save_requirements(str(path), requirement_set if requirement_set is not None else _set())
    return json.loads(path.read_text(encoding="utf-8"))


def test_round_trip_in_a_separate_process(tmp_path):
    """D-07: a file saved here loads identically in a completely separate process."""
    extra = Requirement(AttributeKey("Beam", "", "Zoom"), 0.1 + 0.2, Direction.CLOSEST, 1e-7)
    requirement_set = _set(
        fixture_name="Lumière Spot",
        requirements=_set().requirements + (extra,),
    )
    path = tmp_path / "Lumiere requirements.json"
    save_requirements(str(path), requirement_set)

    def _as_structure(rs):
        return [
            rs.fixture_name,
            rs.manufacturer,
            rs.gdtf_file,
            [
                [
                    requirement.key.category,
                    requirement.key.element_path,
                    requirement.key.attribute,
                    requirement.direction.value,
                    repr(requirement.target),
                    repr(requirement.tolerance),
                ]
                for requirement in rs.requirements
            ],
        ]

    expected = _as_structure(requirement_set)

    script = (
        "import json\n"
        "from gdtf_comparer.core.requirements_repository import load_requirements\n"
        f"rs = load_requirements({str(path)!r})\n"
        "print(json.dumps([rs.fixture_name, rs.manufacturer, rs.gdtf_file, "
        "[[r.key.category, r.key.element_path, r.key.attribute, r.direction.value, "
        "repr(r.target), repr(r.tolerance)] for r in rs.requirements]]))\n"
    )

    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC_PATH)
    env.pop("QT_QPA_PLATFORM", None)

    proc = subprocess.run(
        [sys.executable, "-c", script],
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert proc.returncode == 0, proc.stderr
    actual = json.loads(proc.stdout)
    assert actual == expected


def test_file_holds_exactly_one_fixture(tmp_path):
    """D-09: the saved JSON's key sets, at every level, are exactly these sets."""
    payload = _payload(tmp_path)

    assert set(payload.keys()) == {"format", "version", "tolerance_kind", "fixture", "requirements"}
    assert isinstance(payload["fixture"], dict)
    assert set(payload["fixture"].keys()) == {"name", "manufacturer", "gdtf_file"}
    assert isinstance(payload["requirements"], list)
    for requirement in payload["requirements"]:
        assert set(requirement.keys()) == {
            "category",
            "element",
            "attribute",
            "direction",
            "target",
            "tolerance",
        }

    def _walk(value):
        if isinstance(value, dict):
            for v in value.values():
                yield from _walk(v)
        elif isinstance(value, list):
            for v in value:
                yield from _walk(v)
        else:
            yield value

    for value in _walk(payload):
        if isinstance(value, str):
            assert (os.sep + "tmp") not in value


def test_saving_never_touches_an_mvr(tmp_path, make_mvr):
    """D-08: saving or loading a requirements file never opens, reads or changes an MVR file."""
    mvr_path = make_mvr("show.mvr")
    before_bytes = mvr_path.read_bytes()
    before_mtime_ns = mvr_path.stat().st_mtime_ns
    before_listing = sorted(os.listdir(tmp_path))

    req_path = tmp_path / "Acme Spot requirements.json"
    save_requirements(str(req_path), _set())
    load_requirements(str(req_path))

    assert mvr_path.read_bytes() == before_bytes
    assert mvr_path.stat().st_mtime_ns == before_mtime_ns
    assert sorted(os.listdir(tmp_path)) == sorted(before_listing + ["Acme Spot requirements.json"])


@pytest.mark.parametrize(
    "name, expectation",
    [
        ("Acme Spot", "Acme Spot requirements.json"),
        ("../../etc/passwd", None),
        ('a:b*c?d"e<f>g|h', None),
        ("Tab\there", None),
        ("   ", "Fixture requirements.json"),
        ("...", "Fixture requirements.json"),
        ("x" * 300, None),
        ("Lumière", "Lumière requirements.json"),
    ],
)
def test_suggested_file_name(name, expectation):
    result = suggested_file_name(_set(fixture_name=name))

    assert os.path.basename(result) == result

    if expectation is not None:
        assert result == expectation
        return

    if name == "../../etc/passwd":
        assert "/" not in result
        assert "\\" not in result
        assert not result.startswith(".")
    elif name == 'a:b*c?d"e<f>g|h':
        for character in '/\\:*?"<>|':
            assert character not in result
    elif name == "Tab\there":
        assert all(unicodedata.category(character) not in ("Cc", "Cs") for character in result)
    elif name == "x" * 300:
        stem = result[: -len(" requirements.json")]
        assert len(stem) == MAX_SUGGESTED_NAME_LENGTH


def test_saving_twice_is_byte_identical(tmp_path):
    path = tmp_path / "req.json"
    save_requirements(str(path), _set())
    first_bytes = path.read_bytes()

    save_requirements(str(path), _set())
    second_bytes = path.read_bytes()

    assert first_bytes == second_bytes
