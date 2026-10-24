"""Unit tests for core.requirements_repository: strict validation, safe
reads, hardened naming and atomic saves of the shareable fixture
requirements sidecar file (SUB-03, D-07..D-09).

A requirements file crosses the phase's main trust boundary (D-07): one
person saves it, a completely different person on a different computer
loads it. Every test here treats that boundary literally -- a round trip
through a real, separate Python process (test_round_trip_in_a_separate_
process), never coercing a file that isn't exactly understood.
"""

import errno
import json
import os
import subprocess
import sys
import threading
import time
import unicodedata
from pathlib import Path

import pytest

from gdtf_comparer.core import requirements_repository as requirements_repository_module
from gdtf_comparer.core.errors import RequirementsFileError
from gdtf_comparer.core.models import AttributeKey
from gdtf_comparer.core.requirements_repository import (
    MAX_REQUIREMENTS_COUNT,
    MAX_SUGGESTED_NAME_LENGTH,
    MAX_TEXT_FIELD_LENGTH,
    load_requirements,
    save_requirements,
    suggested_file_name,
)
from gdtf_comparer.core.substitution import TOLERANCE_KIND, Direction, Requirement, RequirementSet

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


# ---------------------------------------------------------------------------
# Task 2: a damaged, foreign, oversized or newer requirements file is
# refused in plain words, rather than coerced or partially loaded.
# ---------------------------------------------------------------------------


def _assert_refusal_message(error: RequirementsFileError, basename: str) -> None:
    """Every refusal names the file, ends "Nothing was loaded." and never leaks a traceback."""
    message = str(error)
    assert basename in message
    assert message.endswith("Nothing was loaded.")
    assert "Traceback" not in message


def _write_json(tmp_path, payload, name="req.json"):
    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _with_requirement(payload, index, **overrides):
    """Return payload with its requirements[index] dict updated by overrides."""
    requirements = [dict(item) for item in payload["requirements"]]
    requirements[index].update(overrides)
    return {**payload, "requirements": requirements}


# requirements[0] is the LOWER (numeric-direction) Weight requirement;
# requirements[1] is the EXACT (text-capable) BeamType requirement -- per
# the shared _set() helper above.
_PAYLOAD_MUTATIONS = {
    "format_missing": lambda p: {k: v for k, v in p.items() if k != "format"},
    "format_wrong": lambda p: {**p, "format": "something-else"},
    "version_zero": lambda p: {**p, "version": 0},
    "version_string": lambda p: {**p, "version": "1"},
    "version_bool": lambda p: {**p, "version": True},
    "newer_version": lambda p: {**p, "version": 2},
    "tolerance_kind_other": lambda p: {**p, "tolerance_kind": "other"},
    "extra_top_level_key": lambda p: {**p, "extra": 1},
    "missing_top_level_key": lambda p: {k: v for k, v in p.items() if k != "tolerance_kind"},
    "extra_fixture_key": lambda p: {**p, "fixture": {**p["fixture"], "extra": "x"}},
    "missing_fixture_key": lambda p: {
        **p,
        "fixture": {k: v for k, v in p["fixture"].items() if k != "manufacturer"},
    },
    "extra_requirement_key": lambda p: _with_requirement(p, 0, extra=1),
    "missing_requirement_key": lambda p: {
        **p,
        "requirements": [
            {k: v for k, v in p["requirements"][0].items() if k != "tolerance"},
            dict(p["requirements"][1]),
        ],
    },
    "direction_sideways": lambda p: _with_requirement(p, 0, direction="sideways"),
    "tolerance_negative": lambda p: _with_requirement(p, 0, tolerance=-1),
    "tolerance_bool": lambda p: _with_requirement(p, 0, tolerance=True),
    "tolerance_string": lambda p: _with_requirement(p, 0, tolerance="2"),
    "tolerance_null": lambda p: _with_requirement(p, 0, tolerance=None),
    "numeric_direction_text_target": lambda p: _with_requirement(p, 0, target="15"),
    "exact_target_bool": lambda p: _with_requirement(p, 1, target=True),
    "category_empty": lambda p: _with_requirement(p, 0, category=""),
    "attribute_empty": lambda p: _with_requirement(p, 0, attribute=""),
    "fixture_name_too_long": lambda p: {
        **p,
        "fixture": {**p["fixture"], "name": "x" * (MAX_TEXT_FIELD_LENGTH + 1)},
    },
    "too_many_requirements": lambda p: {
        **p,
        "requirements": [
            {**p["requirements"][0], "attribute": f"Attr{i}"} for i in range(MAX_REQUIREMENTS_COUNT + 1)
        ],
    },
    "duplicate_requirement_triple": lambda p: {
        **p,
        "requirements": [p["requirements"][0], dict(p["requirements"][0])],
    },
}

_EXPECTED_SUBSTRINGS = {
    "format_missing": "is not a fixture requirements file",
    "format_wrong": "is not a fixture requirements file",
    "newer_version": "saved by a newer version",
    "tolerance_kind_other": "different kind of tolerance",
}


@pytest.mark.parametrize("name, mutate", list(_PAYLOAD_MUTATIONS.items()), ids=list(_PAYLOAD_MUTATIONS.keys()))
def test_refuses_damaged_or_foreign_files(tmp_path, name, mutate):
    base = _payload(tmp_path, name=f"base-{name}.json")
    mutated = mutate(base)
    path = _write_json(tmp_path, mutated, name=f"{name}.json")

    with pytest.raises(RequirementsFileError) as exc_info:
        load_requirements(str(path))

    _assert_refusal_message(exc_info.value, path.name)
    if name in _EXPECTED_SUBSTRINGS:
        assert _EXPECTED_SUBSTRINGS[name] in str(exc_info.value)


@pytest.mark.parametrize(
    "name, raw",
    [
        ("not_json", b"{"),
        ("not_utf8", b"\xff\xfe"),
        ("json_list", b"[]"),
        ("foreign_app_json", b'{"profiles": []}'),
    ],
)
def test_refuses_raw_bytes(tmp_path, name, raw):
    path = tmp_path / f"{name}.json"
    path.write_bytes(raw)

    with pytest.raises(RequirementsFileError) as exc_info:
        load_requirements(str(path))

    _assert_refusal_message(exc_info.value, path.name)


def test_duplicate_json_key_is_refused(tmp_path):
    text = (
        '{"format": "gdtf-comparer-fixture-requirements", "version": 1, '
        f'"tolerance_kind": "{TOLERANCE_KIND}", '
        '"fixture": {"name": "Acme Spot", "manufacturer": "Acme", "gdtf_file": "Acme@Spot.gdtf"}, '
        '"requirements": [{"category": "Physical Properties", "element": "", "attribute": "Weight", '
        '"direction": "lower", "target": 15.0, "target": 16.0, "tolerance": 2.0}]}'
    )
    path = tmp_path / "duplicate-key.json"
    path.write_text(text, encoding="utf-8")

    with pytest.raises(RequirementsFileError) as exc_info:
        load_requirements(str(path))

    _assert_refusal_message(exc_info.value, path.name)


@pytest.mark.parametrize(
    "field, token",
    [("target", "NaN"), ("tolerance", "Infinity"), ("target", "-Infinity")],
)
def test_raw_nan_or_infinity_tokens_are_refused(tmp_path, field, token):
    target_value = token if field == "target" else "15.0"
    tolerance_value = token if field == "tolerance" else "2.0"
    text = (
        '{"format": "gdtf-comparer-fixture-requirements", "version": 1, '
        f'"tolerance_kind": "{TOLERANCE_KIND}", '
        '"fixture": {"name": "Acme Spot", "manufacturer": "Acme", "gdtf_file": "Acme@Spot.gdtf"}, '
        '"requirements": [{"category": "Physical Properties", "element": "", "attribute": "Weight", '
        f'"direction": "lower", "target": {target_value}, "tolerance": {tolerance_value}}}]}}'
    )
    path = tmp_path / f"raw-constant-{field}-{token}.json"
    path.write_text(text, encoding="utf-8")

    with pytest.raises(RequirementsFileError) as exc_info:
        load_requirements(str(path))

    _assert_refusal_message(exc_info.value, path.name)


def test_deeply_nested_target_is_refused(tmp_path):
    nested = "[" * 100000 + "]" * 100000
    text = (
        '{"format": "gdtf-comparer-fixture-requirements", "version": 1, '
        f'"tolerance_kind": "{TOLERANCE_KIND}", '
        '"fixture": {"name": "Acme Spot", "manufacturer": "Acme", "gdtf_file": "Acme@Spot.gdtf"}, '
        '"requirements": [{"category": "Physical Properties", "element": "", "attribute": "Weight", '
        f'"direction": "lower", "target": {nested}, "tolerance": 2.0}}]}}'
    )
    path = tmp_path / "deeply-nested.json"
    path.write_text(text, encoding="utf-8")

    with pytest.raises(RequirementsFileError) as exc_info:
        load_requirements(str(path))

    _assert_refusal_message(exc_info.value, path.name)


def test_exact_accepts_text_or_number(tmp_path):
    requirement_set = _set(
        requirements=(Requirement(AttributeKey("Beam", "", "Zoom"), 3.0, Direction.EXACT, 0.0),)
    )
    path = tmp_path / "exact-number.json"
    save_requirements(str(path), requirement_set)

    loaded = load_requirements(str(path))
    assert loaded.requirements[0].target == 3.0


def test_too_large_file_refused(tmp_path, monkeypatch):
    path = tmp_path / "req.json"
    save_requirements(str(path), _set())
    monkeypatch.setattr(requirements_repository_module, "MAX_REQUIREMENTS_FILE_BYTES", 64)

    with pytest.raises(RequirementsFileError) as exc_info:
        load_requirements(str(path))

    assert "too large" in str(exc_info.value)


@pytest.mark.skipif(sys.platform == "win32", reason="opening a directory on Windows raises a permission error")
def test_folder_refused(tmp_path):
    folder = tmp_path / "folder.json"
    folder.mkdir()

    with pytest.raises(RequirementsFileError) as exc_info:
        load_requirements(str(folder))

    assert "not a regular file" in str(exc_info.value)


def test_fifo_refused_without_blocking(tmp_path):
    if not hasattr(os, "mkfifo"):
        pytest.skip("os.mkfifo is not available on this platform")

    fifo_path = tmp_path / "pipe.json"
    os.mkfifo(fifo_path)

    def _keep_fifo_openable() -> None:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                fd = os.open(str(fifo_path), os.O_WRONLY | os.O_NONBLOCK)
            except OSError:
                pass
            else:
                os.close(fd)
            time.sleep(0.1)

    helper = threading.Thread(target=_keep_fifo_openable, daemon=True)
    helper.start()

    try:
        start = time.monotonic()
        with pytest.raises(RequirementsFileError) as exc_info:
            load_requirements(str(fifo_path))
        elapsed = time.monotonic() - start

        assert "not a regular file" in str(exc_info.value)
        assert elapsed < 2
    finally:
        helper.join(timeout=5)


def test_missing_file(tmp_path):
    missing = tmp_path / "missing.json"

    with pytest.raises(RequirementsFileError) as exc_info:
        load_requirements(str(missing))

    message = str(exc_info.value)
    assert "could not be opened" in message
    assert os.strerror(errno.ENOENT) in message
